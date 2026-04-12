import asyncio
from datetime import datetime, timedelta
from ephemeris import local_to_julian_day, get_moon_longitude
from nakshatra import calculate_nakshatra
from panchang import get_complete_panchang
from horoscope_data import (
    WEEKDAY_PREDICTIONS, RASI_PREDICTIONS, NAKSHATRA_PREDICTIONS,
    TITHI_PREDICTIONS, KARANA_PREDICTIONS, YOGA_PREDICTIONS,
    MOON_TRANSIT_PREDICTIONS
)


def _day_summary(jd: float, year: int, month: int, day: int, janma_rasi_idx: int = None) -> dict:
    """Build panchang + predictions for a single day."""
    moon_lon, moon_speed = get_moon_longitude(jd)
    nk = calculate_nakshatra(moon_lon, moon_speed)
    panchang = get_complete_panchang(jd, year, month, day)

    # Get standard panchang predictions
    weekday_pred = WEEKDAY_PREDICTIONS.get(panchang["weekday"], {})
    nakshatra_pred = NAKSHATRA_PREDICTIONS.get(nk["nakshatra"], "")
    rasi_pred = RASI_PREDICTIONS.get(nk["chandra_rasi"], {})
    tithi_pred = TITHI_PREDICTIONS.get(panchang["tithi"], "")
    karana_pred = KARANA_PREDICTIONS.get(panchang["karana"], "")
    yoga_pred = YOGA_PREDICTIONS.get(panchang["yoga"], "")

    # Calculate Transit (Gochara) Moon Prediction relative to Janma Rasi
    transit_prediction = ""
    transit_house = None
    if janma_rasi_idx is not None:
        transit_rasi_idx = int(moon_lon / 30) % 12
        transit_house = (transit_rasi_idx - janma_rasi_idx + 12) % 12 + 1
        transit_prediction = MOON_TRANSIT_PREDICTIONS.get(transit_house, "")

    return {
        "date": f"{year}-{month:02d}-{day:02d}",
        "weekday": panchang["weekday"],
        "nakshatra": nk["nakshatra"],
        "nakshatra_pada": nk["pada_label"],
        "rasi": nk["chandra_rasi"],
        "tithi": panchang["tithi"],
        "karana": panchang["karana"],
        "yoga": panchang["yoga"],
        "transit_house": transit_house,
        "predictions": {
            "transit": {
                "title": f"Moon in {transit_house}{'st' if transit_house==1 else 'nd' if transit_house==2 else 'rd' if transit_house==3 else 'th'} House from Birth Rasi",
                "description": transit_prediction
            },
            "weekday": {
                "title": f"Weekday: {panchang['weekday']}",
                "description": weekday_pred.get("description", ""),
                "ruling_planet": weekday_pred.get("ruling_planet", ""),
            },
            "nakshatra": {
                "title": f"Nakshatra: {nk['nakshatra']}",
                "description": nakshatra_pred,
            },
            "tithi": {
                "title": f"Tithi: {panchang['tithi']}",
                "description": tithi_pred,
            },
            "karana": {
                "title": f"Karana: {panchang['karana']}",
                "description": karana_pred,
            },
            "yoga": {
                "title": f"Yoga: {panchang['yoga']}",
                "description": yoga_pred,
            },
        },
    }


async def calculate_weekly_horoscope(
    name: str,
    gender: str,
    birth_date: str,
    start_date: str,
    hour: int,
    minute: int,
    ampm: str,
    place: str,
    lat: float,
    lon: float,
    timezone: str,
) -> dict:
    """
    Return predictions for 7 days starting from *start_date*.
    Calculates all days in parallel using asyncio threads for maximum speed.
    """
    # 1. Calculate Janma (Birth) Rasi and Nakshatra
    by, bm, bd = map(int, birth_date.split("-"))
    hour24 = hour
    if ampm == "PM" and hour != 12: hour24 += 12
    if ampm == "AM" and hour == 12: hour24 = 0

    # Calculate Janma details (shared across all days)
    jd_birth = local_to_julian_day(by, bm, bd, hour24, minute, timezone)
    moon_lon_birth, _ = get_moon_longitude(jd_birth)
    janma_details = calculate_nakshatra(moon_lon_birth)
    janma_rasi_idx = int(moon_lon_birth / 30) % 12

    # 2. Prepare parallel tasks
    sy, sm, sd = map(int, start_date.split("-"))
    start_dt = datetime(sy, sm, sd)
    
    tasks = []
    for offset in range(7):
        dt = start_dt + timedelta(days=offset)
        y, m, d = dt.year, dt.month, dt.day
        jd_transit = local_to_julian_day(y, m, d, hour24, minute, timezone)
        
        # Wrap the synchronous _day_summary in a thread for concurrency
        tasks.append(asyncio.to_thread(_day_summary, jd_transit, y, m, d, janma_rasi_idx))

    # 3. Execute all days simultaneously
    days = await asyncio.gather(*tasks)

    return {
        "birth_details": {
            "rasu": janma_details["chandra_rasi"],
            "nakshatra": janma_details["nakshatra"]
        },
        "input_details": {
            "name": name,
            "gender": gender,
            "birth_date": birth_date,
            "date_from": start_date,
            "date_to": days[-1]["date"],
            "time": f"{hour}:{minute:02d} {ampm}",
            "place": place,
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
        },
        "days": days,
    }
