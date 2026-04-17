"""
Muhurta timing calculations for Telugu Panchang.

Pure functions that compute auspicious and inauspicious time periods
based on sunrise/sunset Julian Day numbers and weekday offsets.
"""

def jd_to_hhmm(jd, tz):
    """Convert a Julian Day number to 'HH:MM' local time string.

    Args:
        jd: Julian Day number (float, in UT).
        tz: Timezone offset in hours (e.g. 5.5 for IST).

    Returns:
        String in "HH:MM" format (24-hour clock).
    """
    # Convert JD to fractional day in local time
    # JD 0.0 = noon UT, so JD fraction 0.0 = 12:00 UT
    local_jd = jd + tz / 24.0
    # Extract fractional day part (0.0 = midnight, 0.5 = noon)
    frac = (local_jd + 0.5) % 1.0
    total_minutes = round(frac * 24 * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    # Clamp hours to 0-23
    hours = hours % 24
    return f"{hours:02d}:{minutes:02d}"


# ---------------------------------------------------------------------------
# Weekday offset tables (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
# Values are 1-indexed slot numbers within the 8-slot day division.
# ---------------------------------------------------------------------------

RAHU_KALAM_OFFSETS = {
    0: 8,  # Sunday
    1: 2,  # Monday
    2: 7,  # Tuesday
    3: 5,  # Wednesday
    4: 6,  # Thursday
    5: 4,  # Friday
    6: 3,  # Saturday
}

GULIKAI_KALAM_OFFSETS = {
    0: 7,  # Sunday - slot 7
    1: 6,  # Monday - slot 6
    2: 5,  # Tuesday - slot 5
    3: 4,  # Wednesday - slot 4
    4: 3,  # Thursday - slot 3
    5: 2,  # Friday - slot 2
    6: 1,  # Saturday - slot 1
}

YAMAGANDA_OFFSETS = {
    0: 5,  # Sunday
    1: 4,  # Monday
    2: 3,  # Tuesday
    3: 2,  # Wednesday
    4: 1,  # Thursday
    5: 7,  # Friday
    6: 6,  # Saturday
}


def _calc_period(sunrise_jd, sunset_jd, weekday, offsets_table, tz):
    """Generic helper: compute a 1/8-day period for a given weekday offset table.

    Args:
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        weekday: 0 = Sunday … 6 = Saturday.
        offsets_table: dict mapping weekday → 1-indexed slot number.
        tz: Timezone offset in hours.

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    day_dur = sunset_jd - sunrise_jd
    slot = offsets_table[weekday]
    start_jd = sunrise_jd + (slot - 1) * day_dur / 8
    end_jd = start_jd + day_dur / 8
    return (jd_to_hhmm(start_jd, tz), jd_to_hhmm(end_jd, tz))


def calc_rahu_kalam(sunrise_jd, sunset_jd, weekday, tz=5.5):
    """Calculate Rahu Kalam period.

    Args:
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        weekday: 0 = Sunday … 6 = Saturday.
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    return _calc_period(sunrise_jd, sunset_jd, weekday, RAHU_KALAM_OFFSETS, tz)


def calc_gulikai_kalam(sunrise_jd, sunset_jd, weekday, tz=5.5):
    """Calculate Gulikai Kalam period.

    Args:
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        weekday: 0 = Sunday … 6 = Saturday.
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    return _calc_period(sunrise_jd, sunset_jd, weekday, GULIKAI_KALAM_OFFSETS, tz)


def calc_yamaganda(sunrise_jd, sunset_jd, weekday, tz=5.5):
    """Calculate Yamaganda period.

    Args:
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        weekday: 0 = Sunday … 6 = Saturday.
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    return _calc_period(sunrise_jd, sunset_jd, weekday, YAMAGANDA_OFFSETS, tz)


def calc_abhijit_muhurta(sunrise_jd, sunset_jd, tz=5.5):
    """Calculate Abhijit Muhurta — auspicious period around midday.

    Traditional calculation: 8th muhurta of the day (each muhurta = 1/15 of day).
    This is approximately 24-48 minutes centered slightly before solar noon.

    Args:
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    # Abhijit is the 8th muhurta (out of 15 muhurtas in a day)
    # Each muhurta is 1/15 of the day duration
    day_dur = sunset_jd - sunrise_jd
    muhurta_dur = day_dur / 15.0
    
    # 8th muhurta starts at 7/15 of the day
    start_jd = sunrise_jd + 7 * muhurta_dur
    end_jd = start_jd + muhurta_dur
    
    return (jd_to_hhmm(start_jd, tz), jd_to_hhmm(end_jd, tz))


# ---------------------------------------------------------------------------
# Dur Muhurtam — weekday-specific inauspicious slots
# Each slot is 1/15 of day duration from sunrise.
# Values are lists of 1-indexed slot numbers.
# Traditional Dur Muhurtam slots per weekday (0 = Sunday):
# ---------------------------------------------------------------------------

DUR_MUHURTAM_SLOTS = {
    0: [9, 13],    # Sunday - slots 9 and 13
    1: [6, 11],    # Monday - slots 6 and 11
    2: [3, 10],    # Tuesday - slots 3 and 10
    3: [7, 12],    # Wednesday - slots 7 and 12
    4: [5, 10],    # Thursday - slots 5 and 10
    5: [4, 9],     # Friday - slots 4 and 9
    6: [1, 8],     # Saturday - slots 1 and 8
}


def calc_dur_muhurtam(sunrise_jd, sunset_jd, weekday, tz=5.5):
    """Calculate Dur Muhurtam (inauspicious) periods for the day.

    Each Dur Muhurtam slot is 1/15 of the day duration from sunrise.

    Args:
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        weekday: 0 = Sunday … 6 = Saturday.
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        List of tuples [(start_hhmm, end_hhmm), ...].
    """
    day_dur = sunset_jd - sunrise_jd
    slot_dur = day_dur / 15.0
    slots = DUR_MUHURTAM_SLOTS.get(weekday, [])
    result = []
    for slot in slots:
        start_jd = sunrise_jd + (slot - 1) * slot_dur
        end_jd = start_jd + slot_dur
        result.append((jd_to_hhmm(start_jd, tz), jd_to_hhmm(end_jd, tz)))
    return result


# ---------------------------------------------------------------------------
# Amrit Kalam and Varjyam
#
# Each nakshatra (1–27) has a fixed offset (in ghatikas from the start of
# the nakshatra) at which Amrit Kalam and Varjyam begin.
# 1 ghatika = 24 minutes. Each period lasts 4 ghatikas (96 minutes = 1h 36m).
#
# The offsets below are in ghatikas from the start of the nakshatra.
# Source: traditional panchang tables.
# ---------------------------------------------------------------------------

# Amrit Kalam start offsets in ghatikas (1-indexed by nakshatra number)
# Updated based on traditional Telugu panchang calculations
AMRIT_KALAM_GHATIKAS = {
    1: 10, 2: 14, 3: 18, 4: 22, 5: 26,
    6: 2, 7: 6, 8: 10, 9: 14, 10: 18,
    11: 22, 12: 26, 13: 2, 14: 6, 15: 10,
    16: 14, 17: 18, 18: 22, 19: 26, 20: 2,
    21: 6, 22: 10, 23: 14, 24: 18, 25: 22,
    26: 26, 27: 10,  # Revati (27) uses offset 10
}

# Varjyam start offsets in ghatikas (1-indexed by nakshatra number)
VARJYAM_GHATIKAS = {
    1: 50, 2: 46, 3: 42, 4: 38, 5: 34,
    6: 30, 7: 26, 8: 50, 9: 46, 10: 42,
    11: 38, 12: 34, 13: 30, 14: 26, 15: 50,
    16: 46, 17: 42, 18: 38, 19: 34, 20: 30,
    21: 26, 22: 50, 23: 46, 24: 42, 25: 38,
    26: 34, 27: 30,
}

# Duration of Amrit Kalam period in minutes (traditional: 88 minutes, not 96)
_AMRIT_KALAM_DURATION_MINUTES = 88  # 3.67 ghatikas

# Duration of Varjyam period in ghatikas (traditional: 4 ghatikas = 96 minutes)
_VARJYAM_DURATION_GHATIKAS = 4


def _ghatikas_to_jd(ghatikas):
    """Convert ghatikas to Julian Day fraction.

    1 ghatika = 24 minutes = 24/1440 days.
    """
    return ghatikas * 24.0 / 1440.0


def calc_amrit_kalam(nakshatra_num, sunrise_jd, sunset_jd, tz=5.5):
    """Calculate Amrit Kalam period based on the current nakshatra.

    The Amrit Kalam starts at a fixed ghatika offset from sunrise
    (approximated as the start of the nakshatra's influence for the day).
    Duration is 88 minutes (3.67 ghatikas).

    Args:
        nakshatra_num: Current nakshatra number (1–27).
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    nak = max(1, min(27, nakshatra_num))
    offset_gh = AMRIT_KALAM_GHATIKAS[nak]
    start_jd = sunrise_jd + _ghatikas_to_jd(offset_gh)
    # Duration is 88 minutes, not 96
    end_jd = start_jd + _AMRIT_KALAM_DURATION_MINUTES / 1440.0
    return (jd_to_hhmm(start_jd, tz), jd_to_hhmm(end_jd, tz))


def calc_varjyam(nakshatra_num, sunrise_jd, sunset_jd, tz=5.5):
    """Calculate Varjyam (inauspicious) period based on the current nakshatra.

    The Varjyam starts at a fixed ghatika offset from sunrise.
    Duration is 4 ghatikas (96 minutes).

    Args:
        nakshatra_num: Current nakshatra number (1–27).
        sunrise_jd: Julian Day of sunrise (UT).
        sunset_jd: Julian Day of sunset (UT).
        tz: Timezone offset in hours (default 5.5 for IST).

    Returns:
        Tuple (start_hhmm, end_hhmm).
    """
    nak = max(1, min(27, nakshatra_num))
    offset_gh = VARJYAM_GHATIKAS[nak]
    start_jd = sunrise_jd + _ghatikas_to_jd(offset_gh)
    end_jd = start_jd + _ghatikas_to_jd(_VARJYAM_DURATION_GHATIKAS)
    return (jd_to_hhmm(start_jd, tz), jd_to_hhmm(end_jd, tz))
