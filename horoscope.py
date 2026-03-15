"""
Comprehensive Horoscope API
Returns complete birth chart with predictions for:
- Weekday, Nakshatra, Rasi, Tithi, Karana, Yoga
- Birth details and metadata
"""

from geocode import geocode_place
from ephemeris import local_to_julian_day, get_moon_longitude
from nakshatra import calculate_nakshatra, NAKSHATRAS
from panchang import get_complete_panchang
from horoscope_data import (
    WEEKDAY_PREDICTIONS, RASI_PREDICTIONS, NAKSHATRA_PREDICTIONS,
    TITHI_PREDICTIONS, KARANA_PREDICTIONS, YOGA_PREDICTIONS
)
import swisseph as swe
from datetime import datetime
import pytz

def get_sunrise_sunset(jd: float, lat: float, lon: float) -> dict:
    """Calculate sunrise and sunset times"""
    try:
        # Calculate sunrise
        sunrise_jd = swe.rise_trans(
            jd - 1, swe.SUN, lon, lat, 0, 0,
            swe.CALC_RISE | swe.BIT_DISC_CENTER
        )[1][0]
        
        # Calculate sunset
        sunset_jd = swe.rise_trans(
            jd - 1, swe.SUN, lon, lat, 0, 0,
            swe.CALC_SET | swe.BIT_DISC_CENTER
        )[1][0]
        
        # Convert JD to time
        sunrise_time = jd_to_time(sunrise_jd)
        sunset_time = jd_to_time(sunset_jd)
        
        return {
            "sunrise": sunrise_time,
            "sunset": sunset_time
        }
    except:
        return {
            "sunrise": "06:00 AM",
            "sunset": "06:00 PM"
        }

def jd_to_time(jd: float) -> str:
    """Convert Julian Day to time string"""
    year, month, day, hour = swe.revjul(jd)
    hour_int = int(hour)
    minute = int((hour - hour_int) * 60)
    
    # Convert to 12-hour format
    if hour_int == 0:
        hour_12 = 12
        ampm = "AM"
    elif hour_int < 12:
        hour_12 = hour_int
        ampm = "AM"
    elif hour_int == 12:
        hour_12 = 12
        ampm = "PM"
    else:
        hour_12 = hour_int - 12
        ampm = "PM"
    
    return f"{hour_12:02d}:{minute:02d} {ampm}"

def get_ascendant(jd: float, lat: float, lon: float) -> dict:
    """Calculate Ascendant (Lagna)"""
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P')  # 'P' for Placidus
        
        # Ascendant is the first value in ascmc
        asc_lon = ascmc[0]
        
        # Calculate rasi
        rasi_num = int(asc_lon / 30)
        rasi_names = [
            "Mesha", "Vrishabha", "Mithuna", "Karkataka",
            "Simha", "Kanya", "Tula", "Vrishchika",
            "Dhanu", "Makara", "Kumbha", "Meena"
        ]
        
        # Ascendant lord
        lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        
        return {
            "ascendant": rasi_names[rasi_num],
            "ascendant_lord": lords[rasi_num],
            "ascendant_degree": round(asc_lon, 2)
        }
    except:
        return {
            "ascendant": "Unknown",
            "ascendant_lord": "Unknown",
            "ascendant_degree": 0
        }

