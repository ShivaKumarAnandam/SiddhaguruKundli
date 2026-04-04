"""
drik_gochara.py
===============
Exact DrikPanchang.com Gochara (Rashi) Chart Implementation

Uses whole sign houses (Rashi chart system) where:
- Each house is exactly 30 degrees
- House 1 starts at the Lagna rashi (sign)
- Planets are placed in houses based on their rashi, not degree-based cusps

This matches DrikPanchang's methodology exactly.
"""

import swisseph as swe
from datetime import datetime
from typing import Literal, Dict, List
import math


# ─────────────────────────────────────────────────────────────────────────────
# AYANAMSHA MAPPING
# ─────────────────────────────────────────────────────────────────────────────
AYANAMSHA_MAP = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "kp": swe.SIDM_KRISHNAMURTI,
    "tropical": None,
}


# ─────────────────────────────────────────────────────────────────────────────
# RASHI (SIGN) NAMES
# ─────────────────────────────────────────────────────────────────────────────
RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karkataka",
    "Simha", "Kanya", "Tula", "Vrishchika",
    "Dhanu", "Makara", "Kumbha", "Meena"
]

RASHI_ABBREV = [
    "Mesh", "Vrish", "Mith", "Kark",
    "Simh", "Kany", "Tula", "Vrish",
    "Dhan", "Maka", "Kumb", "Meen"
]


# ─────────────────────────────────────────────────────────────────────────────
# NAKSHATRA DATA
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_ABBREV = {
    "Ashwini": "Ashwini",
    "Bharani": "Bharani",
    "Krittika": "Krittika",
    "Rohini": "Rohini",
    "Mrigashira": "Mrigashira",
    "Ardra": "Ardra",
    "Punarvasu": "Punarvasu",
    "Pushya": "Pushya",
    "Ashlesha": "Ashlesha",
    "Magha": "Magha",
    "Purva Phalguni": "P Phalguni",
    "Uttara Phalguni": "U Phalguni",
    "Hasta": "Hasta",
    "Chitra": "Chitra",
    "Swati": "Swati",
    "Vishakha": "Vishakha",
    "Anuradha": "Anuradha",
    "Jyeshtha": "Jyeshtha",
    "Mula": "Mula",
    "Purva Ashadha": "P Ashadha",
    "Uttara Ashadha": "U Ashadha",
    "Shravana": "Shravana",
    "Dhanishta": "Dhanishta",
    "Shatabhisha": "Shatabhisha",
    "Purva Bhadrapada": "P Bhadrapada",
    "Uttara Bhadrapada": "U Bhadrapada",
    "Revati": "Revati",
}

NAKSHATRA_LORDS = {
    "Ashwini": ("Ketu", "Ketu"),
    "Bharani": ("Shukra", "Venus"),
    "Krittika": ("Surya", "Sun"),
    "Rohini": ("Chandra", "Moon"),
    "Mrigashira": ("Mangal", "Mars"),
    "Ardra": ("Rahu", "Rahu"),
    "Punarvasu": ("Guru", "Jupiter"),
    "Pushya": ("Shani", "Saturn"),
    "Ashlesha": ("Budha", "Mercury"),
    "Magha": ("Ketu", "Ketu"),
    "Purva Phalguni": ("Shukra", "Venus"),
    "Uttara Phalguni": ("Surya", "Sun"),
    "Hasta": ("Chandra", "Moon"),
    "Chitra": ("Mangal", "Mars"),
    "Swati": ("Rahu", "Rahu"),
    "Vishakha": ("Guru", "Jupiter"),
    "Anuradha": ("Shani", "Saturn"),
    "Jyeshtha": ("Budha", "Mercury"),
    "Mula": ("Ketu", "Ketu"),
    "Purva Ashadha": ("Shukra", "Venus"),
    "Uttara Ashadha": ("Surya", "Sun"),
    "Shravana": ("Chandra", "Moon"),
    "Dhanishta": ("Mangal", "Mars"),
    "Shatabhisha": ("Rahu", "Rahu"),
    "Purva Bhadrapada": ("Guru", "Jupiter"),
    "Uttara Bhadrapada": ("Shani", "Saturn"),
    "Revati": ("Budha", "Mercury"),
}


