"""
gochara_south_indian.py
=======================
Gochara (Transit) Chart using Swiss Ephemeris for accurate calculations.
Generates South Indian style Rashi chart with complete astronomical data.
Matches DrikPanchang.com format exactly.
"""

from ephemeris import (
    local_to_julian_day,
    longitude_to_sign,
)
from datetime import datetime
import pytz
import swisseph as swe


# Planet abbreviations for chart display
PLANET_ABBREV = {
    "Sun": "Sur",
    "Moon": "Cha",
    "Mars": "Man",
    "Mercury": "Bud",
    "Jupiter": "Gur",
    "Venus": "Shu",
    "Saturn": "Sha",
    "Uranus": "Arun",
    "Neptune": "Varun",
    "Pluto": "Yam",
    "Rahu": "Rahu",
    "Ketu": "Ketu",
}

# Standard planet order for sorting within houses
PLANET_ORDER = ["Sur", "Cha", "Man", "Bud", "Gur", "Shu", "Sha", "Rahu", "Ketu"]

# Rashi names
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

# Nakshatra data
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


def longitude_to_nakshatra(longitude: float) -> tuple:
    """Convert longitude to nakshatra name and pada."""
    nakshatra_span = 360 / 27
    nakshatra_index = int(longitude / nakshatra_span)
    
    pada_span = nakshatra_span / 4
    position_in_nakshatra = longitude % nakshatra_span
    pada = int(position_in_nakshatra / pada_span) + 1
    
    return NAKSHATRA_NAMES[nakshatra_index], pada


