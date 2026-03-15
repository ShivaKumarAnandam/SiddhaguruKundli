import swisseph as swe
import pytz
from datetime import datetime

# Use Moshier ephemeris - built into pyswisseph, no data files needed
# Accuracy: ~1 arc-second, more than enough (nakshatras are 13.3° wide)
swe.set_ephe_path('')

def local_to_julian_day(year: int, month: int, day: int,
                         hour: int, minute: int, timezone_str: str) -> float:
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime(year, month, day, hour, minute, 0))
    utc_dt = local_dt.astimezone(pytz.utc)

    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0
    )
    return jd

def get_moon_longitude(julian_day: float) -> float:
    # Set Lahiri ayanamsa (standard for Vedic / Indian astrology)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # FLG_MOSEPH = use built-in Moshier ephemeris (no files needed)
    # FLG_SIDEREAL = sidereal coordinates (Vedic), not tropical (Western)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    result, ret_flag = swe.calc_ut(julian_day, swe.MOON, flags)

    moon_lon = result[0]  # ecliptic longitude in degrees 0–360
    moon_speed = result[3]  # degrees/day (positive = direct motion)

    return moon_lon, moon_speed


def get_all_planets(julian_day: float) -> dict:
    """
    Calculate positions of all planets for Gochara chart.
    Returns dictionary with planet positions in sidereal zodiac.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    planets = {
        'sun': swe.SUN,
        'moon': swe.MOON,
        'mars': swe.MARS,
        'mercury': swe.MERCURY,
        'jupiter': swe.JUPITER,
        'venus': swe.VENUS,
        'saturn': swe.SATURN,
        'rahu': swe.TRUE_NODE,  # North Node (Rahu)
    }
    
    positions = {}
    
    for planet_name, planet_id in planets.items():
        result, ret_flag = swe.calc_ut(julian_day, planet_id, flags)
        longitude = result[0]  # 0-360 degrees
        positions[planet_name] = longitude
    
    # Ketu is always 180 degrees opposite to Rahu
    positions['ketu'] = (positions['rahu'] + 180) % 360
    
    return positions


def longitude_to_sign(longitude: float) -> str:
    """Convert longitude (0-360) to zodiac sign name."""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude / 30)
    return signs[sign_index]


def longitude_to_nakshatra(longitude: float) -> str:
    """Convert longitude (0-360) to nakshatra name."""
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    nakshatra_index = int(longitude / (360 / 27))
    return nakshatras[nakshatra_index]


def calculate_house_from_ascendant(planet_longitude: float, ascendant_longitude: float) -> int:
    """Calculate which house a planet is in, relative to ascendant."""
    # House = ((planet_longitude - ascendant_longitude) / 30) + 1
    # Normalize to 0-360 range
    diff = (planet_longitude - ascendant_longitude) % 360
    house = int(diff / 30) + 1
    return house