def compute_drik_planetary_positions(
    date_str: str,
    time_str: str,
    latitude: float,
    longitude: float,
    tz_offset: float,
    ayanamsha: Literal["lahiri", "raman", "kp", "tropical"] = "lahiri",
    rahu_type: Literal["mean", "true"] = "mean",
) -> dict:
    """
    Calculate planetary positions using Drik Panchanga methodology.
    
    This uses sidereal (Nirayana) positions with Lahiri ayanamsha by default.
    Also calculates Right Ascension (RA) and Declination for each planet.
    """
    
    # Parse date and time
    day, month, year = map(int, date_str.split('/'))
    hour, minute, second = map(int, time_str.split(':'))
    
    # Convert local time to UTC
    local_hour_decimal = hour + minute / 60.0 + second / 3600.0
    utc_hour_decimal = local_hour_decimal - tz_offset
    
    # Handle day overflow/underflow
    utc_day = day
    if utc_hour_decimal < 0:
        utc_hour_decimal += 24
        utc_day -= 1
    elif utc_hour_decimal >= 24:
        utc_hour_decimal -= 24
        utc_day += 1
    
    # Calculate Julian Day (UTC)
    jd_ut = swe.julday(year, month, utc_day, utc_hour_decimal)
    
    # Set ayanamsha
    if ayanamsha != "tropical" and ayanamsha in AYANAMSHA_MAP:
        swe.set_sid_mode(AYANAMSHA_MAP[ayanamsha])
    
    # Set calculation flags
    if ayanamsha == "tropical":
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    else:
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    # Flags for equatorial coordinates (RA/Dec)
    flags_equatorial = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL | swe.FLG_SPEED
    
    # Calculate all planets
    planet_ids = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO,
    }
    
    planets = {}
    speeds = {}
    right_ascensions = {}
    declinations = {}
    latitudes = {}
    
    for planet_name, planet_id in planet_ids.items():
        # Ecliptic coordinates (longitude, latitude, distance, speed)
        result, ret_flag = swe.calc_ut(jd_ut, planet_id, flags)
        planets[planet_name] = result[0]  # Longitude 0-360°
        latitudes[planet_name] = result[1]  # Latitude (Shara)
        speeds[planet_name] = result[3]   # Speed in degrees/day
        
        # Equatorial coordinates (RA, Dec)
        result_eq, ret_flag_eq = swe.calc_ut(jd_ut, planet_id, flags_equatorial)
        right_ascensions[planet_name] = result_eq[0]  # Right Ascension
        declinations[planet_name] = result_eq[1]  # Declination (Kranti)
    
    # Calculate Rahu and Ketu
    if rahu_type == "true":
        rahu_id = swe.TRUE_NODE
    else:
        rahu_id = swe.MEAN_NODE
    
    result, ret_flag = swe.calc_ut(jd_ut, rahu_id, flags)
    planets["Rahu"] = result[0]
    latitudes["Rahu"] = result[1]
    speeds["Rahu"] = result[3]
    
    # Equatorial for Rahu
    result_eq, ret_flag_eq = swe.calc_ut(jd_ut, rahu_id, flags_equatorial)
    right_ascensions["Rahu"] = result_eq[0]
    declinations["Rahu"] = result_eq[1]
    
    # Ketu is always 180° opposite to Rahu
    planets["Ketu"] = (planets["Rahu"] + 180) % 360
    latitudes["Ketu"] = -latitudes["Rahu"]  # Opposite latitude
    speeds["Ketu"] = speeds["Rahu"]
    right_ascensions["Ketu"] = (right_ascensions["Rahu"] + 180) % 360
    declinations["Ketu"] = -declinations["Rahu"]
    
    # Calculate Ascendant (Lagna)
    if ayanamsha == "tropical":
        houses, ascmc = swe.houses(jd_ut, latitude, longitude, b'P')
    else:
        houses, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b'P', flags)
    
    ascendant = ascmc[0]  # Lagna
    
    return {
        "planets": planets,
        "speeds": speeds,
        "right_ascensions": right_ascensions,
        "declinations": declinations,
        "latitudes": latitudes,
        "ascendant": ascendant,
        "julian_day": jd_ut,
    }


