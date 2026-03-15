"""
Panchang calculations: Tithi, Karana, Yoga, Weekday
Based on Vedic astrology principles using Swiss Ephemeris
"""

import swisseph as swe
from datetime import datetime
import pytz

# Tithi names
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"
]

# Karana names (11 karanas, 7 repeat, 4 fixed)
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",  # Repeating (0-6)
    "Shakuni", "Chatushpada", "Naga", "Kimstughna"  # Fixed (7-10)
]

# Yoga names
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

# Weekday names
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def calculate_tithi(jd: float) -> dict:
    """
    Calculate Tithi (lunar day) from Julian Day
    Tithi is based on the angular difference between Sun and Moon
    Each tithi = 12 degrees difference
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    
    # Get Sun and Moon longitudes
    sun_data, _ = swe.calc_ut(jd, swe.SUN, flags)
    moon_data, _ = swe.calc_ut(jd, swe.MOON, flags)
    
    sun_lon = sun_data[0]
    moon_lon = moon_data[0]
    
    # Calculate angular difference
    diff = moon_lon - sun_lon
    if diff < 0:
        diff += 360
    
    # Each tithi is 12 degrees
    tithi_num = int(diff / 12)  # 0-29
    
    # Determine paksha and tithi name
    if tithi_num < 15:
        paksha = "Shukla Paksha"
        tithi_index = tithi_num
    else:
        paksha = "Krishna Paksha"
        tithi_index = tithi_num - 15
    
    # Special case for Purnima and Amavasya
    if tithi_num == 14:
        tithi_name = "Purnima"
    elif tithi_num == 29:
        tithi_name = "Amavasya"
    else:
        tithi_name = TITHI_NAMES[tithi_index]
    
    # Full tithi name with paksha
    if tithi_name in ["Purnima", "Amavasya"]:
        full_tithi = tithi_name
    else:
        full_tithi = f"{paksha} {tithi_name}"
    
    return {
        "tithi": full_tithi,
        "tithi_name": tithi_name,
        "paksha": paksha if tithi_name not in ["Purnima", "Amavasya"] else "",
        "tithi_number": tithi_num + 1,
        "angle_difference": round(diff, 2)
    }

def calculate_karana(jd: float) -> dict:
    """
    Calculate Karana (half of tithi)
    Each karana = 6 degrees difference between Sun and Moon
    60 karanas in a lunar month (7 repeat 8 times, 4 fixed at end)
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    
    sun_data, _ = swe.calc_ut(jd, swe.SUN, flags)
    moon_data, _ = swe.calc_ut(jd, swe.MOON, flags)
    
    sun_lon = sun_data[0]
    moon_lon = moon_data[0]
    
    diff = moon_lon - sun_lon
    if diff < 0:
        diff += 360
    
    # Each karana is 6 degrees (half tithi)
    karana_num = int(diff / 6)  # 0-59
    
    # First karana (0) is Kimstughna (fixed)
    # Karanas 1-56 are the 7 repeating karanas (8 times each)
    # Karanas 57-60 are the 4 fixed karanas
    if karana_num == 0:
        karana_index = 10  # Kimstughna
    elif karana_num >= 57:
        karana_index = 7 + (karana_num - 57)  # Shakuni, Chatushpada, Naga, Kimstughna
    else:
        karana_index = (karana_num - 1) % 7  # Repeating karanas
    
    karana_name = KARANA_NAMES[karana_index]
    
    return {
        "karana": karana_name,
        "karana_number": karana_num + 1
    }

def calculate_yoga(jd: float) -> dict:
    """
    Calculate Yoga (sum of Sun and Moon longitudes)
    Each yoga = 13.333... degrees (360/27)
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    
    sun_data, _ = swe.calc_ut(jd, swe.SUN, flags)
    moon_data, _ = swe.calc_ut(jd, swe.MOON, flags)
    
    sun_lon = sun_data[0]
    moon_lon = moon_data[0]
    
    # Yoga is based on sum of Sun and Moon longitudes
    yoga_sum = (sun_lon + moon_lon) % 360
    
    # Each yoga is 13.333... degrees (360/27)
    yoga_num = int(yoga_sum / (360 / 27))  # 0-26
    
    yoga_name = YOGA_NAMES[yoga_num]
    
    return {
        "yoga": yoga_name,
        "yoga_number": yoga_num + 1,
        "yoga_sum": round(yoga_sum, 2)
    }

def calculate_weekday(year: int, month: int, day: int) -> dict:
    """
    Calculate weekday from date
    """
    date_obj = datetime(year, month, day)
    weekday_num = date_obj.weekday()  # 0=Monday, 6=Sunday
    weekday_name = WEEKDAY_NAMES[weekday_num]
    
    return {
        "weekday": weekday_name,
        "weekday_number": weekday_num + 1
    }

def calculate_vikram_samvat(year: int, month: int, day: int) -> str:
    """
    Calculate Vikram Samvat date (approximate)
    Vikram Samvat is 57 years ahead of Gregorian calendar
    """
    vs_year = year + 57
    
    # Month names in Vikram Samvat
    vs_months = [
        "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha",
        "Shravana", "Bhadrapada", "Ashvina", "Kartika",
        "Margashirsha", "Pausha", "Magha", "Phalguna"
    ]
    
    # Approximate mapping (Gregorian to Hindu lunar month)
    # This is simplified; actual calculation requires lunar calendar
    month_map = {
        1: "Magha", 2: "Phalguna", 3: "Chaitra", 4: "Vaishakha",
        5: "Jyeshtha", 6: "Ashadha", 7: "Shravana", 8: "Bhadrapada",
        9: "Ashvina", 10: "Kartika", 11: "Margashirsha", 12: "Pausha"
    }
    
    vs_month = month_map.get(month, "Chaitra")
    
    return f"{vs_month} {day}, {vs_year}"

def get_complete_panchang(jd: float, year: int, month: int, day: int) -> dict:
    """
    Get complete panchang details
    """
    tithi_data = calculate_tithi(jd)
    karana_data = calculate_karana(jd)
    yoga_data = calculate_yoga(jd)
    weekday_data = calculate_weekday(year, month, day)
    vikram_samvat = calculate_vikram_samvat(year, month, day)
    
    return {
        **tithi_data,
        **karana_data,
        **yoga_data,
        **weekday_data,
        "vikram_samvat": vikram_samvat
    }
