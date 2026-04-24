"""
Geocoding module — GeoNames (primary) + Photon (fallback).

GeoNames: 11M+ places, every village/hamlet. Needs free account.
Photon:   Free, no registration, uses OpenStreetMap data.

Both find small villages like Yergatla, Metpalli, Bhattiprolu etc.

Set env var GEONAMES_USERNAME to your free GeoNames username.
If not set, Photon is used automatically.
"""

import os
import httpx
from timezonefinder import TimezoneFinder
from functools import lru_cache

GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "")
_tf = TimezoneFinder()
_HEADERS = {"User-Agent": "Mozilla/5.0 (NakshatraApp/2.0)"}

# Persistent HTTP client for connection pooling (much faster)
_http_client = None

def get_http_client():
    """Get or create persistent HTTP client for connection reuse."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=5.0,  # Reduced from 10s to 5s
            headers=_HEADERS,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )
    return _http_client

_sync_http_client = None

def get_sync_http_client():
    """Get or create persistent sync HTTP client for connection reuse."""
    global _sync_http_client
    if _sync_http_client is None:
        _sync_http_client = httpx.Client(
            timeout=10.0,
            headers=_HEADERS,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )
    return _sync_http_client


# ═══════════════════════════════════════════════════════════════════════════
#  SYNC geocode — used internally by /api/nakshatra & /api/horoscope
#  when frontend sends only place string (no lat/lon/timezone)
# ═══════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=128)
def geocode_place(place_name: str) -> dict:
    """
    Resolve a place string to {lat, lon, timezone, display_name}.
    Uses GeoNames if configured, else Photon — same engines as /api/places.
    Finds every village/hamlet on Earth.
    """
    if not place_name or not place_name.strip():
        raise ValueError("Place name cannot be empty")

    if GEONAMES_USERNAME:
        return _geocode_geonames_sync(place_name)
    return _geocode_photon_sync(place_name)


def _geocode_photon_sync(place_name: str) -> dict:
    """Photon sync search — pick top result."""
    url = "https://photon.komoot.io/api/"
    params = {"q": place_name.strip(), "limit": 1, "lang": "en"}

    client = get_sync_http_client()
    resp = client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    features = data.get("features", [])
    if not features:
        raise ValueError(f"Place not found: '{place_name}'")

    props = features[0].get("properties", {})
    coords = features[0].get("geometry", {}).get("coordinates", [0, 0])
    lon, lat = coords[0], coords[1]
    tz = _tf.timezone_at(lat=lat, lng=lon)
    if not tz:
        raise ValueError(f"Could not determine timezone for: {place_name}")

    name = props.get("name", "")
    admin1 = props.get("state", "")
    country = props.get("country", "")
    display = ", ".join(p for p in (name, admin1, country) if p) or place_name

    return {"lat": lat, "lon": lon, "timezone": tz, "display_name": display}


def _geocode_geonames_sync(place_name: str) -> dict:
    """GeoNames sync search — pick top result."""
    url = "http://api.geonames.org/searchJSON"
    params = {
        "q": place_name.strip(),
        "maxRows": 1,
        "featureClass": "P",
        "orderby": "relevance",
        "username": GEONAMES_USERNAME,
        "style": "MEDIUM",
    }

    client = get_sync_http_client()
    resp = client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if "status" in data:
        raise RuntimeError(data["status"].get("message", "GeoNames error"))

    geonames = data.get("geonames", [])
    if not geonames:
        raise ValueError(f"Place not found: '{place_name}'")

    g = geonames[0]
    lat = float(g["lat"])
    lon = float(g["lng"])
    tz = _tz_from_geonames(g, lat, lon)
    if not tz:
        raise ValueError(f"Could not determine timezone for: {place_name}")

    name = g.get("name", "")
    admin1 = g.get("adminName1", "")
    country = g.get("countryName", "")
    display = ", ".join(p for p in (name, admin1, country) if p) or place_name

    return {"lat": lat, "lon": lon, "timezone": tz, "display_name": display}


# ═══════════════════════════════════════════════════════════════════════════
#  ASYNC search — used by GET /api/places (autocomplete dropdown)
# ═══════════════════════════════════════════════════════════════════════════

_search_cache = {}
_MAX_CACHE_SIZE = 10000

async def search_places(query: str, max_rows: int = 10) -> list[dict]:
    """
    Search for populated places. Uses GeoNames if configured, else Photon.
    Returns list of {display, name, admin1, country, lat, lon, timezone, ...}.
    """
    if not query or len(query.strip()) < 2:
        return []
        
    cache_key = f"{query.strip().lower()}_{max_rows}"
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    if GEONAMES_USERNAME:
        result = await _search_geonames(query, max_rows)
    else:
        result = await _search_photon(query, max_rows)
        
    if len(_search_cache) >= _MAX_CACHE_SIZE:
        _search_cache.pop(next(iter(_search_cache)))
    _search_cache[cache_key] = result
    
    return result


async def _search_geonames(query: str, max_rows: int) -> list[dict]:
    url = "http://api.geonames.org/searchJSON"
    params = {
        "q": query.strip(),
        "maxRows": max_rows,
        "featureClass": "P",
        "orderby": "relevance",
        "username": GEONAMES_USERNAME,
        "style": "SHORT",  # Changed from MEDIUM to SHORT for faster response
    }

    client = get_http_client()
    resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if "status" in data:
        raise RuntimeError(data["status"].get("message", "GeoNames error"))

    results = []
    for g in data.get("geonames", []):
        lat = float(g["lat"])
        lon = float(g["lng"])
        # Optimize: skip timezone lookups during search autocomplete to save CPU
        tz = "" 

        name = g.get("name", "")
        admin1 = g.get("adminName1", "")
        country = g.get("countryName", "")
        display = ", ".join(p for p in (name, admin1, country) if p)

        results.append({
            "geoname_id": g.get("geonameId"),
            "name": name, "admin1": admin1, "country": country,
            "display": display,
            "lat": lat, "lon": lon, "timezone": tz,
            "population": g.get("population", 0),
            "feature_code": g.get("fcode", ""),
        })
    return results


async def _search_photon(query: str, max_rows: int) -> list[dict]:
    url = "https://photon.komoot.io/api/"
    params = {"q": query.strip(), "limit": max_rows, "lang": "en"}

    client = get_http_client()
    resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [0, 0])
        lon, lat = coords[0], coords[1]
        # Optimize: skip timezone lookups during search autocomplete to save CPU
        tz = "" 

        name = props.get("name", "")
        admin1 = props.get("state", "")
        country = props.get("country", "")
        display = ", ".join(p for p in (name, admin1, country) if p)

        results.append({
            "geoname_id": props.get("osm_id"),
            "name": name, "admin1": admin1, "country": country,
            "display": display,
            "lat": lat, "lon": lon, "timezone": tz,
            "population": props.get("population", 0),
            "feature_code": props.get("osm_value", ""),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════
def _tz_from_geonames(rec: dict, lat: float, lon: float) -> str:
    tz = rec.get("timezone", {})
    if isinstance(tz, dict):
        tz = tz.get("timeZoneId", "")
    if tz:
        return tz
    return _tf.timezone_at(lat=lat, lng=lon) or "UTC"