def format_longitude_dms(longitude: float) -> str:
    """Format longitude as DrikPanchang does."""
    rashi_index = int(longitude / 30)
    degree_in_sign = longitude % 30
    
    degrees = int(degree_in_sign)
    minutes_decimal = (degree_in_sign - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    return f"{degrees:02d}° {RASHI_ABBREV[rashi_index]} {minutes:02d}' {seconds:05.2f}\""

import functools

@functools.lru_cache(maxsize=128)
def calculate_gochara_chart(
    date: str,
    time: str,
    place: str,
    latitude: float,
    longitude: float,
    timezone: str,
) -> dict:
    """
    Calculate Gochara (Transit) chart with complete astronomical data.
    Matches DrikPanchang.com format exactly.
    
    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM:SS or HH:MM format
        place: Place name
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        timezone: Timezone name (e.g., "Asia/Kolkata")
    
    Returns:
        Dictionary with chart, planets_table, and metadata
    """
    
    # Parse date and time
    year, month, day = map(int, date.split("-"))
    
    # Parse time (handle both HH:MM:SS and HH:MM formats)
    time_parts = time.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    second = int(time_parts[2]) if len(time_parts) > 2 else 0
    
    # Calculate Julian Day using UTC conversion
    tz = pytz.timezone(timezone)
    local_dt = tz.localize(datetime(year, month, day, hour, minute, second))
    utc_dt = local_dt.astimezone(pytz.utc)
    
    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    )
    
    # Set sidereal mode (Lahiri ayanamsha)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Calculation flags - use SWIEPH for consistency
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    flags_equatorial = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_EQUATORIAL | swe.FLG_SPEED
    
    # Calculate Ascendant (Lagna)
    houses, ascmc = swe.houses_ex(jd, latitude, longitude, b'P', flags)
    ascendant_longitude = ascmc[0]
    
    # Get ARMC (Ascendant's Right Ascension on Meridian Circle)
    # ascmc[2] contains ARMC
    armc = ascmc[2]
    
    # Calculate Lagna's RA and Dec
    # For Lagna, we use the ARMC and calculate declination from latitude
    # The RA of the Ascendant is related to ARMC and local sidereal time
    lagna_ra = armc
    
    # Calculate declination using the formula: sin(dec) = sin(lat) * sin(obliquity)
    # But for Ascendant, we need to use the ecliptic coordinates
    ecl_nut_result, ret_flag = swe.calc_ut(jd, swe.ECL_NUT, 0)
    obliquity = ecl_nut_result[0]
    
    # Convert Lagna ecliptic to equatorial
    lagna_equatorial = swe.cotrans([ascendant_longitude, 0.0, 1.0], -obliquity)
    lagna_dec = lagna_equatorial[1]
    
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
    latitudes = {}
    right_ascensions = {}
    declinations = {}
    
    for planet_name, planet_id in planet_ids.items():
        # Ecliptic coordinates
        result, ret_flag = swe.calc_ut(jd, planet_id, flags)
        planets[planet_name] = result[0]
        latitudes[planet_name] = result[1]
        speeds[planet_name] = result[3]
        
        # Equatorial coordinates
        result_eq, ret_flag_eq = swe.calc_ut(jd, planet_id, flags_equatorial)
        right_ascensions[planet_name] = result_eq[0]
        declinations[planet_name] = result_eq[1]
    
    # Calculate Mean Rahu/Ketu
    result, ret_flag = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    planets["Rahu"] = result[0]
    latitudes["Rahu"] = result[1]
    speeds["Rahu"] = result[3]
    
    result_eq, ret_flag_eq = swe.calc_ut(jd, swe.MEAN_NODE, flags_equatorial)
    right_ascensions["Rahu"] = result_eq[0]
    declinations["Rahu"] = result_eq[1]
    
    planets["Ketu"] = (planets["Rahu"] + 180) % 360
    latitudes["Ketu"] = -latitudes["Rahu"]
    speeds["Ketu"] = speeds["Rahu"]
    right_ascensions["Ketu"] = (right_ascensions["Rahu"] + 180) % 360
    declinations["Ketu"] = -declinations["Rahu"]
    
    # Calculate True (Spashth) Rahu/Ketu
    result_true, ret_flag_true = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    spashth_rahu_lon = result_true[0]
    spashth_ketu_lon = (spashth_rahu_lon + 180) % 360
    
    result_true_eq, ret_flag_true_eq = swe.calc_ut(jd, swe.TRUE_NODE, flags_equatorial)
    spashth_rahu_ra = result_true_eq[0]
    spashth_rahu_dec = result_true_eq[1]
    spashth_ketu_ra = (spashth_rahu_ra + 180) % 360
    spashth_ketu_dec = -spashth_rahu_dec
    
    # Build South Indian chart (12 houses) - only main planets
    chart = {i: [] for i in range(1, 13)}
    
    # Add Lagna to house 1
    chart[1].append("Lagna")
    
    # Calculate Lagna rashi for house placement
    lagna_rashi = int(ascendant_longitude / 30)
    
    # Place main planets (exclude outer planets from chart)
    main_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    
    for planet_name in main_planets:
        planet_lon = planets[planet_name]
        planet_rashi = int(planet_lon / 30)
        house = ((planet_rashi - lagna_rashi) % 12) + 1
        
        abbrev = PLANET_ABBREV[planet_name]
        chart[house].append(abbrev)
    
    # Sort planets within each house
    for house in range(1, 13):
        has_lagna = "Lagna" in chart[house]
        planets_in_house = [p for p in chart[house] if p != "Lagna"]
        planets_in_house.sort(key=lambda p: PLANET_ORDER.index(p) if p in PLANET_ORDER else 999)
        
        chart[house] = []
        if has_lagna:
            chart[house].append("Lagna")
        chart[house].extend(planets_in_house)
    
    # Add lagna_rashi to metadata for UI to know where to start the layout
    chart["lagna_rashi"] = lagna_rashi
    
    # Build planets table with all details
    planets_table = []
    
    # Helper function to get sub-lord using Vimshottari sub-sub period
    def get_sub_lord(longitude):
        """
        Calculate sub-lord (sub-sub period lord) using Vimshottari dasha system.
        This divides each nakshatra pada into 9 sub-divisions.
        """
        # Vimshottari dasha lords in order
        dasha_lords = ["Ketu", "Shukra", "Surya", "Chandra", "Mangal", "Rahu", "Guru", "Shani", "Budha"]
        
        # Each nakshatra is 13°20' (800 minutes)
        # Each pada is 3°20' (200 minutes)
        # Sub-lord divisions within pada follow Vimshottari proportions
        
        nakshatra_span = 360 / 27  # 13.333...°
        nakshatra_index = int(longitude / nakshatra_span)
        position_in_nakshatra = longitude % nakshatra_span
        
        # Get nakshatra lord
        nakshatra_lord_idx = nakshatra_index % 9
        
        # Calculate pada (1-4)
        pada_span = nakshatra_span / 4
        pada = int(position_in_nakshatra / pada_span) + 1
        position_in_pada = position_in_nakshatra % pada_span
        
        # Vimshottari proportions (in years, but we use as ratios)
        dasha_years = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        total_years = sum(dasha_years)
        
        # Calculate cumulative proportions
        cumulative = 0
        for i, years in enumerate(dasha_years):
            proportion = years / total_years
            cumulative += proportion
            
            # Check if position falls in this sub-division
            if position_in_pada / pada_span <= cumulative:
                sub_lord_idx = (nakshatra_lord_idx + i) % 9
                return dasha_lords[sub_lord_idx]
        
        # Fallback (should not reach here)
        return dasha_lords[nakshatra_lord_idx]
    
    # Add all planets to table
    planet_list = [
        ("Lagna", None, ascendant_longitude, 0, 0, lagna_ra, lagna_dec),
        ("Surya", "Sun", planets["Sun"], speeds["Sun"], latitudes["Sun"], right_ascensions["Sun"], declinations["Sun"]),
        ("Chandra", "Moon", planets["Moon"], speeds["Moon"], latitudes["Moon"], right_ascensions["Moon"], declinations["Moon"]),
        ("Mangal", "Mars", planets["Mars"], speeds["Mars"], latitudes["Mars"], right_ascensions["Mars"], declinations["Mars"]),
        ("Budha", "Mercury", planets["Mercury"], speeds["Mercury"], latitudes["Mercury"], right_ascensions["Mercury"], declinations["Mercury"]),
        ("Guru", "Jupiter", planets["Jupiter"], speeds["Jupiter"], latitudes["Jupiter"], right_ascensions["Jupiter"], declinations["Jupiter"]),
        ("Shukra", "Venus", planets["Venus"], speeds["Venus"], latitudes["Venus"], right_ascensions["Venus"], declinations["Venus"]),
        ("Shani", "Saturn", planets["Saturn"], speeds["Saturn"], latitudes["Saturn"], right_ascensions["Saturn"], declinations["Saturn"]),
        ("Arun", "Uranus", planets["Uranus"], speeds["Uranus"], latitudes["Uranus"], right_ascensions["Uranus"], declinations["Uranus"]),
        ("Varun", "Neptune", planets["Neptune"], speeds["Neptune"], latitudes["Neptune"], right_ascensions["Neptune"], declinations["Neptune"]),
        ("Yam", "Pluto", planets["Pluto"], speeds["Pluto"], latitudes["Pluto"], right_ascensions["Pluto"], declinations["Pluto"]),
        ("Rahu", "Rahu", planets["Rahu"], speeds["Rahu"], latitudes["Rahu"], right_ascensions["Rahu"], declinations["Rahu"]),
        ("Ketu", "Ketu", planets["Ketu"], speeds["Ketu"], latitudes["Ketu"], right_ascensions["Ketu"], declinations["Ketu"]),
        ("Spashth Rahu", None, spashth_rahu_lon, speeds["Rahu"], latitudes["Rahu"], spashth_rahu_ra, spashth_rahu_dec),
        ("Spashth Ketu", None, spashth_ketu_lon, speeds["Ketu"], latitudes["Ketu"], spashth_ketu_ra, spashth_ketu_dec),
    ]
    
    for display_name, english_name, lon, speed, lat, ra, dec in planet_list:
        nakshatra, pada = longitude_to_nakshatra(lon)
        nakshatra_abbrev = NAKSHATRA_ABBREV.get(nakshatra, nakshatra)
        nakshatra_lord_sanskrit, nakshatra_lord_english = NAKSHATRA_LORDS.get(nakshatra, ("", ""))
        
        # Get sub-lord using Vimshottari system
        sub_lord = get_sub_lord(lon)
        
        lon_formatted = format_longitude_dms(lon)
        
        # Calculate house (only for main planets, not outer planets or spashth nodes)
        if english_name in main_planets or display_name == "Lagna":
            planet_rashi = int(lon / 30)
            house = ((planet_rashi - lagna_rashi) % 12) + 1
        else:
            house = None
        
        planet_data = {
            "planet": display_name,
            "longitude": lon_formatted,
            "nakshatra": nakshatra_abbrev,
            "pada": pada,
            "nakshatra_lord": f"{nakshatra_lord_sanskrit}, {sub_lord}",
            "full_degree": round(lon, 2),
            "latitude": round(lat, 2) if lat != 0 else 0.0,
            "speed_deg_per_day": round(speed, 2),
            "right_ascension": round(ra, 2) if ra is not None else 0.0,
            "declination": round(dec, 2) if dec is not None else 0.0,
        }
        
        if house is not None:
            planet_data["house"] = house
        
        planets_table.append(planet_data)
    
    # Metadata
    metadata = {
        "place": place,
        "date": date,
        "time": time,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "julian_day": jd,
        "calculation_type": "Gochara (Transit Chart)",
        "chart_style": "South Indian (Whole Sign Houses)",
    }
    
    return {
        "chart": chart,
        "planets_table": planets_table,
        "metadata": metadata,
    }


