from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from geocode import geocode_place, search_places
from ephemeris import local_to_julian_day, get_moon_longitude
from nakshatra import calculate_nakshatra
from name_nakshatra import find_nakshatra_by_name

# Load environment variables
load_dotenv()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"✅ Gemini API initialized with key: {GEMINI_API_KEY[:20]}...")
else:
    gemini_client = None
    print("⚠️  Gemini API key not found. /api/nakshatra/bygemini will not work.")


# ── Gemini API Helper (No Auto-Retry) ──────────────────────────────────────
def call_gemini_with_retry(prompt: str, response_schema: dict, temperature: float = 0.1):
    """
    Call Gemini API without auto-retry.
    Returns parsed JSON result or raises HTTPException.
    Frontend will handle button disabling to prevent spam clicks.
    
    Temperature 0.1 for faster, more deterministic responses.
    """
    try:
        response = gemini_client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                response_schema=response_schema, 
                temperature=temperature
            ),
        )
        return json.loads(response.text)
        
    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail=f"Invalid JSON from AI: {response.text[:200]}")
    except Exception as api_error:
        error_str = str(api_error)
        
        # Check if it's a quota/rate limit error
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            raise HTTPException(status_code=429, detail="API quota exhausted. Please wait a moment and try again.")
        else:
            raise HTTPException(status_code=500, detail=f"AI error: {error_str}")

app = FastAPI(
    title="Nakshatra Calculator API",
    description="Vedic astrology nakshatra calculation using Swiss Ephemeris (Moshier)",
    version="2.0.0",
    docs_url="/swagger",   # move default Swagger to /swagger
    redoc_url="/redoc",
)

