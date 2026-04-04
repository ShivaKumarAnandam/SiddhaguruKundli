"""
prokerala_location_api.py
==========================
ProKerala-style location search API using GeoNames.

Replicates the ProKerala location widget functionality:
- Autocomplete location search
- Returns coordinates and timezone
- Fast and accurate results

This can be integrated into main.py or run standalone.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from datetime import datetime
import zoneinfo

# GeoNames username - get free account at https://www.geonames.org/login
GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "AnandamShivaKumar")

app = FastAPI(
    title="ProKerala-style Location API",
    description="Location search API compatible with ProKerala astrology widget",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LocationResult(BaseModel):
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


class LocationSearchResponse(BaseModel):
    """Response format matching ProKerala API."""
    status: str = "success"
    results: List[LocationResult]
    count: int


async def search_geonames(query: str, max_rows: int = 10) -> List[dict]:
    """
    Search GeoNames database for locations.
    
    This is the same API that DrikPanchang and many astrology sites use.
    """
    url = "https://secure.geonames.org/searchJSON"
    
    params = {
        "name_startsWith": query,
        "featureClass": "P",  # Populated places (cities, towns, villages)
        "maxRows": max_rows,
        "style": "MEDIUM",  # Includes timezone
        "orderby": "population",  # Most populated first
        "username": GEONAMES_USERNAME,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if "status" in data:
                raise HTTPException(
                    status_code=502,
                    detail=f"GeoNames error: {data['status'].get('message', 'Unknown error')}"
                )
            
            return data.get("geonames", [])
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Location search timed out")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Location search failed: {str(e)}")


def get_timezone_offset(timezone_name: str) -> float:
    """Get current UTC offset for a timezone (handles DST automatically)."""
    try:
        tz = zoneinfo.ZoneInfo(timezone_name)
        now = datetime.now(tz)
        return now.utcoffset().total_seconds() / 3600
    except Exception:
        return 0.0


@app.get("/api/location/search", response_model=LocationSearchResponse)
async def location_search(
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
        geonames_results = await search_geonames(q, max_results)
        
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
            
            results.append(LocationResult(
                id=str(place.get("geonameId", "")),
                name=place.get("name", ""),
                full_name=full_name,
                latitude=float(place.get("lat", 0)),
                longitude=float(place.get("lng", 0)),
                timezone=timezone,
                country_code=place.get("countryCode", ""),
                country_name=place.get("countryName", ""),
                state=place.get("adminName1"),
            ))
        
        return LocationSearchResponse(
            status="success",
            results=results,
            count=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/location/{location_id}")
async def get_location_details(location_id: str):
    """
    Get detailed information for a specific location by ID.
    
    **Example:**
    ```
    GET /api/location/1269843
    ```
    """
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
                    "timezone_offset": get_timezone_offset(timezone),
                    "country_code": data.get("countryCode", ""),
                    "country_name": data.get("countryName", ""),
                    "state": data.get("adminName1"),
                    "population": data.get("population", 0),
                }
            }
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch location: {str(e)}")


@app.get("/")
async def root():
    """API information."""
    return {
        "name": "ProKerala-style Location API",
        "version": "1.0.0",
        "description": "Location search API compatible with ProKerala astrology widget",
        "endpoints": {
            "search": "/api/location/search?q=<query>",
            "details": "/api/location/{location_id}",
            "docs": "/docs"
        },
        "features": [
            "Autocomplete location search",
            "11M+ places worldwide",
            "Timezone information",
            "Compatible with ProKerala format"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("PROKERALA-STYLE LOCATION API")
    print("=" * 80)
    print()
    print("Starting server on http://localhost:8001")
    print()
    print("📚 Swagger UI: http://localhost:8001/docs")
    print()
    print("Example endpoints:")
    print("  - Search: http://localhost:8001/api/location/search?q=Bhongir")
    print("  - Details: http://localhost:8001/api/location/1269843")
    print()
    print("=" * 80)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
