"""
Weekly Horoscope: calculates Panchang + predictions for 7 consecutive days
starting from the birth/submitted date.
"""

from datetime import datetime, timedelta
from ephemeris import local_to_julian_day, get_moon_longitude
from nakshatra import calculate_nakshatra
from panchang import get_complete_panchang
from horoscope_data import (
    WEEKDAY_PREDICTIONS, RASI_PREDICTIONS, NAKSHATRA_PREDICTIONS,
    TITHI_PREDICTIONS, KARANA_PREDICTIONS, YOGA_PREDICTIONS
)


def _day_summary(jd: float, year: int, month: int, day: int) -> dict:
    """Build panchang + predictions for a single day."""
    moon_lon, moon_speed = get_moon_longitude(jd)
    nk = calculate_nakshatra(moon_lon, moon_speed)
    panchang = get_complete_panchang(jd, year, month, day)

    weekday_pred = WEEKDAY_PREDICTIONS.get(panchang["weekday"], {})
    nakshatra_pred = NAKSHATRA_PREDICTIONS.get(nk["nakshatra"], "")
    rasi_pred = RASI_PREDICTIONS.get(nk["chandra_rasi"], {})
    tithi_pred = TITHI_PREDICTIONS.get(panchang["tithi"], "")
    karana_pred = KARANA_PREDICTIONS.get(panchang["karana"], "")
    yoga_pred = YOGA_PREDICTIONS.get(panchang["yoga"], "")

    return {
        "date": f"{year}-{month:02d}-{day:02d}",
        "weekday": panchang["weekday"],
        "nakshatra": nk["nakshatra"],
        "nakshatra_pada": nk["pada_label"],
        "rasi": nk["chandra_rasi"],
        "tithi": panchang["tithi"],
        "karana": panchang["karana"],
        "yoga": panchang["yoga"],
        "predictions": {
            "weekday": {
                "title": f"Weekday: {panchang['weekday']}",
                "description": weekday_pred.get("description", ""),
                "ruling_planet": weekday_pred.get("ruling_planet", ""),
            },
            "nakshatra": {
                "title": f"Nakshatra: {nk['nakshatra']}",
                "description": nakshatra_pred,
            },
            "rasi": {
                "title": f"Rasi: {nk['chandra_rasi']}",
                "description": rasi_pred.get("description", ""),
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


def calculate_weekly_horoscope(
    name: str,
    gender: str,
    date: str,
    hour: int,
    minute: int,
    ampm: str,
    place: str,
    lat: float,
    lon: float,
    timezone: str,
) -> dict:
    """
    Return predictions for 7 days starting from *date*, all at the same
    birth-time so the Moon position shifts naturally day by day.
    """
    year, month, day = map(int, date.split("-"))

    # Convert to 24h
    hour24 = hour
    if ampm == "PM" and hour != 12:
        hour24 += 12
    if ampm == "AM" and hour == 12:
        hour24 = 0

    start = datetime(year, month, day)
    days = []

    for offset in range(7):
        dt = start + timedelta(days=offset)
        y, m, d = dt.year, dt.month, dt.day
        jd = local_to_julian_day(y, m, d, hour24, minute, timezone)
        days.append(_day_summary(jd, y, m, d))

    return {
        "input_details": {
            "name": name,
            "gender": gender,
            "date_from": date,
            "date_to": days[-1]["date"],
            "time": f"{hour}:{minute:02d} {ampm}",
            "place": place,
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
        },
        "days": days,
    }