# Serve custom interactive docs with place-search dropdown at /docs
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    with open("static/docs.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Add GZip compression for faster response times
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models ───────────────────────────────────────────────────────────
class BirthDetails(BaseModel):
    name:      str            = Field(..., example="Shiva Kumar")
    gender:    str            = Field(..., example="Male")
    date:      str            = Field(..., example="1999-11-08", description="YYYY-MM-DD")
    hour:      int            = Field(..., example=7,  ge=1, le=12)
    minute:    int            = Field(..., example=15, ge=0, le=59)
    ampm:      str            = Field(..., example="PM", pattern="^(AM|PM)$")
    place:     str            = Field(..., example="Nizamabad, Telangana, India")
    # Optional pre-resolved coordinates from /api/places dropdown
    latitude:  Optional[float] = Field(None, example=18.6725)
    longitude: Optional[float] = Field(None, example=78.0941)
    timezone:  Optional[str]   = Field(None, example="Asia/Kolkata")

class NameRequest(BaseModel):
    name: str = Field(..., example="Shiva", description="Name in Telugu or English")

class WeeklyHoroscopeRequest(BaseModel):
    name:      str            = Field(..., example="Shiva Kumar")
    gender:    str            = Field(..., example="Male")
    date:      str            = Field(..., example="1999-11-08", description="Birth date YYYY-MM-DD")
    hour:      int            = Field(..., example=7,  ge=1, le=12)
    minute:    int            = Field(..., example=15, ge=0, le=59)
    ampm:      str            = Field(..., example="PM", pattern="^(AM|PM)$")
    place:     str            = Field(..., example="Nizamabad, Telangana, India")
    latitude:  Optional[float] = Field(None, example=18.6725)
    longitude: Optional[float] = Field(None, example=78.0941)
    timezone:  Optional[str]   = Field(None, example="Asia/Kolkata")


# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_to_24h(hour: int, minute: int, ampm: str):
    h = hour
    if ampm == "PM" and h != 12:
        h += 12
    if ampm == "AM" and h == 12:
        h = 0
    return h, minute


def resolve_geo(details: BirthDetails) -> dict:
    """
    If frontend already sent lat/lon/timezone (from /api/places dropdown),
    use them directly.  Otherwise fall back to Nominatim geocoding.
    """
    if details.latitude is not None and details.longitude is not None and details.timezone:
        return {
            "lat": details.latitude,
            "lon": details.longitude,
            "timezone": details.timezone,
            "display_name": details.place,
        }
    return geocode_place(details.place)


# ── Place search (GeoNames) ─────────────────────────────────────────────────
@app.get("/api/places")
async def places_search(
    q: str = Query(..., min_length=2, description="Search query (min 2 chars)"),
    max_rows: int = Query(10, ge=1, le=20),
):
    """
    Autocomplete place search powered by GeoNames (11M+ places).
    Finds every village, hamlet, town, and city on Earth.

    Returns list of places with lat, lon, timezone ready to use.
    Frontend should call this as the user types, then send the
    selected place's lat/lon/timezone in the birth-details request.
    """
    try:
        results = await search_places(q, max_rows)
        return {"query": q, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GeoNames search failed: {e}")


# ── Nakshatra endpoint ──────────────────────────────────────────────────────
@app.post("/api/nakshatra")
def get_nakshatra(details: BirthDetails):
    try:
        geo = resolve_geo(details)
        year, month, day = map(int, details.date.split("-"))
        hour24, minute = parse_to_24h(details.hour, details.minute, details.ampm)
        jd = local_to_julian_day(year, month, day, hour24, minute, geo["timezone"])
        moon_lon, moon_speed = get_moon_longitude(jd)
        nk = calculate_nakshatra(moon_lon, moon_speed)

        return {
            "name": details.name, "gender": details.gender,
            "date": details.date,
            "time": f"{details.hour}:{details.minute:02d} {details.ampm}",
            "place": details.place,
            "timezone": geo["timezone"],
            "latitude": geo["lat"], "longitude": geo["lon"],
            "julian_day": round(jd, 6),
            **nk,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


# ── Gemini AI-powered Nakshatra endpoint ────────────────────────────────────
@app.post("/api/nakshatra/bygemini")
def get_nakshatra_by_gemini(details: BirthDetails):
    """
    AI-powered nakshatra calculation using Gemini 2.0 Flash Lite (optimized for speed).
    Returns the EXACT same format as /api/nakshatra endpoint.
    """
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="Gemini API is not configured. Please set GEMINI_API_KEY in .env file and restart the server.")

    try:
        geo = resolve_geo(details)

        # Optimized prompt with example format
        prompt = f"""Calculate Vedic astrology Nakshatra using Lahiri ayanamsa for:
Birth Date: {details.date}
Birth Time: {details.hour}:{details.minute:02d} {details.ampm}
Location: Latitude {geo["lat"]}, Longitude {geo["lon"]}, Timezone {geo["timezone"]}

Return JSON in this EXACT format:
{{
  "nakshatra": "Ardra",
  "pada": 1,
  "pada_label": "1st",
  "chandra_rasi": "Mithuna (Gemini)",
  "deity": "Rudra",
  "gana": "Manushya",
  "animal_sign": "Dog",
  "color": "Green",
  "birthstone": "Emerald",
  "syllables": ["Ku", "Gha", "Ng", "Chha"],
  "best_direction": "West",
  "symbol": "Teardrop",
  "zodiac_sign": "Gemini",
  "moon_longitude": 67.5,
  "nakshatra_range": "66.67° – 80.00°",
  "moon_speed_deg_per_day": 13.5,
  "julian_day": 2451234.5
}}

Calculate accurate values for the given birth details."""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "nakshatra": {"type": "STRING"}, "pada": {"type": "INTEGER"}, "pada_label": {"type": "STRING"},
                "chandra_rasi": {"type": "STRING"}, "deity": {"type": "STRING"}, "gana": {"type": "STRING"},
                "animal_sign": {"type": "STRING"}, "color": {"type": "STRING"}, "birthstone": {"type": "STRING"},
                "syllables": {"type": "ARRAY", "items": {"type": "STRING"}}, "best_direction": {"type": "STRING"},
                "symbol": {"type": "STRING"}, "zodiac_sign": {"type": "STRING"}, "moon_longitude": {"type": "NUMBER"},
                "nakshatra_range": {"type": "STRING"}, "moon_speed_deg_per_day": {"type": "NUMBER"}, "julian_day": {"type": "NUMBER"}
            },
            "required": ["nakshatra", "pada", "pada_label", "chandra_rasi", "deity", "gana", "animal_sign", "color", "birthstone", "syllables", "best_direction", "symbol", "zodiac_sign", "moon_longitude", "nakshatra_range", "moon_speed_deg_per_day", "julian_day"]
        }

        # Use helper function with retry logic
        ai_result = call_gemini_with_retry(prompt, response_schema)

        return {
            "name": details.name, "gender": details.gender, "date": details.date,
            "time": f"{details.hour}:{details.minute:02d} {details.ampm}", "place": details.place,
            "timezone": geo["timezone"], "latitude": geo["lat"], "longitude": geo["lon"],
            "julian_day": ai_result["julian_day"], "nakshatra": ai_result["nakshatra"],
            "pada": ai_result["pada"], "pada_label": ai_result["pada_label"],
            "chandra_rasi": ai_result["chandra_rasi"], "deity": ai_result["deity"],
            "gana": ai_result["gana"], "animal_sign": ai_result["animal_sign"],
            "color": ai_result["color"], "birthstone": ai_result["birthstone"],
            "syllables": ai_result["syllables"], "best_direction": ai_result["best_direction"],
            "symbol": ai_result["symbol"], "zodiac_sign": ai_result["zodiac_sign"],
            "moon_longitude": ai_result["moon_longitude"], "nakshatra_range": ai_result["nakshatra_range"],
            "moon_speed_deg_per_day": ai_result["moon_speed_deg_per_day"]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI calculation error: {e}")


# ── Name-based nakshatra lookup ─────────────────────────────────────────────
@app.post("/api/nakshatra-by-name")
def get_nakshatra_by_name(request: NameRequest):
    """Find nakshatra, rashi, and pada based on the first syllable of a name."""
    try:
        return find_nakshatra_by_name(request.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup error: {e}")


# ── Comprehensive Horoscope endpoint ────────────────────────────────────────
from horoscope import calculate_comprehensive_horoscope
from weekly_horoscope import calculate_weekly_horoscope

@app.post("/api/horoscope")
def get_comprehensive_horoscope(details: BirthDetails):
    """
    Full horoscope: Weekday, Nakshatra, Rasi, Tithi, Karana, Yoga predictions
    plus complete birth-chart metadata.
    """
    try:
        geo = resolve_geo(details)
        return calculate_comprehensive_horoscope(
            name=details.name, gender=details.gender,
            date=details.date, hour=details.hour,
            minute=details.minute, ampm=details.ampm,
            place=details.place,
            lat=geo["lat"], lon=geo["lon"], timezone=geo["timezone"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


# ── Gemini AI-powered Horoscope endpoint ────────────────────────────────────
@app.post("/api/horoscope/bygemini")
def get_horoscope_by_gemini(details: BirthDetails):
    """
    AI-powered comprehensive horoscope using Gemini 2.0 Flash Lite (optimized for speed).
    Returns the EXACT same format as /api/horoscope endpoint.
    """
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="Gemini API is not configured.")

    try:
        geo = resolve_geo(details)

        # Optimized prompt with example format
        prompt = f"""Calculate comprehensive Vedic horoscope using Lahiri ayanamsa for:
Birth Date: {details.date}
Birth Time: {details.hour}:{details.minute:02d} {details.ampm}
Location: Latitude {geo["lat"]}, Longitude {geo["lon"]}, Timezone {geo["timezone"]}

Return JSON in this EXACT format:
{{
  "predictions": {{
    "weekday": {{"title": "Weekday: Sunday", "description": "Born on Sunday...", "ruling_planet": "Sun"}},
    "nakshatra": {{"title": "Nakshatra: Ardra", "description": "Ardra nakshatra indicates..."}},
    "rasi": {{"title": "Rasi: Mithuna (Gemini)", "description": "Gemini moon sign..."}},
    "tithi": {{"title": "Tithi: Shukla Pratipada", "description": "First lunar day..."}},
    "karana": {{"title": "Karana: Bava", "description": "Bava karana..."}},
    "yoga": {{"title": "Yoga: Vishkambha", "description": "Vishkambha yoga..."}}
  }},
  "birth_details": {{
    "nakshatra": "Ardra 1st Pada",
    "weekday": "Sunday",
    "tithi": "Shukla Pratipada",
    "yoga": "Vishkambha",
    "karana": "Bava",
    "vikram_samvat": "2056",
    "god": "Rudra",
    "animal_sign": "Dog",
    "rasi": "Mithuna (Gemini)",
    "rasi_lord": "Mercury",
    "ascendant": "Mesha",
    "ascendant_lord": "Mars",
    "ganam": "Manushya",
    "yoni": "Male",
    "gothram": "Vasishtha",
    "bhutham": "Air",
    "sunrise": "06:15 AM",
    "sunset": "06:30 PM"
  }},
  "input_details": {{
    "name": "{details.name}",
    "gender": "{details.gender}",
    "date_of_birth": "{details.date}",
    "time_of_birth": "{details.hour}:{details.minute:02d} {details.ampm}",
    "place_of_birth": "{details.place}",
    "latitude": {geo["lat"]},
    "longitude": {geo["lon"]},
    "timezone": "{geo["timezone"]}"
  }},
  "technical_details": {{
    "julian_day": 2451234.5,
    "moon_longitude": 67.5,
    "moon_speed": 13.5,
    "ascendant_degree": 15.25
  }}
}}

Calculate accurate values for the given birth details."""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "predictions": {"type": "OBJECT", "properties": {
                    "weekday": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "description": {"type": "STRING"}, "ruling_planet": {"type": "STRING"}}},
                    "nakshatra": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "description": {"type": "STRING"}}},
                    "rasi": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "description": {"type": "STRING"}}},
                    "tithi": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "description": {"type": "STRING"}}},
                    "karana": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "description": {"type": "STRING"}}},
                    "yoga": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "description": {"type": "STRING"}}}
                }},
                "birth_details": {"type": "OBJECT", "properties": {
                    "nakshatra": {"type": "STRING"}, "weekday": {"type": "STRING"}, "tithi": {"type": "STRING"},
                    "yoga": {"type": "STRING"}, "karana": {"type": "STRING"}, "vikram_samvat": {"type": "STRING"},
                    "god": {"type": "STRING"}, "animal_sign": {"type": "STRING"}, "rasi": {"type": "STRING"},
                    "rasi_lord": {"type": "STRING"}, "ascendant": {"type": "STRING"}, "ascendant_lord": {"type": "STRING"},
                    "ganam": {"type": "STRING"}, "yoni": {"type": "STRING"}, "gothram": {"type": "STRING"},
                    "bhutham": {"type": "STRING"}, "sunrise": {"type": "STRING"}, "sunset": {"type": "STRING"}
                }},
                "input_details": {"type": "OBJECT", "properties": {
                    "name": {"type": "STRING"}, "gender": {"type": "STRING"}, "date_of_birth": {"type": "STRING"},
                    "time_of_birth": {"type": "STRING"}, "place_of_birth": {"type": "STRING"},
                    "latitude": {"type": "NUMBER"}, "longitude": {"type": "NUMBER"}, "timezone": {"type": "STRING"}
                }},
                "technical_details": {"type": "OBJECT", "properties": {
                    "julian_day": {"type": "NUMBER"}, "moon_longitude": {"type": "NUMBER"},
                    "moon_speed": {"type": "NUMBER"}, "ascendant_degree": {"type": "NUMBER"}
                }}
            },
            "required": ["predictions", "birth_details", "input_details", "technical_details"]
        }

        # Use helper function with retry logic
        return call_gemini_with_retry(prompt, response_schema)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI horoscope calculation error: {e}")


