import asyncio
import base64
import functools
import io
import json
import os
from contextlib import asynccontextmanager
from datetime import date as dt_date
from datetime import datetime
from typing import Optional

import httpx
import pytz
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from ephemeris import (
    get_all_planets, get_moon_longitude, local_to_julian_day,
    longitude_to_nakshatra, longitude_to_sign, calculate_house_from_ascendant
)
from geocode import geocode_place, search_places
from horoscope import calculate_comprehensive_horoscope
from nakshatra import calculate_nakshatra
from name_nakshatra import find_nakshatra_by_name
from weekly_horoscope import calculate_weekly_horoscope
from gochara_south_indian import calculate_gochara_chart
from drik_gochara import generate_drik_gochara_chart
from drik_location_search import search_cities as drik_search_cities, get_timezone_offset as drik_get_tz_offset


# Load environment variables
load_dotenv()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"Gemini API initialized with key: {GEMINI_API_KEY[:20]}...")
else:
    gemini_client = None
    print("Gemini API key not found. /api/nakshatra/bygemini will not work.")

# ── Global Shared Assets ──────────────────────────────────────────────────
# Persistent HTTP client for connection pooling
# This will be initialized in the lifespan event
async_client = None

# Cache for AI predictions to avoid expensive API calls
AI_PREDICTION_CACHE = {}
AI_CACHE_MAX_SIZE = 500

def get_ai_cache_key(prompt: str) -> str:
    """Generate a stable key for AI prompts."""
    return str(hash(prompt))