def print_gochara_chart(chart_data: dict):
    """Print Gochara chart in readable format."""
    chart = chart_data["chart"]
    planets_table = chart_data["planets_table"]
    metadata = chart_data["metadata"]
    
    print("=" * 100)
    print(f"GOCHARA (TRANSIT) CHART - {metadata['place']}")
    print(f"Date: {metadata['date']} | Time: {metadata['time']}")
    print("=" * 100)
    print()
    
    # Print chart
    print("SOUTH INDIAN RASHI CHART (Whole Sign Houses):")
    print("-" * 100)
    for house in range(1, 13):
        planets_in_house = ", ".join(chart[house]) if chart[house] else "—"
        print(f"House {house:2d}: {planets_in_house}")
    print()
    
    # Print planets table
    print("PLANETARY POSITIONS:")
    print("-" * 100)
    print(f"{'Planet':<12} {'Longitude':<25} {'Sign':<15} {'Nakshatra':<15} {'House':>6} {'Full°':>10} {'Speed':>10}")
    print("-" * 100)
    
    for row in planets_table:
        print(f"{row['planet']:<12} {row['longitude']:<25} {row['sign']:<15} "
              f"{row['nakshatra']:<15} {row['house']:>6} {row['full_degree']:>10.2f} {row['speed_deg_per_day']:>+10.2f}")
    
    print()
    print(f"Julian Day: {metadata['julian_day']:.6f}")
    print(f"Chart Style: {metadata['chart_style']}")
    print("=" * 100)


# Demo / Test
if __name__ == "__main__":
    print("Testing Gochara Chart - March 21, 2026 at 11:21:10 IST")
    print()
    
    chart_data = calculate_gochara_chart(
        date="2026-03-21",
        time="11:21:10",
        place="Bhongir, India",
        latitude=17.51083,
        longitude=78.88889,
        timezone="Asia/Kolkata",
    )
    
    print_gochara_chart(chart_data)