def longitude_to_rashi_number(longitude: float) -> int:
    """Convert longitude (0-360°) to rashi number (0-11)."""
    return int(longitude / 30)


def longitude_to_nakshatra(longitude: float) -> tuple:
    """
    Convert longitude to nakshatra name and pada.
    Returns (nakshatra_name, pada_number)
    """
    nakshatra_span = 360 / 27
    nakshatra_index = int(longitude / nakshatra_span)
    
    pada_span = nakshatra_span / 4
    position_in_nakshatra = longitude % nakshatra_span
    pada = int(position_in_nakshatra / pada_span) + 1
    
    return NAKSHATRA_NAMES[nakshatra_index], pada


def format_longitude_dms(longitude: float) -> str:
    """Format longitude as DrikPanchang does: "04° Meen 39' 57\"""" 
    rashi_index = int(longitude / 30)
    degree_in_sign = longitude % 30
    
    degrees = int(degree_in_sign)
    minutes_decimal = (degree_in_sign - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    return f"{degrees:02d}° {RASHI_ABBREV[rashi_index]} {minutes:02d}' {seconds:05.2f}\""


def calculate_whole_sign_houses(ascendant_longitude: float, planets: dict) -> dict:
    """
    Calculate house placements using WHOLE SIGN HOUSE SYSTEM (Rashi Chart).
    
    In whole sign houses:
    - Each house is exactly 30 degrees (one rashi/sign)
    - House 1 starts at the beginning of the Lagna rashi
    - Planets are placed based on their rashi, not degree-based cusps
    
    This is the system used by DrikPanchang for Rashi charts.
    
    Planets within each house are sorted in the standard order:
    1. Sur (Sun)
    2. Cha (Moon)
    3. Man (Mars)
    4. Bud (Mercury)
    5. Gur (Jupiter)
    6. Shu (Venus)
    7. Sha (Saturn)
    8. Rahu
    9. Ketu
    """
    
    # Find the Lagna rashi (sign)
    lagna_rashi = longitude_to_rashi_number(ascendant_longitude)
    
    # Initialize 12 houses
    chart = {i: [] for i in range(1, 13)}
    
    # Add Lagna to house 1
    chart[1].append("Lagna")
    
    # Planet abbreviations for chart display
    planet_abbrev = {
        "Sun": "Sur",
        "Moon": "Cha",
        "Mars": "Man",
        "Mercury": "Bud",
        "Jupiter": "Gur",
        "Venus": "Shu",
        "Saturn": "Sha",
        "Rahu": "Rahu",
        "Ketu": "Ketu",
    }
    
    # Define the standard planet order for sorting
    planet_order = ["Sur", "Cha", "Man", "Bud", "Gur", "Shu", "Sha", "Rahu", "Ketu"]
    
    # Place each planet in its house
    for planet_name, abbrev in planet_abbrev.items():
        planet_lon = planets[planet_name]
        planet_rashi = longitude_to_rashi_number(planet_lon)
        
        # Calculate house number using whole sign system
        # House = (planet_rashi - lagna_rashi) % 12 + 1
        house = ((planet_rashi - lagna_rashi) % 12) + 1
        
        chart[house].append(abbrev)
    
    # Sort planets within each house according to the standard order
    for house in range(1, 13):
        # Separate Lagna from planets
        has_lagna = "Lagna" in chart[house]
        planets_in_house = [p for p in chart[house] if p != "Lagna"]
        
        # Sort planets according to the standard order
        planets_in_house.sort(key=lambda p: planet_order.index(p) if p in planet_order else 999)
        
        # Reconstruct the house list with Lagna first (if present), then sorted planets
        chart[house] = []
        if has_lagna:
            chart[house].append("Lagna")
        chart[house].extend(planets_in_house)
    
    return chart


def generate_drik_gochara_chart(
    date_str: str,
    time_str: str,
    place_name: str,
    latitude: float,
    longitude: float,
    timezone_offset: float,
    ayanamsha: Literal["lahiri", "raman", "kp", "tropical"] = "lahiri",
    rahu_type: Literal["mean", "true"] = "mean",
) -> dict:
    """
    Generate Gochara (Rashi) chart exactly as DrikPanchang does.
    
    Uses whole sign house system (Rashi chart).
    """
    
    # Calculate planetary positions
    result = compute_drik_planetary_positions(
        date_str=date_str,
        time_str=time_str,
        latitude=latitude,
        longitude=longitude,
        tz_offset=timezone_offset,
        ayanamsha=ayanamsha,
        rahu_type=rahu_type,
    )
    
    planets = result["planets"]
    speeds = result["speeds"]
    right_ascensions = result["right_ascensions"]
    declinations = result["declinations"]
    latitudes = result["latitudes"]
    ascendant = result["ascendant"]
    jd_ut = result["julian_day"]
    
    # Calculate whole sign houses (Rashi chart)
    chart = calculate_whole_sign_houses(ascendant, planets)
    
    # Build planets table
    planets_table = []
    
    planet_list = [
        ("Lagna", None, ascendant, 0, None, None, None),
        ("Surya", "Sun", planets["Sun"], speeds["Sun"], right_ascensions.get("Sun"), declinations.get("Sun"), latitudes.get("Sun")),
        ("Chandra", "Moon", planets["Moon"], speeds["Moon"], right_ascensions.get("Moon"), declinations.get("Moon"), latitudes.get("Moon")),
        ("Mangal", "Mars", planets["Mars"], speeds["Mars"], right_ascensions.get("Mars"), declinations.get("Mars"), latitudes.get("Mars")),
        ("Budha", "Mercury", planets["Mercury"], speeds["Mercury"], right_ascensions.get("Mercury"), declinations.get("Mercury"), latitudes.get("Mercury")),
        ("Guru", "Jupiter", planets["Jupiter"], speeds["Jupiter"], right_ascensions.get("Jupiter"), declinations.get("Jupiter"), latitudes.get("Jupiter")),
        ("Shukra", "Venus", planets["Venus"], speeds["Venus"], right_ascensions.get("Venus"), declinations.get("Venus"), latitudes.get("Venus")),
        ("Shani", "Saturn", planets["Saturn"], speeds["Saturn"], right_ascensions.get("Saturn"), declinations.get("Saturn"), latitudes.get("Saturn")),
        ("Rahu", "Rahu", planets["Rahu"], speeds["Rahu"], right_ascensions.get("Rahu"), declinations.get("Rahu"), latitudes.get("Rahu")),
        ("Ketu", "Ketu", planets["Ketu"], speeds["Ketu"], right_ascensions.get("Ketu"), declinations.get("Ketu"), latitudes.get("Ketu")),
    ]
    
    for display_name, english_name, lon, speed, ra, dec, lat in planet_list:
        nakshatra, pada = longitude_to_nakshatra(lon)
        nakshatra_abbrev = NAKSHATRA_ABBREV.get(nakshatra, nakshatra)
        nakshatra_lord_sanskrit, nakshatra_lord_english = NAKSHATRA_LORDS.get(nakshatra, ("", ""))
        
        lon_formatted = format_longitude_dms(lon)
        
        planet_data = {
            "planet": display_name,
            "longitude": lon_formatted,
            "nakshatra": nakshatra_abbrev,
            "pada": pada,
            "nakshatra_lord": f"{nakshatra_lord_sanskrit}, {nakshatra_lord_english}",
            "full_degree": round(lon, 2),
            "speed_deg_per_day": round(speed, 2),
        }
        
        # Add RA, Dec, Latitude if available (not for Lagna)
        if ra is not None:
            planet_data["right_ascension"] = round(ra, 2)
        if dec is not None:
            planet_data["declination"] = round(dec, 2)
        if lat is not None:
            planet_data["latitude"] = round(lat, 2)
        
        planets_table.append(planet_data)
    
    return {
        "chart": chart,
        "planets_table": planets_table,
        "metadata": {
            "place": place_name,
            "date": date_str,
            "time": time_str,
            "latitude": latitude,
            "longitude": longitude,
            "tz_offset": timezone_offset,
            "ayanamsha": ayanamsha,
            "rahu_type": rahu_type,
            "julian_day": jd_ut,
        }
    }


def print_drik_chart(chart_data: dict):
    """Print Gochara chart in readable format."""
    chart = chart_data["chart"]
    planets_table = chart_data["planets_table"]
    metadata = chart_data["metadata"]
    
    print("=" * 100)
    print(f"DRIK GOCHARA (RASHI) CHART - {metadata['place']}")
    print(f"Date: {metadata['date']} | Time: {metadata['time']}")
    print("=" * 100)
    print()
    
    # Print chart
    print("RASHI CHART (Whole Sign Houses):")
    print("-" * 100)
    for house in range(1, 13):
        planets_in_house = ", ".join(chart[house]) if chart[house] else "—"
        print(f"House {house:2d}: {planets_in_house}")
    print()
    
    # Print planets table
    print("PLANETARY POSITIONS:")
    print("-" * 100)
    print(f"{'Planet':<12} {'Longitude':<22} {'Nakshatra':<18} {'Pada':>4} {'Full°':>10} {'Speed':>10}")
    print("-" * 100)
    
    for row in planets_table:
        print(f"{row['planet']:<12} {row['longitude']:<22} {row['nakshatra']:<18} "
              f"{row['pada']:>4} {row['full_degree']:>10.2f} {row['speed_deg_per_day']:>+10.2f}")
    
    # Print additional astronomical data if available
    has_extra_data = any('right_ascension' in row for row in planets_table)
    if has_extra_data:
        print()
        print("ADDITIONAL ASTRONOMICAL DATA:")
        print("-" * 100)
        print(f"{'Planet':<12} {'RA (°)':>10} {'Dec (°)':>10} {'Lat (°)':>10}")
        print("-" * 100)
        
        for row in planets_table:
            if 'right_ascension' in row:
                ra = row.get('right_ascension', 0)
                dec = row.get('declination', 0)
                lat = row.get('latitude', 0)
                print(f"{row['planet']:<12} {ra:>10.2f} {dec:>+10.2f} {lat:>+10.2f}")
    
    print()
    print(f"Julian Day: {metadata['julian_day']:.6f}")
    print(f"Ayanamsha: {metadata['ayanamsha'].title()} | Rahu: {metadata['rahu_type'].title()}")
    print("=" * 100)


# ─────────────────────────────────────────────────────────────────────────────
# DEMO / MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test with DrikPanchang example: Bhongir, India on March 19, 2026 at 17:56:47
    
    print("Testing with Bhongir, India - March 19, 2026 at 17:56:47 IST")
    print()
    
    chart_data = generate_drik_gochara_chart(
        date_str="19/03/2026",
        time_str="17:56:47",
        place_name="Bhongir, India",
        latitude=17.5167,
        longitude=78.8833,
        timezone_offset=5.5,
        ayanamsha="lahiri",
        rahu_type="mean",
    )
    
    print_drik_chart(chart_data)
    
    # Verify house placements match DrikPanchang screenshot
    print("\n\nVERIFICATION AGAINST DRIKPANCHANG SCREENSHOT:")
    print("-" * 100)
    print("Expected from screenshot:")
    print("  House 8: Sur, Sha, Cha, Shu")
    print("  House 7: Man, Bud, Rahu")
    print("  House 11: Gur")
    print("  House 1: Ketu")
    print()
    print("Calculated:")
    chart = chart_data["chart"]
    for house in [1, 7, 8, 11]:
        planets = ", ".join(chart[house]) if chart[house] else "—"
        print(f"  House {house}: {planets}")
