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

# ── Global Shared Assets ──────────────────────────────────────────────────
# Persistent HTTP client for connection pooling
# This will be initialized in the lifespan event
async_client = None

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