# ── Weekly Horoscope endpoint ───────────────────────────────────────────────
@app.post("/api/weekly-horoscope")
def get_weekly_horoscope(details: WeeklyHoroscopeRequest):
    """
    Weekly horoscope: Panchang predictions for 7 consecutive days
    starting from TODAY, using the person's birth time and place.
    """
    from datetime import date as dt_date
    try:
        if details.latitude is not None and details.longitude is not None and details.timezone:
            geo = {"lat": details.latitude, "lon": details.longitude, "timezone": details.timezone, "display_name": details.place}
        else:
            geo = geocode_place(details.place)
        today = dt_date.today().isoformat()  # YYYY-MM-DD
        return calculate_weekly_horoscope(
            name=details.name, gender=details.gender,
            date=today, hour=details.hour,
            minute=details.minute, ampm=details.ampm,
            place=details.place,
            lat=geo["lat"], lon=geo["lon"], timezone=geo["timezone"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


# ── Gochara (Transit) Chart endpoint ────────────────────────────────────────
@app.post("/api/gochara/bygemini")
def get_gochara_by_gemini(details: BirthDetails):
    """
    Gochara (Transit) Chart with real astronomical calculations + AI predictions.
    Shows current planetary positions using Swiss Ephemeris and AI-generated interpretations.
    """
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="Gemini API is not configured.")
    
    try:
        from ephemeris import (
            local_to_julian_day, get_all_planets, get_moon_longitude,
            longitude_to_sign, longitude_to_nakshatra, calculate_house_from_ascendant
        )
        from nakshatra import calculate_nakshatra
        
        geo = resolve_geo(details)
        
        # Get current date for transit calculations
        from datetime import datetime
        import pytz
        
        tz = pytz.timezone(geo["timezone"])
        now = datetime.now(tz)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%I:%M %p")
        
        # Calculate birth chart details
        birth_parts = details.date.split("-")
        birth_year, birth_month, birth_day = int(birth_parts[0]), int(birth_parts[1]), int(birth_parts[2])
        birth_hour = details.hour if details.ampm == "AM" or details.hour == 12 else details.hour + 12
        if details.ampm == "AM" and details.hour == 12:
            birth_hour = 0
        
        birth_jd = local_to_julian_day(birth_year, birth_month, birth_day, birth_hour, details.minute, geo["timezone"])
        birth_planets = get_all_planets(birth_jd)
        birth_moon_lon, _ = get_moon_longitude(birth_jd)
        birth_nakshatra_info = calculate_nakshatra(birth_moon_lon)
        
        # Calculate current transit positions
        current_jd = local_to_julian_day(now.year, now.month, now.day, now.hour, now.minute, geo["timezone"])
        transit_planets = get_all_planets(current_jd)
        
        # Get ascendant (using Sun as approximation - you can improve this with actual ascendant calculation)
        ascendant_longitude = birth_planets['sun']  # Simplified - use proper ascendant calculation if available
        
        # Build current_transits with real data
        current_transits = {}
        for planet_name, longitude in transit_planets.items():
            current_transits[planet_name] = {
                "sign": longitude_to_sign(longitude),
                "nakshatra": longitude_to_nakshatra(longitude),
                "degree": round(longitude, 2),
                "house": calculate_house_from_ascendant(longitude, ascendant_longitude)
            }
        
        # Build birth_chart info
        birth_chart = {
            "sun_sign": longitude_to_sign(birth_planets['sun']),
            "moon_sign": longitude_to_sign(birth_planets['moon']),
            "ascendant": longitude_to_sign(ascendant_longitude),
            "birth_nakshatra": birth_nakshatra_info['nakshatra']
        }
        
        # Now use Gemini ONLY for predictions and interpretations
        transit_summary = "\n".join([
            f"{planet.title()}: {data['sign']} ({data['nakshatra']}) in House {data['house']}"
            for planet, data in current_transits.items()
        ])
        
        prompt = f"""As a Vedic astrologer, provide predictions for these current planetary transits.

BIRTH CHART:
Sun Sign: {birth_chart['sun_sign']}
Moon Sign: {birth_chart['moon_sign']}
Ascendant: {birth_chart['ascendant']}
Birth Nakshatra: {birth_chart['birth_nakshatra']}

CURRENT TRANSITS (calculated on {current_date} at {current_time}):
{transit_summary}

Provide detailed interpretations in this EXACT JSON format:
{{
  "transit_effects": {{
    "sun": "Brief effect of Sun's current position...",
    "moon": "Brief effect of Moon's current position...",
    "mars": "Brief effect of Mars's current position...",
    "mercury": "Brief effect of Mercury's current position...",
    "jupiter": "Brief effect of Jupiter's current position...",
    "venus": "Brief effect of Venus's current position...",
    "saturn": "Brief effect of Saturn's current position...",
    "rahu": "Brief effect of Rahu's current position...",
    "ketu": "Brief effect of Ketu's current position..."
  }},
  "major_predictions": {{
    "career": "Career prediction based on transits...",
    "finance": "Financial prediction...",
    "health": "Health guidance...",
    "relationships": "Relationship insights...",
    "spiritual": "Spiritual guidance..."
  }},
  "remedies": [
    "Specific remedy 1",
    "Specific remedy 2",
    "Specific remedy 3"
  ],
  "favorable_periods": {{
    "next_7_days": "Brief outlook",
    "next_month": "Brief outlook",
    "next_3_months": "Brief outlook"
  }}
}}

Provide meaningful, specific predictions based on the transit positions."""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "transit_effects": {
                    "type": "OBJECT",
                    "properties": {
                        "sun": {"type": "STRING"}, "moon": {"type": "STRING"}, "mars": {"type": "STRING"},
                        "mercury": {"type": "STRING"}, "jupiter": {"type": "STRING"}, "venus": {"type": "STRING"},
                        "saturn": {"type": "STRING"}, "rahu": {"type": "STRING"}, "ketu": {"type": "STRING"}
                    }
                },
                "major_predictions": {
                    "type": "OBJECT",
                    "properties": {
                        "career": {"type": "STRING"}, "finance": {"type": "STRING"},
                        "health": {"type": "STRING"}, "relationships": {"type": "STRING"},
                        "spiritual": {"type": "STRING"}
                    }
                },
                "remedies": {"type": "ARRAY", "items": {"type": "STRING"}},
                "favorable_periods": {
                    "type": "OBJECT",
                    "properties": {
                        "next_7_days": {"type": "STRING"},
                        "next_month": {"type": "STRING"},
                        "next_3_months": {"type": "STRING"}
                    }
                }
            },
            "required": ["transit_effects", "major_predictions", "remedies", "favorable_periods"]
        }

        # Use helper function with retry logic
        ai_result = call_gemini_with_retry(prompt, response_schema)
        
        # Combine real calculations with AI predictions
        result = {
            "birth_chart": birth_chart,
            "current_transits": current_transits,
            "transit_effects": ai_result["transit_effects"],
            "major_predictions": ai_result["major_predictions"],
            "remedies": ai_result["remedies"],
            "favorable_periods": ai_result["favorable_periods"],
            "calculation_date": current_date,
            "calculation_time": current_time
        }
        
        # Add input details
        result["input_details"] = {
            "name": details.name,
            "gender": details.gender,
            "date_of_birth": details.date,
            "time_of_birth": f"{details.hour}:{details.minute:02d} {details.ampm}",
            "place_of_birth": details.place,
            "latitude": geo["lat"],
            "longitude": geo["lon"],
            "timezone": geo["timezone"]
        }
        
        # Generate chart image - South Indian Style (ProKerala format)
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            import base64
            
            # Create image with vintage parchment background
            img_size = 900
            img = Image.new('RGB', (img_size, img_size), color='#F5E6D3')
            draw = ImageDraw.Draw(img)
            
            # Try to use a font, fallback to default
            try:
                title_font = ImageFont.truetype("arial.ttf", 20)
                label_font = ImageFont.truetype("arial.ttf", 16)
                planet_font = ImageFont.truetype("arialbd.ttf", 18)
                small_font = ImageFont.truetype("arial.ttf", 14)
                center_font = ImageFont.truetype("arial.ttf", 16)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
                planet_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
                center_font = ImageFont.load_default()
            
            # South Indian chart - 4x4 grid
            margin = 50
            chart_size = img_size - 2 * margin
            cell_size = chart_size // 4
            
            # Border color - reddish brown like ProKerala
            border_color = '#8B4513'
            line_width = 4
            
            # Draw outer rectangle with thick border
            draw.rectangle(
                [(margin, margin), (margin + chart_size, margin + chart_size)],
                outline=border_color,
                width=line_width
            )
            
            # Draw grid lines (4x4) - but skip the middle 2x2 area
            for i in range(1, 4):
                # Vertical lines - skip middle section
                x = margin + i * cell_size
                if i == 1 or i == 3:
                    # Full vertical line for outer columns
                    draw.line([(x, margin), (x, margin + chart_size)], fill=border_color, width=2)
                else:
                    # Split vertical line for middle column (skip center)
                    draw.line([(x, margin), (x, margin + cell_size)], fill=border_color, width=2)  # Top
                    draw.line([(x, margin + 3 * cell_size), (x, margin + chart_size)], fill=border_color, width=2)  # Bottom
                
                # Horizontal lines - skip middle section
                y = margin + i * cell_size
                if i == 1 or i == 3:
                    # Full horizontal line for outer rows
                    draw.line([(margin, y), (margin + chart_size, y)], fill=border_color, width=2)
                else:
                    # Split horizontal line for middle row (skip center)
                    draw.line([(margin, y), (margin + cell_size, y)], fill=border_color, width=2)  # Left
                    draw.line([(margin + 3 * cell_size, y), (margin + chart_size, y)], fill=border_color, width=2)  # Right
            
            # South Indian house layout (fixed positions in 4x4 grid)
            # Row 0: 12, 1, 2, 3
            # Row 1: 11, center, center, 4
            # Row 2: 10, center, center, 5
            # Row 3: 9, 8, 7, 6
            
            house_grid = {
                12: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0),
                11: (0, 1),                         4: (3, 1),
                10: (0, 2),                         5: (3, 2),
                9: (0, 3),  8: (1, 3), 7: (2, 3),  6: (3, 3)
            }
            
            # Calculate center positions for each house
            house_positions = {}
            for house_num, (col, row) in house_grid.items():
                x = margin + col * cell_size + cell_size // 2
                y = margin + row * cell_size + cell_size // 2
                house_positions[house_num] = (x, y)
            
            # Map planets to houses
            house_planets = {i: [] for i in range(1, 13)}
            transits = result["current_transits"]
            
            # Planet abbreviations like ProKerala
            planet_abbrev = {
                'sun': 'Su', 'moon': 'Mo', 'mars': 'Ma', 'mercury': 'Me',
                'jupiter': 'Ju', 'venus': 'Ve', 'saturn': 'Sa', 'rahu': 'Ra', 'ketu': 'Ke'
            }
            
            for planet, data in transits.items():
                house_num = data['house']
                abbrev = planet_abbrev.get(planet, planet[:2].upper())
                house_planets[house_num].append(abbrev)
            
            # Draw house numbers and planets
            for house_num, (x, y) in house_positions.items():
                # Draw house number in top-left corner of cell
                col, row = house_grid[house_num]
                num_x = margin + col * cell_size + 15
                num_y = margin + row * cell_size + 15
                draw.text((num_x, num_y), str(house_num), fill='#CC0000', font=small_font)
                
                # Draw planets in center of cell
                if house_planets[house_num]:
                    planets_text = "\n".join(house_planets[house_num])
                    draw.text((x, y), planets_text, fill='#4B3621', font=planet_font, anchor="mm")
            
            # Draw center information (birth details and Rasi)
            center_x = margin + chart_size // 2
            center_y = margin + chart_size // 2
            
            # Birth date and time
            birth_date_text = f"{details.date}"
            birth_time_text = f"{details.hour}:{details.minute:02d}:00 {details.ampm}"
            draw.text((center_x, center_y - 60), birth_date_text, fill='#CC6666', font=center_font, anchor="mm")
            draw.text((center_x, center_y - 35), birth_time_text, fill='#CC6666', font=center_font, anchor="mm")
            
            # Rasi (Moon sign)
            draw.text((center_x, center_y), "Rasi", fill='#000000', font=title_font, anchor="mm")
            
            # Nakshatra
            nakshatra_name = result['birth_chart'].get('birth_nakshatra', 'Unknown')
            draw.text((center_x, center_y + 30), nakshatra_name, fill='#000000', font=center_font, anchor="mm")
            
            # Ascendant at bottom-right corner (house 6 position)
            asc_text = f"Asc"
            asc_x = margin + 3 * cell_size + cell_size // 2
            asc_y = margin + 3 * cell_size + cell_size // 2 + 40
            draw.text((asc_x, asc_y), asc_text, fill='#4B3621', font=planet_font, anchor="mm")
            
            # Draw watermark at bottom
            watermark = "Generated By PROKERALA.com"
            draw.text((margin + chart_size - 10, margin + chart_size - 10), 
                     watermark, fill='#999', font=small_font, anchor="rb")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            result["chart_image"] = {
                "data": img_base64,
                "mime_type": "image/png",
                "format": "base64"
            }
            
        except Exception as img_error:
            result["chart_image"] = {
                "error": f"Image generation failed: {str(img_error)}",
                "data": None
            }
        
        return result
        
    except HTTPException:
        raise  # Re-raise HTTPException without wrapping
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gochara calculation error: {e}")


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Nakshatra API is running"}

@app.get("/api/health")
def health():
    return {"status": "ok"}