def calculate_comprehensive_horoscope(
    name: str,
    gender: str,
    date: str,
    hour: int,
    minute: int,
    ampm: str,
    place: str,
    lat: float = None,
    lon: float = None,
    timezone: str = None,
) -> dict:
    """
    Calculate comprehensive horoscope with all predictions.
    Accepts pre-resolved lat/lon/timezone (from /api/places) or falls back to geocoding.
    """
    # Step 1: Use provided geo or geocode
    if lat is not None and lon is not None and timezone:
        geo = {"lat": lat, "lon": lon, "timezone": timezone, "display_name": place}
    else:
        geo = geocode_place(place)

    # Step 2: Parse date
    year, month, day = map(int, date.split("-"))

    # Step 3: Convert to 24h
    hour24 = hour
    if ampm == "PM" and hour != 12:
        hour24 += 12
    if ampm == "AM" and hour == 12:
        hour24 = 0

    # Step 4: Julian Day
    jd = local_to_julian_day(year, month, day, hour24, minute, geo["timezone"])

    # Step 5: Moon longitude and nakshatra
    moon_lon, moon_speed = get_moon_longitude(jd)
    nakshatra_data = calculate_nakshatra(moon_lon, moon_speed)

    # Step 6: Panchang (Tithi, Karana, Yoga, Weekday)
    panchang_data = get_complete_panchang(jd, year, month, day)

    # Step 7: Ascendant
    ascendant_data = get_ascendant(jd, geo["lat"], geo["lon"])
    
    # Step 8: Sunrise/Sunset
    sun_times = get_sunrise_sunset(jd, geo["lat"], geo["lon"])
    
    # Step 9: Get predictions
    weekday_pred = WEEKDAY_PREDICTIONS.get(panchang_data["weekday"], {})
    rasi_pred = RASI_PREDICTIONS.get(nakshatra_data["chandra_rasi"], {})
    nakshatra_pred = NAKSHATRA_PREDICTIONS.get(nakshatra_data["nakshatra"], "")
    tithi_pred = TITHI_PREDICTIONS.get(panchang_data["tithi"], "")
    karana_pred = KARANA_PREDICTIONS.get(panchang_data["karana"], "")
    yoga_pred = YOGA_PREDICTIONS.get(panchang_data["yoga"], "")
    
    # Step 10: Get nakshatra details
    nakshatra_index = None
    for i, nk in enumerate(NAKSHATRAS):
        if nk["name"] == nakshatra_data["nakshatra"]:
            nakshatra_index = i
            break
    
    nakshatra_details = NAKSHATRAS[nakshatra_index] if nakshatra_index is not None else {}
    
    # Step 11: Determine Ganam, Yoni, Gothram, Bhutham
    ganam = nakshatra_details.get("gana", "Unknown")
    
    # Yoni mapping (simplified)
    yoni_map = {
        "Horse": "Male", "Elephant": "Female", "Sheep": "Male", "Cobra": "Male",
        "Female Serpent": "Female", "Dog": "Male", "Cat": "Female", "Ram": "Male",
        "Rat": "Male", "Female Rat": "Female", "Bull": "Male", "Buffalo": "Male",
        "Female Tiger": "Female", "Tiger": "Male", "Deer": "Male", "Monkey": "Male",
        "Mongoose": "Male", "Lion": "Male", "Cow": "Female"
    }
    yoni = yoni_map.get(nakshatra_details.get("animal", ""), "Male")
    
    # Gothram (simplified - using deity name)
    deity = nakshatra_details.get("deity", "Unknown")
    gothram_map = {
        "Ashwini Kumaras": "Vasishtha", "Yama": "Bharadvaja", "Agni": "Gautama",
        "Brahma": "Atri", "Soma": "Kashyapa", "Rudra": "Vishwamitra",
        "Aditi": "Jamadagni", "Brihaspati": "Vasishtha", "Nagas": "Bharadvaja",
        "Pitris": "Gautama", "Bhaga": "Atri", "Aryaman": "Kashyapa",
        "Savitar": "Vishwamitra", "Vishwakarma": "Jamadagni", "Vayu": "Vasishtha",
        "Indra-Agni": "Bharadvaja", "Mitra": "Gautama", "Indra": "Atri",
        "Nirriti": "Kashyapa", "Apas": "Vishwamitra", "Vishvedevas": "Jamadagni",
        "Vishnu": "Vasishtha", "Ashta Vasus": "Bharadvaja", "Varuna": "Gautama",
        "Aja Ekapada": "Atri", "Ahir Budhanya": "Kashyapa", "Pushan": "Vishwamitra"
    }
    gothram = gothram_map.get(deity, "Vasishtha")
    
    # Bhutham (element) mapping
    bhutham_map = {
        "Fire": "Fire", "Earth": "Earth", "Air": "Air", "Water": "Water"
    }
    bhutham = bhutham_map.get(rasi_pred.get("element", "Fire"), "Fire")
    
    # Step 12: Build response
    result = {
        "predictions": {
            "weekday": {
                "title": f"Weekday: {panchang_data['weekday']}",
                "description": weekday_pred.get("description", ""),
                "ruling_planet": weekday_pred.get("ruling_planet", "")
            },
            "nakshatra": {
                "title": f"Nakshatra: {nakshatra_data['nakshatra']}",
                "description": nakshatra_pred
            },
            "rasi": {
                "title": f"Rasi: {nakshatra_data['chandra_rasi']}",
                "description": rasi_pred.get("description", "")
            },
            "tithi": {
                "title": f"Tithi: {panchang_data['tithi']}",
                "description": tithi_pred
            },
            "karana": {
                "title": f"Karana: {panchang_data['karana']}",
                "description": karana_pred
            },
            "yoga": {
                "title": f"Yoga: {panchang_data['yoga']}",
                "description": yoga_pred
            }
        },
        "birth_details": {
            "nakshatra": f"{nakshatra_data['nakshatra']} {nakshatra_data['pada_label']} Pada",
            "weekday": panchang_data["weekday"],
            "tithi": panchang_data["tithi"],
            "yoga": panchang_data["yoga"],
            "karana": panchang_data["karana"],
            "vikram_samvat": panchang_data["vikram_samvat"],
            "god": nakshatra_details.get("deity", "Unknown"),
            "animal_sign": nakshatra_details.get("animal", "Unknown"),
            "rasi": nakshatra_data["chandra_rasi"],
            "rasi_lord": rasi_pred.get("lord", "Unknown"),
            "ascendant": ascendant_data["ascendant"],
            "ascendant_lord": ascendant_data["ascendant_lord"],
            "ganam": ganam,
            "yoni": yoni,
            "gothram": gothram,
            "bhutham": bhutham,
            "sunrise": sun_times["sunrise"],
            "sunset": sun_times["sunset"]
        },
        "input_details": {
            "name": name,
            "gender": gender,
            "date_of_birth": date,
            "time_of_birth": f"{hour}:{minute:02d} {ampm}",
            "place_of_birth": place,
            "latitude": geo["lat"],
            "longitude": geo["lon"],
            "timezone": geo["timezone"]
        },
        "technical_details": {
            "julian_day": round(jd, 6),
            "moon_longitude": nakshatra_data["moon_longitude"],
            "moon_speed": nakshatra_data.get("moon_speed_deg_per_day", 0),
            "ascendant_degree": ascendant_data["ascendant_degree"]
        }
    }
    
    return result