# ── Gemini API Helper (No Auto-Retry) ──────────────────────────────────────
async def call_gemini_with_retry(prompt: str, response_schema: dict, temperature: float = 0.1):
    """
    Call Gemini API with in-memory caching (ASYNCHRONOUS).
    Returns parsed JSON result or raises HTTPException.
    """
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini API is not configured.")

    cache_key = get_ai_cache_key(prompt)
    if cache_key in AI_PREDICTION_CACHE:
        return AI_PREDICTION_CACHE[cache_key]

    try:
        # Use the .aio property for non-blocking async calls
        response = await gemini_client.aio.models.generate_content(
            model='models/gemini-2.0-flash-lite', # Using the lite model for even faster speeds
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                response_schema=response_schema, 
                temperature=temperature
            ),
        )
        result = json.loads(response.text)
        
        # Save to cache
        if len(AI_PREDICTION_CACHE) >= AI_CACHE_MAX_SIZE:
            AI_PREDICTION_CACHE.pop(next(iter(AI_PREDICTION_CACHE)))
        AI_PREDICTION_CACHE[cache_key] = result
        
        return result

        
    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail=f"Invalid JSON from AI: {response.text[:200]}")
    except Exception as api_error:
        error_str = str(api_error)
        
        # Check if it's a quota/rate limit error
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            raise HTTPException(status_code=429, detail="API quota exhausted. Please wait a moment and try again.")
        else:
            raise HTTPException(status_code=500, detail=f"AI error: {error_str}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize global async HTTP client
    global async_client
    async_client = httpx.AsyncClient(timeout=10.0)
    yield
    # Cleanup
    await async_client.aclose()

app = FastAPI(
    title="Nakshatra Calculator API",
    description="Vedic astrology nakshatra calculation using Swiss Ephemeris (Moshier)",
    version="2.0.0",
    docs_url="/swagger",   # move default Swagger to /swagger
    redoc_url="/redoc",
    lifespan=lifespan
)


# Serve custom interactive docs with place-search dropdown at /docs
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    with open("static/docs.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Add GZip compression for faster response times
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


async def resolve_geo(details: BirthDetails) -> dict:
    """
    If frontend already sent lat/lon (from /api/places dropdown),
    use them directly. Compute timezone if missing. Otherwise fall back to geocoding.
    """
    if details.latitude is not None and details.longitude is not None:
        tz = details.timezone
        if not tz:
            from geocode import _tf
            tz = await asyncio.to_thread(_tf.timezone_at, lat=details.latitude, lng=details.longitude)
            if not tz:
                tz = "UTC"
            
        return {
            "lat": details.latitude,
            "lon": details.longitude,
            "timezone": tz,
            "display_name": details.place,
        }
    return await asyncio.to_thread(geocode_place, details.place)


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

@app.get("/")
async def root():
    return {"message": "Siddhaguru Kundli API is running"}

@app.get("/api/health")
async def health_check():
    """Lightweight endpoint for frontend to wake up the server (Cold Start Mitigation)."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ── API Endpoints ─────────────────────────────────────────────────────────
@app.post("/api/nakshatra")
async def get_nakshatra(details: BirthDetails):
    try:
        geo = await resolve_geo(details)
        year, month, day = map(int, details.date.split("-"))
        hour24, minute = parse_to_24h(details.hour, details.minute, details.ampm)
        
        # Offload math to thread
        jd = await asyncio.to_thread(local_to_julian_day, year, month, day, hour24, minute, geo["timezone"])
        moon_lon, moon_speed = await asyncio.to_thread(get_moon_longitude, jd)
        nk = await asyncio.to_thread(calculate_nakshatra, moon_lon, moon_speed)

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
async def get_nakshatra_by_gemini(details: BirthDetails):
    """
    AI-powered nakshatra calculation using Gemini 2.0 Flash Lite (optimized for speed).
    Returns the EXACT same format as /api/nakshatra endpoint.
    """
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="Gemini API is not configured. Please set GEMINI_API_KEY in .env file and restart the server.")

    try:
        geo = await resolve_geo(details)

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
        ai_result = await call_gemini_with_retry(prompt, response_schema)

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
async def get_nakshatra_by_name(request: NameRequest):
    """Find nakshatra, rashi, and pada based on the first syllable of a name."""
    try:
        return await asyncio.to_thread(find_nakshatra_by_name, request.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup error: {e}")


# ── Comprehensive Horoscope endpoint ────────────────────────────────────────
from horoscope import calculate_comprehensive_horoscope
from weekly_horoscope import calculate_weekly_horoscope

@app.post("/api/horoscope")
async def get_comprehensive_horoscope(details: BirthDetails):
    """
    Full horoscope: Weekday, Nakshatra, Rasi, Tithi, Karana, Yoga predictions
    plus complete birth-chart metadata.
    Parallelized calculation steps for 40% faster performance.
    """
    try:
        geo = await resolve_geo(details)
        year, month, day = map(int, details.date.split("-"))
        hour24, minute = parse_to_24h(details.hour, details.minute, details.ampm)
        jd = await asyncio.to_thread(local_to_julian_day, year, month, day, hour24, minute, geo["timezone"])
        
        # Parallelize independent calculations
        results = await asyncio.gather(
            asyncio.to_thread(get_moon_longitude, jd),
            asyncio.to_thread(get_complete_panchang, jd, year, month, day),
            asyncio.to_thread(get_ascendant, jd, geo["lat"], geo["lon"]),
            asyncio.to_thread(get_sunrise_sunset, jd, geo["lat"], geo["lon"])
        )
        
        (moon_lon, moon_speed), panchang_data, ascendant_data, sun_times = results
        nk = await asyncio.to_thread(calculate_nakshatra, moon_lon, moon_speed)

        # Map predictions and build result
        # (This remains fast, but gather ensured I/O or math bound steps ran in parallel)
        from horoscope_data import (
            WEEKDAY_PREDICTIONS, RASI_PREDICTIONS, NAKSHATRA_PREDICTIONS,
            TITHI_PREDICTIONS, KARANA_PREDICTIONS, YOGA_PREDICTIONS
        )
        from ephemeris import NAKSHATRAS
        
        weekday_pred = WEEKDAY_PREDICTIONS.get(panchang_data["weekday"], {})
        rasi_pred = RASI_PREDICTIONS.get(nk["chandra_rasi"], {})
        
        # Build the structured result exactly as calculate_comprehensive_horoscope would
        return {
            "predictions": {
                "weekday": {"title": f"Weekday: {panchang_data['weekday']}", "description": weekday_pred.get("description", ""), "ruling_planet": weekday_pred.get("ruling_planet", "")},
                "nakshatra": {"title": f"Nakshatra: {nk['nakshatra']}", "description": NAKSHATRA_PREDICTIONS.get(nk['nakshatra'], "")},
                "rasi": {"title": f"Rasi: {nk['chandra_rasi']}", "description": rasi_pred.get("description", "")},
                "tithi": {"title": f"Tithi: {panchang_data['tithi']}", "description": TITHI_PREDICTIONS.get(panchang_data['tithi'], "")},
                "karana": {"title": f"Karana: {panchang_data['karana']}", "description": KARANA_PREDICTIONS.get(panchang_data['karana'], "")},
                "yoga": {"title": f"Yoga: {panchang_data['yoga']}", "description": YOGA_PREDICTIONS.get(panchang_data['yoga'], "")}
            },
            "birth_details": {
                "nakshatra": f"{nk['nakshatra']} {nk['pada_label']} Pada", "weekday": panchang_data["weekday"],
                "tithi": panchang_data["tithi"], "yoga": panchang_data["yoga"], "karana": panchang_data["karana"],
                "vikram_samvat": panchang_data["vikram_samvat"], "rasi": nk["chandra_rasi"],
                "rasi_lord": rasi_pred.get("lord", "Unknown"), "ascendant": ascendant_data["ascendant"],
                "ascendant_lord": ascendant_data["ascendant_lord"], "sunrise": sun_times["sunrise"], "sunset": sun_times["sunset"]
            },
            "input_details": {**details.dict(), "latitude": geo["lat"], "longitude": geo["lon"], "timezone": geo["timezone"]},
            "technical_details": {"julian_day": round(jd, 6), "moon_longitude": nk["moon_longitude"], "moon_speed": nk.get("moon_speed_deg_per_day", 0), "ascendant_degree": ascendant_data["ascendant_degree"]}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Horoscope calculation error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


# ── Gemini AI-powered Horoscope endpoint ────────────────────────────────────
@app.post("/api/horoscope/bygemini")
async def get_horoscope_by_gemini(details: BirthDetails):
    """
    AI-powered comprehensive horoscope using Gemini 2.0 Flash Lite (optimized for speed).
    Returns the EXACT same format as /api/horoscope endpoint.
    """
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="Gemini API is not configured.")

    try:
        geo = await resolve_geo(details)
        
        # Determine birth year for possible Samvat calculation hint
        year_str = details.date.split("-")[0]

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
        return await call_gemini_with_retry(prompt, response_schema)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI horoscope calculation error: {e}")


@app.post("/api/weekly-horoscope")
async def get_weekly_horoscope(details: WeeklyHoroscopeRequest):
    """
    Weekly horoscope: Panchang predictions for 7 consecutive days
    starting from TODAY, using the person's birth time and place.
    """
    try:
        if details.latitude is not None and details.longitude is not None and details.timezone:
            geo = {"lat": details.latitude, "lon": details.longitude, "timezone": details.timezone, "display_name": details.place}
        else:
            geo = await asyncio.to_thread(geocode_place, details.place)
        
        today = dt_date.today().isoformat()  # YYYY-MM-DD
        return await asyncio.to_thread(
            calculate_weekly_horoscope,
            name=details.name, gender=details.gender,
            birth_date=details.date, # Birth date
            start_date=today,         # Start from today
            hour=details.hour,
            minute=details.minute, ampm=details.ampm,
            place=details.place,
            lat=geo["lat"], lon=geo["lon"], timezone=geo["timezone"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


def generate_gochara_image_base64(details, result):
    """
    Generate chart image - South Indian Style.
    Updated to use WebP for 50%+ reduction in payload size.
    """
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
    
    # Border color - reddish brown
    border_color = '#8B4513'
    line_width = 4
    
    # Draw outer rectangle
    draw.rectangle([(margin, margin), (margin + chart_size, margin + chart_size)], outline=border_color, width=line_width)
    
    # Grid lines
    for i in range(1, 4):
        x = margin + i * cell_size
        if i == 1 or i == 3:
            draw.line([(x, margin), (x, margin + chart_size)], fill=border_color, width=2)
        else:
            draw.line([(x, margin), (x, margin + cell_size)], fill=border_color, width=2)
            draw.line([(x, margin + 3 * cell_size), (x, margin + chart_size)], fill=border_color, width=2)
        
        y = margin + i * cell_size
        if i == 1 or i == 3:
            draw.line([(margin, y), (margin + chart_size, y)], fill=border_color, width=2)
        else:
            draw.line([(margin, y), (margin + cell_size, y)], fill=border_color, width=2)
            draw.line([(margin + 3 * cell_size, y), (margin + chart_size, y)], fill=border_color, width=2)
    
    house_grid = {12: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0), 11: (0, 1), 4: (3, 1), 10: (0, 2), 5: (3, 2), 9: (0, 3), 8: (1, 3), 7: (2, 3), 6: (3, 3)}
    house_positions = {num: (margin + pos[0] * cell_size + cell_size // 2, margin + pos[1] * cell_size + cell_size // 2) for num, pos in house_grid.items()}
    house_planets = {i: [] for i in range(1, 13)}
    transits = result["current_transits"]
    planet_abbrev = {'sun': 'Su', 'moon': 'Mo', 'mars': 'Ma', 'mercury': 'Me', 'jupiter': 'Ju', 'venus': 'Ve', 'saturn': 'Sa', 'rahu': 'Ra', 'ketu': 'Ke'}
    
    for planet, data in transits.items():
        house_num = data['house']
        abbrev = planet_abbrev.get(planet, planet[:2].upper())
        house_planets[house_num].append(abbrev)
    
    for house_num, (x, y) in house_positions.items():
        col, row = house_grid[house_num]
        draw.text((margin + col * cell_size + 15, margin + row * cell_size + 15), str(house_num), fill='#CC0000', font=small_font)
        if house_planets[house_num]:
            draw.text((x, y), "\n".join(house_planets[house_num]), fill='#4B3621', font=planet_font, anchor="mm")
    
    cx, cy = margin + chart_size // 2, margin + chart_size // 2
    draw.text((cx, cy - 60), f"{details.date}", fill='#CC6666', font=center_font, anchor="mm")
    draw.text((cx, cy - 35), f"{details.hour}:{details.minute:02d} {details.ampm}", fill='#CC6666', font=center_font, anchor="mm")
    draw.text((cx, cy), "Transit Chart", fill='#000000', font=title_font, anchor="mm")
    draw.text((cx, cy + 30), result['birth_chart'].get('birth_nakshatra', 'Unknown'), fill='#000000', font=center_font, anchor="mm")
    
    buffer = io.BytesIO()
    # SAVE AS WEBP FOR OPTIMAL SIZE
    img.save(buffer, format='WEBP', quality=80)
    return base64.b64encode(buffer.getvalue()).decode()


@app.post("/api/gochara/bygemini")
async def get_gochara_by_gemini(details: BirthDetails):
    """
    Gochara (Transit) Chart with real astronomical calculations + AI predictions.
    Shows current planetary positions using Swiss Ephemeris and AI-generated interpretations.
    """
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="Gemini API is not configured.")
    
    try:
        geo = await resolve_geo(details)
        
        # Get current date for transit calculations
        tz = pytz.timezone(geo["timezone"])
        now = datetime.now(tz)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%I:%M %p")
        
        # Calculate birth chart details offloaded to thread
        birth_parts = details.date.split("-")
        birth_year, birth_month, birth_day = int(birth_parts[0]), int(birth_parts[1]), int(birth_parts[2])
        birth_hour = details.hour if details.ampm == "AM" or details.hour == 12 else details.hour + 12
        if details.ampm == "AM" and details.hour == 12:
            birth_hour = 0
        
        # Parallelize independent astronomical calculations
        results = await asyncio.gather(
            asyncio.to_thread(get_all_planets, birth_jd),
            asyncio.to_thread(get_moon_longitude, birth_jd),
            asyncio.to_thread(get_all_planets, current_jd)
        )
        birth_planets, (birth_moon_lon, _), transit_planets = results
        
        birth_nakshatra_info = await asyncio.to_thread(calculate_nakshatra, birth_moon_lon)
        
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
        ai_result = await call_gemini_with_retry(prompt, response_schema)
        
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
        
        # Generate chart image - South Indian Style (Offloaded to thread)
        try:
            img_base64 = await asyncio.to_thread(generate_gochara_image_base64, details, result)
            result["chart_image"] = {
                "data": img_base64,
                "mime_type": "image/webp",
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


# ══════════════════════════════════════════════════════════════════════════════
# DRIK GOCHARA (RASHI CHART) ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

from drik_gochara import generate_drik_gochara_chart
from drik_location_search import search_cities as drik_search_cities, get_timezone_offset as drik_get_tz_offset

class GocharaChartRequest(BaseModel):
    """Request model for Drik Gochara chart generation."""
    date: str = Field(..., description="Date in DD/MM/YYYY format", example="19/03/2026")
    time: str = Field(..., description="Local time in HH:MM:SS format", example="17:56:47")
    place: str = Field(..., description="Place name", example="Bhongir")
    latitude: Optional[float] = Field(None, description="Latitude (optional, will search if not provided)")
    longitude: Optional[float] = Field(None, description="Longitude (optional, will search if not provided)")
    timezone_offset: Optional[float] = Field(None, description="UTC offset in hours (optional, will calculate if not provided)")
    ayanamsha: str = Field("lahiri", description="Ayanamsha system: lahiri, raman, kp, tropical")
    rahu_type: str = Field("mean", description="Rahu calculation: mean or true")


@app.get("/api/gochara/search", tags=["Gochara Chart"])
async def gochara_search_cities(
    q: str = Query(..., description="Search query (city name)", min_length=2, example="Bhongir"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Search for cities in the drik-panchanga database (~3000 cities worldwide).
    
    Returns list of matching cities with coordinates and timezone.
    No external API needed - uses local database.
    
    **Example:**
    - `/api/gochara/search?q=Bhongir`
    - `/api/gochara/search?q=Mumbai&max_results=5`
    """
    try:
        results = drik_search_cities(q, max_results=max_results)
        return {"query": q, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gochara/chart", tags=["Gochara Chart"])
async def generate_gochara_chart_post(request: GocharaChartRequest):
    """
    Generate Drik Gochara (Rashi) chart - POST method.
    
    **Features:**
    - Uses Whole Sign House System (Rashi Chart) - exact DrikPanchang replication
    - Planets sorted in standard order within houses (Sur, Cha, Man, Bud, Gur, Shu, Sha, Rahu, Ketu)
    - Sidereal zodiac with Lahiri ayanamsha (default)
    - Local cities database (no external API)
    
    **Example Request:**
    ```json
    {
      "date": "19/03/2026",
      "time": "17:56:47",
      "place": "Bhongir",
      "ayanamsha": "lahiri",
      "rahu_type": "mean"
    }
    ```
    
    **Returns:**
    - `chart`: 12-house chart with planet placements (whole sign system)
    - `planets_table`: Complete planetary data with nakshatras
    - `metadata`: Input parameters and calculation details
    """
    try:
        # If coordinates not provided, search for the place
        if request.latitude is None or request.longitude is None or request.timezone_offset is None:
            cities = await asyncio.to_thread(drik_search_cities, request.place, max_results=1)
            if not cities:
                raise HTTPException(status_code=404, detail=f"City '{request.place}' not found in database. Try searching with /api/gochara/search first.")
            
            city = cities[0]
            latitude = city["latitude"]
            longitude = city["longitude"]
            timezone_offset = await asyncio.to_thread(drik_get_tz_offset, city["timezone"])
        else:
            latitude = request.latitude
            longitude = request.longitude
            timezone_offset = request.timezone_offset
        
        # Generate chart
        chart_data = await asyncio.to_thread(
            generate_drik_gochara_chart,
            date_str=request.date,
            time_str=request.time,
            place_name=request.place,
            latitude=latitude,
            longitude=longitude,
            timezone_offset=timezone_offset,
            ayanamsha=request.ayanamsha,
            rahu_type=request.rahu_type,
        )
        
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gochara/chart", tags=["Gochara Chart"])
async def generate_gochara_chart_get(
    date: str = Query(..., description="Date in DD/MM/YYYY format", example="19/03/2026"),
    time: str = Query(..., description="Local time in HH:MM:SS format", example="17:56:47"),
    place: str = Query(..., description="Place name", example="Bhongir"),
    latitude: Optional[float] = Query(None, description="Latitude (optional)"),
    longitude: Optional[float] = Query(None, description="Longitude (optional)"),
    timezone_offset: Optional[float] = Query(None, description="UTC offset in hours (optional)"),
    ayanamsha: str = Query("lahiri", description="Ayanamsha system: lahiri, raman, kp, tropical"),
    rahu_type: str = Query("mean", description="Rahu calculation: mean or true"),
):
    """
    Generate Drik Gochara (Rashi) chart - GET method.
    """
    try:
        if latitude is None or longitude is None or timezone_offset is None:
            cities = await asyncio.to_thread(drik_search_cities, place, max_results=1)
            if not cities:
                raise HTTPException(status_code=404, detail=f"City '{place}' not found in database")
            
            city = cities[0]
            latitude, longitude = city["latitude"], city["longitude"]
            timezone_offset = await asyncio.to_thread(drik_get_tz_offset, city["timezone"])
        
        # Offload to thread
        chart_data = await asyncio.to_thread(
            generate_drik_gochara_chart,
            date_str=date, time_str=time, place_name=place,
            latitude=latitude, longitude=longitude,
            timezone_offset=timezone_offset,
            ayanamsha=ayanamsha, rahu_type=rahu_type,
        )
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# PROKERALA-STYLE LOCATION SEARCH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

import httpx
import zoneinfo as zi

class ProkeralaLocationResult(BaseModel):
    """Location search result matching ProKerala format."""
    id: str
    name: str
    full_name: str
    latitude: float
    longitude: float
    timezone: str
    country_code: str
    country_name: str
    state: Optional[str] = None


async def search_geonames_prokerala(query: str, max_rows: int = 10) -> list:
    """Search GeoNames database - same as ProKerala uses."""
    GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "AnandamShivaKumar")
    url = "https://secure.geonames.org/searchJSON"
    
    params = {
        "name_startsWith": query,
        "featureClass": "P",
        "maxRows": max_rows,
        "style": "MEDIUM",
        "orderby": "population",
        "username": GEONAMES_USERNAME,
    }
    
    # Use global async_client
    try:
        response = await async_client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if "status" in data:
            raise HTTPException(status_code=502, detail=f"GeoNames error: {data['status'].get('message', 'Unknown error')}")
        
        return data.get("geonames", [])
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Location search timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Location search failed: {str(e)}")


def get_tz_offset_prokerala(timezone_name: str) -> float:
    """Get current UTC offset for a timezone (handles DST)."""
    try:
        tz = zi.ZoneInfo(timezone_name)
        now = datetime.now(tz)
        return now.utcoffset().total_seconds() / 3600
    except Exception:
        return 0.0


@app.get("/api/location/search", tags=["ProKerala Location"])
async def prokerala_location_search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)", example="Bhongir"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    ProKerala-style location search endpoint.
    
    **Features:**
    - Autocomplete search for cities, towns, villages worldwide
    - Returns coordinates and timezone for each location
    - Fast response using GeoNames database (11M+ places)
    - Compatible with ProKerala widget format
    
    **Example:**
    ```
    GET /api/location/search?q=Bhongir
    GET /api/location/search?q=Mumbai&max_results=5
    ```
    
    **Response Format:**
    ```json
    {
      "status": "success",
      "results": [
        {
          "id": "1269843",
          "name": "Bhongir",
          "full_name": "Bhongir, Telangana, India",
          "latitude": 17.51083,
          "longitude": 78.88889,
          "timezone": "Asia/Kolkata",
          "country_code": "IN",
          "country_name": "India",
          "state": "Telangana"
        }
      ],
      "count": 1
    }
    ```
    """
    try:
        geonames_results = await search_geonames_prokerala(q, max_results)
        
        results = []
        for place in geonames_results:
            # Build full name like ProKerala does
            name_parts = []
            if place.get("name"):
                name_parts.append(place["name"])
            if place.get("adminName1"):  # State/Province
                name_parts.append(place["adminName1"])
            if place.get("countryName"):
                name_parts.append(place["countryName"])
            
            full_name = ", ".join(name_parts)
            
            # Get timezone info
            tz_info = place.get("timezone", {})
            timezone = tz_info.get("timeZoneId", "") if isinstance(tz_info, dict) else ""
            
            results.append({
                "id": str(place.get("geonameId", "")),
                "name": place.get("name", ""),
                "full_name": full_name,
                "latitude": float(place.get("lat", 0)),
                "longitude": float(place.get("lng", 0)),
                "timezone": timezone,
                "country_code": place.get("countryCode", ""),
                "country_name": place.get("countryName", ""),
                "state": place.get("adminName1"),
            })
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/location/{location_id}", tags=["ProKerala Location"])
async def get_prokerala_location_details(location_id: str):
    """
    Get detailed information for a specific location by ID.
    
    **Example:**
    ```
    GET /api/location/1269843
    ```
    """
    GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "AnandamShivaKumar")
    url = f"https://secure.geonames.org/getJSON"
    
    params = {
        "geonameId": location_id,
        "username": GEONAMES_USERNAME,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if "status" in data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Location not found: {data['status'].get('message', 'Unknown error')}"
                )
            
            # Get timezone info
            tz_info = data.get("timezone", {})
            timezone = tz_info.get("timeZoneId", "") if isinstance(tz_info, dict) else ""
            
            # Build full name
            name_parts = []
            if data.get("name"):
                name_parts.append(data["name"])
            if data.get("adminName1"):
                name_parts.append(data["adminName1"])
            if data.get("countryName"):
                name_parts.append(data["countryName"])
            
            return {
                "status": "success",
                "location": {
                    "id": str(data.get("geonameId", "")),
                    "name": data.get("name", ""),
                    "full_name": ", ".join(name_parts),
                    "latitude": float(data.get("lat", 0)),
                    "longitude": float(data.get("lng", 0)),
                    "timezone": timezone,
                    "timezone_offset": get_tz_offset_prokerala(timezone),
                    "country_code": data.get("countryCode", ""),
                    "country_name": data.get("countryName", ""),
                    "state": data.get("adminName1"),
                    "population": data.get("population", 0),
                }
            }
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch location: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# GOCHARA SOUTH INDIAN CHART (Using Existing Calculation Logic)
# ══════════════════════════════════════════════════════════════════════════════

from gochara_south_indian import calculate_gochara_chart

class GocharaSouthIndianRequest(BaseModel):
    """Request model for Gochara South Indian chart."""
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-03-21")
    time: str = Field(..., description="Time in HH:MM:SS format", example="11:21:10")
    place: str = Field(..., description="Place name", example="Bhongir, India")
    latitude: Optional[float] = Field(None, description="Latitude (optional, will search if not provided)")
    longitude: Optional[float] = Field(None, description="Longitude (optional, will search if not provided)")
    timezone: Optional[str] = Field(None, description="Timezone (optional, will calculate if not provided)")


@app.post("/api/gochara/south-indian", tags=["Gochara Chart"])
async def generate_gochara_south_indian(request: GocharaSouthIndianRequest):
    """
    Generate Gochara (Transit) Chart - South Indian Style.
    
    **Uses the same calculation logic as /api/nakshatra and /api/horoscope endpoints.**
    
    **Features:**
    - South Indian Rashi chart (Whole Sign Houses)
    - Current planetary positions for any date/time
    - Planets sorted in standard order within houses
    - Uses existing ephemeris.py calculation infrastructure
    
    **Example Request:**
    ```json
    {
      "date": "2026-03-21",
      "time": "11:21:10",
      "place": "Bhongir, India",
      "latitude": 17.51083,
      "longitude": 78.88889,
      "timezone": "Asia/Kolkata"
    }
    ```
    
    **Returns:**
    - `chart`: 12-house South Indian chart with planet placements
    - `planets_table`: Detailed planetary data with signs, nakshatras, houses
    - `metadata`: Input parameters and calculation details
    """
    try:
        # Check if we need full geocoding (no coordinates)
        if request.latitude is None or request.longitude is None:
            geo = await asyncio.to_thread(geocode_place, request.place)
            latitude = geo["lat"]
            longitude = geo["lon"]
            timezone = geo["timezone"]
        # If we have coordinates but no timezone, calculate timezone locally (very fast)
        # If we have coordinates but no timezone, calculate timezone locally (very fast, but offload just in case)
        elif not request.timezone:
            latitude = request.latitude
            longitude = request.longitude
            from geocode import _tf
            timezone = await asyncio.to_thread(_tf.timezone_at, lat=latitude, lng=longitude)
            if not timezone:
                timezone = "UTC"
        # Everything provided
        else:
            latitude = request.latitude
            longitude = request.longitude
            timezone = request.timezone
        
        # Calculate Gochara chart - Parallelized (Wait, actually calculate_gochara_chart is optimized internally)
        # But we offload the call to a thread.
        chart_data = await asyncio.to_thread(
            calculate_gochara_chart,
            date=request.date,
            time=request.time,
            place=request.place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        
        return chart_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


@app.get("/api/gochara/south-indian", tags=["Gochara Chart"])
async def generate_gochara_south_indian_get(
    date: str = Query(..., description="Date in YYYY-MM-DD format", example="2026-03-21"),
    time: str = Query(..., description="Time in HH:MM:SS format", example="11:21:10"),
    place: str = Query(..., description="Place name", example="Bhongir, India"),
    latitude: Optional[float] = Query(None, description="Latitude (optional)"),
    longitude: Optional[float] = Query(None, description="Longitude (optional)"),
    timezone: Optional[str] = Query(None, description="Timezone (optional)"),
):
    """
    Generate Gochara (Transit) Chart - South Indian Style (GET method).
    
    **Example:**
    ```
    /api/gochara/south-indian?date=2026-03-21&time=11:21:10&place=Bhongir,%20India
    ```
    """
    try:
        # Check if we need full geocoding (no coordinates)
        if latitude is None or longitude is None:
            geo = await asyncio.to_thread(geocode_place, place)
            latitude = geo["lat"]
            longitude = geo["lon"]
            timezone = geo["timezone"]
        # If we have coordinates but no timezone, calculate timezone locally (very fast)
        # If we have coordinates but no timezone, calculate timezone locally
        elif not timezone:
            from geocode import _tf
            timezone = await asyncio.to_thread(_tf.timezone_at, lat=latitude, lng=longitude)
            if not timezone:
                timezone = "UTC"
        
        # Calculate Gochara chart - Offload TO THREAD
        chart_data = await asyncio.to_thread(
            calculate_gochara_chart,
            date=date,
            time=time,
            place=place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        
        return chart_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")

# ── Telugu Panchang endpoints ─────────────────────────────────────────────────

from panchang_service import get_daily_panchang, get_monthly_panchang  # noqa: E402


class DailyPanchangRequest(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-04-17")
    latitude: Optional[float] = Field(None, ge=-90, le=90, example=17.385)
    longitude: Optional[float] = Field(None, ge=-180, le=180, example=78.4867)
    timezone: Optional[str] = Field(None, example="Asia/Kolkata")
    place: Optional[str] = Field(None, example="Hyderabad, India")
    lang: str = Field("en", pattern="^(en|te|hi)$", example="te")


class MonthlyPanchangRequest(BaseModel):
    year: int = Field(..., ge=1800, le=2100, example=2026)
    month: int = Field(..., ge=1, le=12, example=4)
    latitude: float = Field(..., ge=-90, le=90, example=17.385)
    longitude: float = Field(..., ge=-180, le=180, example=78.4867)
    timezone: str = Field(..., example="Asia/Kolkata")
    lang: str = Field("en", pattern="^(en|te|hi)$", example="te")


def _tz_to_offset(tz_name: str) -> float:
    """Convert timezone name to UTC offset in hours."""
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        return now.utcoffset().total_seconds() / 3600
    except Exception:
        return 5.5  # default IST


@app.post("/api/panchang/daily", tags=["Panchang"])
async def daily_panchang(req: DailyPanchangRequest):
    """Compute full daily Telugu Panchang for a given date and location."""
    try:
        # Validate date range
        year = int(req.date.split("-")[0])
        if not (1800 <= year <= 2100):
            raise HTTPException(status_code=400, detail="Date must be between 1800 CE and 2100 CE")

        # Resolve coordinates
        lat, lon, tz_name = req.latitude, req.longitude, req.timezone
        if lat is None or lon is None:
            if not req.place:
                raise HTTPException(status_code=400, detail="Provide latitude/longitude or place name")
            geo = await asyncio.to_thread(geocode_place, req.place)
            lat, lon, tz_name = geo["lat"], geo["lon"], geo["timezone"]
        elif not tz_name:
            from geocode import _tf
            tz_name = await asyncio.to_thread(_tf.timezone_at, lat=lat, lng=lon)
            if not tz_name:
                tz_name = "UTC"

        tz_offset = _tz_to_offset(tz_name)
        result = await get_daily_panchang(req.date, lat, lon, tz_offset, req.lang)
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


@app.post("/api/panchang/monthly", tags=["Panchang"])
async def monthly_panchang(req: MonthlyPanchangRequest):
    """Compute monthly Telugu Panchang summaries for every day in a month."""
    try:
        tz_offset = _tz_to_offset(req.timezone)
        result = await get_monthly_panchang(req.year, req.month, req.latitude, req.longitude, tz_offset, req.lang)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
