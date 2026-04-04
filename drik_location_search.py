"""
drik_location_search.py
=======================
Location search using the drik-panchanga cities database.

No external API dependencies - uses local JSON file.
"""

import json
import os
from typing import List, Dict


def load_cities_database() -> Dict:
    """Load cities database from drik-panchanga."""
    cities_file = "drik-panchanga/cities.json"
    
    if not os.path.exists(cities_file):
        raise FileNotFoundError(
            f"Cities database not found at {cities_file}. "
            "Please ensure drik-panchanga repository is cloned."
        )
    
    with open(cities_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_cities(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search for cities matching the query.
    
    Parameters
    ----------
    query : str
        Search query (city name)
    max_results : int
        Maximum number of results to return
    
    Returns
    -------
    List of dicts with city information
    """
    cities_db = load_cities_database()
    
    query_lower = query.lower()
    results = []
    
    for city_name, city_data in cities_db.items():
        if query_lower in city_name.lower():
            results.append({
                "name": city_name,
                "latitude": city_data["latitude"],
                "longitude": city_data["longitude"],
                "timezone": city_data["timezone"],
                "display": city_name,
            })
            
            if len(results) >= max_results:
                break
    
    return results


def get_city_info(city_name: str) -> Dict:
    """
    Get information for a specific city.
    
    Parameters
    ----------
    city_name : str
        Exact city name
    
    Returns
    -------
    Dict with city information
    """
    cities_db = load_cities_database()
    
    if city_name in cities_db:
        city_data = cities_db[city_name]
        return {
            "name": city_name,
            "latitude": city_data["latitude"],
            "longitude": city_data["longitude"],
            "timezone": city_data["timezone"],
            "display": city_name,
        }
    else:
        raise ValueError(f"City '{city_name}' not found in database")


def get_timezone_offset(timezone_name: str, date_str: str = None, time_str: str = None) -> float:
    """
    Get UTC offset for a timezone.
    
    For simplicity, returns standard offsets. DST handling would require pytz.
    """
    # Common timezone offsets (standard time, not DST)
    timezone_offsets = {
        "Asia/Kolkata": 5.5,
        "Asia/Calcutta": 5.5,
        "Asia/Karachi": 5.0,
        "Asia/Dhaka": 6.0,
        "Asia/Kathmandu": 5.75,
        "Asia/Dubai": 4.0,
        "Asia/Tokyo": 9.0,
        "Asia/Shanghai": 8.0,
        "Asia/Singapore": 8.0,
        "Asia/Bangkok": 7.0,
        "Asia/Jakarta": 7.0,
        "Asia/Manila": 8.0,
        "Asia/Seoul": 9.0,
        "Asia/Taipei": 8.0,
        "Asia/Hong_Kong": 8.0,
        "Asia/Kuala_Lumpur": 8.0,
        "Asia/Tehran": 3.5,
        "Asia/Baghdad": 3.0,
        "Asia/Riyadh": 3.0,
        "Asia/Jerusalem": 2.0,
        "Asia/Istanbul": 3.0,
        "Europe/London": 0.0,
        "Europe/Paris": 1.0,
        "Europe/Berlin": 1.0,
        "Europe/Rome": 1.0,
        "Europe/Madrid": 1.0,
        "Europe/Moscow": 3.0,
        "America/New_York": -5.0,
        "America/Chicago": -6.0,
        "America/Denver": -7.0,
        "America/Los_Angeles": -8.0,
        "America/Toronto": -5.0,
        "America/Mexico_City": -6.0,
        "America/Sao_Paulo": -3.0,
        "America/Buenos_Aires": -3.0,
        "America/Caracas": -4.0,
        "America/Lima": -5.0,
        "America/Bogota": -5.0,
        "America/Santiago": -4.0,
        "Africa/Cairo": 2.0,
        "Africa/Johannesburg": 2.0,
        "Africa/Lagos": 1.0,
        "Africa/Nairobi": 3.0,
        "Australia/Sydney": 10.0,
        "Australia/Melbourne": 10.0,
        "Australia/Perth": 8.0,
        "Pacific/Auckland": 12.0,
    }
    
    return timezone_offsets.get(timezone_name, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# DEMO / MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 80)
    print("DRIK LOCATION SEARCH - Using drik-panchanga cities database")
    print("=" * 80)
    print()
    
    # Test search
    query = "Bhongir"
    print(f"Searching for '{query}'...")
    print()
    
    results = search_cities(query, max_results=5)
    
    if results:
        print(f"Found {len(results)} result(s):\n")
        print(f"{'#':<3} {'City Name':<30} {'Latitude':>10} {'Longitude':>10} {'Timezone':>20}")
        print("-" * 80)
        
        for i, city in enumerate(results, 1):
            tz_offset = get_timezone_offset(city["timezone"])
            print(f"{i:<3} {city['name']:<30} {city['latitude']:>10.4f} {city['longitude']:>10.4f} "
                  f"{city['timezone']:>20} (UTC{tz_offset:+.1f})")
        
        print()
        print(f"Using first result: {results[0]['name']}")
        print(f"  Coordinates: {results[0]['latitude']}, {results[0]['longitude']}")
        print(f"  Timezone: {results[0]['timezone']}")
        print(f"  UTC Offset: {get_timezone_offset(results[0]['timezone']):+.1f} hours")
    else:
        print(f"No results found for '{query}'")
