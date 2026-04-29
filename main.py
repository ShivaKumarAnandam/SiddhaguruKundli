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
import socket
import re

import httpx
import pytz
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from ephemeris import (
    get_all_planets, get_moon_longitude, local_to_julian_day,
    longitude_to_nakshatra, longitude_to_sign, calculate_house_from_ascendant
)
from geocode import geocode_place, search_places
from nakshatra import calculate_nakshatra
from gochara_south_indian import calculate_gochara_chart


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
app.add_middleware(GZipMiddleware, minimum_size=2000)

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
@app.get("/api/places", response_class=ORJSONResponse)
async def places_search(
    response: Response,
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
        response.headers["Cache-Control"] = "public, max-age=86400"
        return {"query": q, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GeoNames search failed: {e}")

@app.get("/api/health")
async def health_check(response: Response):
    """Lightweight endpoint for frontend to wake up the server (Cold Start Mitigation)."""
    response.headers["Cache-Control"] = "no-cache"
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ── API Endpoints ─────────────────────────────────────────────────────────
@app.post("/api/nakshatra", response_class=ORJSONResponse)
async def get_nakshatra(details: BirthDetails):
    try:
        geo = await resolve_geo(details)
        year, month, day = map(int, details.date.split("-"))
        hour24, minute = parse_to_24h(details.hour, details.minute, details.ampm)
        
        # Consolidated calculation to minimize thread overhead
        def run_calculation():
            jd = local_to_julian_day(year, month, day, hour24, minute, geo["timezone"])
            moon_lon, moon_speed = get_moon_longitude(jd)
            return jd, calculate_nakshatra(moon_lon, moon_speed)

        jd, nk = await asyncio.to_thread(run_calculation)

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








# ══════════════════════════════════════════════════════════════════════════════
# GOCHARA SOUTH INDIAN CHART (Using Existing Calculation Logic)
# ══════════════════════════════════════════════════════════════════════════════

class GocharaSouthIndianRequest(BaseModel):
    """Request model for Gochara South Indian chart."""
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-03-21")
    time: str = Field(..., description="Time in HH:MM:SS format", example="11:21:10")
    place: str = Field(..., description="Place name", example="Bhongir, India")
    latitude: Optional[float] = Field(None, description="Latitude (optional, will search if not provided)")
    longitude: Optional[float] = Field(None, description="Longitude (optional, will search if not provided)")
    timezone: Optional[str] = Field(None, description="Timezone (optional, will calculate if not provided)")


@app.post("/api/gochara/south-indian", tags=["Gochara Chart"], response_class=ORJSONResponse)
async def generate_gochara_south_indian(request: GocharaSouthIndianRequest):
    """
    Generate Gochara (Transit) Chart - South Indian Style.
    Consolidated thread-execution for ultra-fast response.
    """
    try:
        def run_all():
            # 1. Resolve Geo (In one thread)
            lat, lon, tz = request.latitude, request.longitude, request.timezone
            if lat is None or lon is None:
                geo = geocode_place(request.place)
                lat, lon, tz = geo["lat"], geo["lon"], geo["timezone"]
            elif not tz:
                from geocode import _tf
                tz = _tf.timezone_at(lat=lat, lng=lon) or "UTC"
            
            # 2. Calculate Chart (In same thread)
            from gochara_south_indian import calculate_gochara_chart
            return calculate_gochara_chart(
                date=request.date,
                time=request.time,
                place=request.place,
                latitude=lat,
                longitude=lon,
                timezone=tz,
            )

        chart_data = await asyncio.to_thread(run_all)
        return chart_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {e}")


@app.get("/api/gochara/south-indian", tags=["Gochara Chart"], response_class=ORJSONResponse)
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
        def run_all():
            lat, lon, tz = latitude, longitude, timezone
            if lat is None or lon is None:
                geo = geocode_place(place)
                lat, lon, tz = geo["lat"], geo["lon"], geo["timezone"]
            elif not tz:
                from geocode import _tf
                tz = _tf.timezone_at(lat=lat, lng=lon) or "UTC"

            from gochara_south_indian import calculate_gochara_chart
            return calculate_gochara_chart(
                date=date,
                time=time,
                place=place,
                latitude=lat,
                longitude=lon,
                timezone=tz,
            )

        chart_data = await asyncio.to_thread(run_all)
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


@app.post("/api/panchang/daily", tags=["Panchang"], response_class=ORJSONResponse)
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


@app.post("/api/panchang/monthly", tags=["Panchang"], response_class=ORJSONResponse)
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


def get_local_ip():
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connection not actually established, just used to find the interface
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def update_flutter_api_service(ip_address):
    """Updates the api_service.dart file in the Flutter project with the current IP."""
    # Path to api_service.dart (adjusting relative to Backend directory)
    api_service_path = os.path.join("..", "SiddhaguruAstrology", "lib", "core", "api_service.dart")
    
    if not os.path.exists(api_service_path):
        print(f"⚠️  Warning: api_service.dart not found at {api_service_path}")
        return

    try:
        with open(api_service_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Regex to find the local IP line in baseUrl getter
        # Matches return 'http://<any_ip>:<any_port>/api';
        pattern = r"return 'http://[\d\.]+:(\d+)/api';"
        replacement = f"return 'http://{ip_address}:\\1/api';"
        
        new_content = re.sub(pattern, replacement, content)

        if content != new_content:
            with open(api_service_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"🚀 Updated Flutter ApiService with IP: {ip_address}")
        else:
            print(f"✅ Flutter ApiService is already up to date with IP: {ip_address}")

    except Exception as e:
        print(f"❌ Failed to update api_service.dart: {e}")

if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"📡 Detected Local IP: {local_ip}")
    update_flutter_api_service(local_ip)
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
