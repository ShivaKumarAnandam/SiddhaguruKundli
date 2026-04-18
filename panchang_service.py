"""
Core calculation orchestrator for Telugu Panchang.

Wraps the drik-panchanga library (panchanga.py) and composes results from
muhurta.py and festival_data.py into structured daily/monthly responses.
"""

import asyncio
import calendar
import os
import sys
import json
from math import ceil
from functools import lru_cache
from datetime import datetime, timedelta

# Make drik-panchanga importable
_drik_path = os.path.join(os.path.dirname(__file__), "drik-panchanga")
if _drik_path not in sys.path:
    sys.path.insert(0, _drik_path)

import panchanga  # noqa: E402
from panchanga import (  # noqa: E402
    Date,
    Place,
    gregorian_to_jd,
    sunrise as _sunrise,
    sunset as _sunset,
    moonrise as _moonrise,
    moonset as _moonset,
    tithi as _tithi,
    nakshatra as _nakshatra,
    yoga as _yoga,
    karana as _karana,
    vaara as _vaara,
    masa as _masa,
    raasi as _raasi,
    lunar_longitude as _lunar_longitude,
    elapsed_year as _elapsed_year,
    samvatsara as _samvatsara,
)
import swisseph as swe  # noqa: E402

from muhurta import (  # noqa: E402
    calc_rahu_kalam,
    calc_gulikai_kalam,
    calc_yamaganda,
    calc_abhijit_muhurta,
    calc_dur_muhurtam,
    calc_amrit_kalam,
    calc_varjyam,
)
from festival_data import get_festivals  # noqa: E402

# ---------------------------------------------------------------------------
# Name lookup tables — English
# ---------------------------------------------------------------------------

TITHI_NAMES_EN = [
    "",  # 0-index placeholder
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

TITHI_NAMES_TE = [
    "",
    "పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి",
    "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి",
    "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "పూర్ణిమ",
    "పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి",
    "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి",
    "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "అమావాస్య",
]

TITHI_NAMES_HI = [
    "",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावस्या",
]

NAKSHATRA_NAMES_EN = [
    "",  # 0-index placeholder
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_NAMES_TE = [
    "",
    "అశ్విని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర",
    "ఆర్ద్ర", "పునర్వసు", "పుష్యమి", "ఆశ్లేష", "మఘ",
    "పూర్వ ఫల్గుణి", "ఉత్తర ఫల్గుణి", "హస్త", "చిత్త", "స్వాతి",
    "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ",
    "ఉత్తరాషాఢ", "శ్రవణం", "ధనిష్ఠ", "శతభిషం",
    "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి",
]

NAKSHATRA_NAMES_HI = [
    "",
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा",
    "आर्द्रा", "पुनर्वसु", "पुष्य", "अश्लेषा", "मघा",
    "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी", "हस्त", "चित्रा", "स्वाती",
    "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा",
    "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा",
    "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती",
]

YOGA_NAMES_EN = [
    "",
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Aindra", "Vaidhriti",
]

YOGA_NAMES_TE = [
    "",
    "విష్కంభ", "ప్రీతి", "ఆయుష్మాన్", "సౌభాగ్య", "శోభన",
    "అతిగండ", "సుకర్మ", "ధృతి", "శూల", "గండ",
    "వృద్ధి", "ధ్రువ", "వ్యాఘాత", "హర్షణ", "వజ్ర",
    "సిద్ధి", "వ్యతీపాత", "వారీయాన", "పరిఘ", "శివ",
    "సిద్ధ", "సాధ్య", "శుభ", "శుక్ల", "బ్రహ్మ",
    "ఐంద్ర", "వైధృతి",
]

YOGA_NAMES_HI = [
    "",
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन",
    "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड",
    "वृद्धि", "ध्रुव", "व्याघात", "हर्षण", "वज्र",
    "सिद्धि", "व्यतीपात", "वरीयान", "परिघ", "शिव",
    "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म",
    "ऐन्द्र", "वैधृति",
]

# 11 unique Karana names (7 movable + 4 fixed)
KARANA_NAMES_EN = [
    "",
    "Kinstughna", "Bava", "Balava", "Kaulava", "Taitila",
    "Garaja", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga",
]

KARANA_NAMES_TE = [
    "",
    "కింస్తుఘ్న", "బవ", "బాలవ", "కౌలవ", "తైతిల",
    "గరజ", "వణిజ", "విష్టి", "శకుని", "చతుష్పాద", "నాగ",
]

KARANA_NAMES_HI = [
    "",
    "किंस्तुघ्न", "बव", "बालव", "कौलव", "तैतिल",
    "गरज", "वणिज", "विष्टि", "शकुनि", "चतुष्पाद", "नाग",
]

# Karana mapping: karana number (1-60) → unique karana name index (1-11)
@lru_cache(maxsize=32)
def _karana_index(karana_num: int) -> int:
    """Map karana number (1-60) to unique karana name index (1-11).

    Karanas 1 = Kimstughna (fixed), 2-8 = Bava..Vishti (movable, repeat 7 times),
    58 = Shakuni, 59 = Chatushpada, 60 = Nagava (fixed).
    """
    karana_num = int(karana_num)
    if karana_num == 1:
        return 1  # Kimstughna
    elif karana_num >= 58:
        return karana_num - 49  # 58→9(Shakuni), 59→10(Chatushpada), 60→11(Nagava)
    else:
        # Movable karanas: 2-8 repeat. Map to index 2-8.
        return ((karana_num - 2) % 7) + 2

VAARA_NAMES_EN = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday",
]

VAARA_NAMES_TE = [
    "ఆదివారం", "సోమవారం", "మంగళవారం", "బుధవారం",
    "గురువారం", "శుక్రవారం", "శనివారం",
]

VAARA_NAMES_HI = [
    "रविवार", "सोमवार", "मंगलवार", "बुधवार",
    "गुरुवार", "शुक्रवार", "शनिवार",
]

MASA_NAMES_EN = [
    "",
    "Chaitra", "Vaisakha", "Jyeshtha", "Ashadha",
    "Shravana", "Bhadrapada", "Ashwina", "Kartika",
    "Margashira", "Pushya", "Magha", "Phalguna",
]

MASA_NAMES_TE = [
    "",
    "చైత్రం", "వైశాఖం", "జ్యేష్ఠం", "ఆషాఢం",
    "శ్రావణం", "భాద్రపదం", "ఆశ్వయుజం", "కార్తీకం",
    "మార్గశిరం", "పుష్యం", "మాఘం", "ఫాల్గుణం",
]

MASA_NAMES_HI = [
    "",
    "चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़",
    "श्रावण", "भाद्रपद", "अश्विन", "कार्तिक",
    "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन",
]

SAMVATSARA_NAMES_EN = [
    "",  # 0-index placeholder (samvatsara is 1-60, but library returns 0-59)
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati",
    "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri",
    "Ishvara", "Bahudhanya", "Pramadhi", "Vikrama", "Vrisha",
    "Chitrabhanu", "Svabhanu", "Tarana", "Parthiva", "Vyaya",
    "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti", "Khara",
    "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava",
    "Shubhakrit", "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava",
    "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhikrit",
    "Paridhavi", "Pramadicha", "Ananda", "Rakshasa", "Nala",
    "Pingala", "Kalayukti", "Siddharthi", "Raudra", "Durmati",
    "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]

SAMVATSARA_NAMES_TE = [
    "",
    "ప్రభవ", "విభవ", "శుక్ల", "ప్రమోద", "ప్రజాపతి",
    "ఆంగీరస", "శ్రీముఖ", "భావ", "యువ", "ధాతృ",
    "ఈశ్వర", "బహుధాన్య", "ప్రమాది", "విక్రమ", "వృష",
    "చిత్రభాను", "స్వభాను", "తారణ", "పార్థివ", "వ్యయ",
    "సర్వజిత్", "సర్వధారి", "విరోధి", "వికృతి", "ఖర",
    "నందన", "విజయ", "జయ", "మన్మథ", "దుర్ముఖి",
    "హేవిళంబి", "విళంబి", "వికారి", "శార్వరి", "ప్లవ",
    "శుభకృత్", "శోభకృత్", "క్రోధి", "విశ్వావసు", "పరాభవ",
    "ప్లవంగ", "కీలక", "సౌమ్య", "సాధారణ", "విరోధికృత్",
    "పరిధావి", "ప్రమాదీచ", "ఆనంద", "రాక్షస", "నల",
    "పింగళ", "కాలయుక్తి", "సిద్ధార్థి", "రౌద్ర", "దుర్మతి",
    "దుందుభి", "రుధిరోద్గారి", "రక్తాక్షి", "క్రోధన", "అక్షయ",
]

SAMVATSARA_NAMES_HI = [
    "",
    "प्रभव", "विभव", "शुक्ल", "प्रमोद", "प्रजापति",
    "अंगिरा", "श्रीमुख", "भाव", "युवा", "धाता",
    "ईश्वर", "बहुधान्य", "प्रमादी", "विक्रम", "वृष",
    "चित्रभानु", "स्वभानु", "तारण", "पार्थिव", "व्यय",
    "सर्वजीत", "सर्वधारी", "विरोधी", "विकृति", "खर",
    "नंदन", "विजय", "जय", "मन्मथ", "दुर्मुख",
    "हेविलम्बी", "विलम्बी", "विकारी", "शार्वरी", "प्लव",
    "शुभकृत", "शोभकृत", "क्रोधी", "विश्वावसु", "पराभव",
    "प्लवंग", "कीलक", "सौम्य", "साधारण", "विरोधकृत",
    "परिधावी", "प्रमादी", "आनंद", "राक्षस", "नल",
    "पिंगल", "कालद्युति", "सिद्धार्थी", "रौद्र", "दुर्मति",
    "दुन्दुभी", "रुधिरोद्गारी", "रक्ताक्ष", "क्रोधन", "अक्षय",
]

RASHI_NAMES_EN = [
    "",
    "Mesha", "Vrishabha", "Mithuna", "Karka",
    "Simha", "Kanya", "Tula", "Vrischika",
    "Dhanu", "Makara", "Kumbha", "Meena",
]

RASHI_NAMES_TE = [
    "",
    "మేషం", "వృషభం", "మిథునం", "కర్కాటకం",
    "సింహం", "కన్య", "తుల", "వృశ్చికం",
    "ధనుస్సు", "మకరం", "కుంభం", "మీనం",
]

RASHI_NAMES_HI = [
    "",
    "मेष", "वृषभ", "मिथुन", "कर्क",
    "सिंह", "कन्या", "तुला", "वृश्चिक",
    "धनु", "मकर", "कुंभ", "मीन",
]

PAKSHA_NAMES = {
    "en": {"shukla": "Shukla Paksha", "krishna": "Krishna Paksha"},
    "te": {"shukla": "శుక్ల పక్షం", "krishna": "కృష్ణ పక్షం"},
    "hi": {"shukla": "शुक्ल पक्ष", "krishna": "कृष्ण पक्ष"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "panchang_cache.json")

# In-memory maps for daily and monthly panchang results
_daily_cache = {}
_daily_cache_ttl = {}
_monthly_cache = {}
_monthly_cache_ttl = {}
CACHE_TTL_SECONDS = 86400  # 24 hours

def _save_cache_to_disk():
    """Serialize the current in-memory cache to a JSON file."""
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        # We only save valid (non-expired) entries
        now = datetime.now()
        data = {
            "daily": {k: v for k, v in _daily_cache.items() if k in _daily_cache_ttl and now < _daily_cache_ttl[k]},
            "daily_ttl": {k: _daily_cache_ttl[k].isoformat() for k, v in _daily_cache.items() if k in _daily_cache_ttl and now < _daily_cache_ttl[k]},
            "monthly": {k: v for k, v in _monthly_cache.items() if k in _monthly_cache_ttl and now < _monthly_cache_ttl[k]},
            "monthly_ttl": {k: _monthly_cache_ttl[k].isoformat() for k, v in _monthly_cache.items() if k in _monthly_cache_ttl and now < _monthly_cache_ttl[k]},
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Cache save error: {e}")

def _load_cache_from_disk():
    """Load cached data from the JSON file into memory."""
    global _daily_cache, _daily_cache_ttl, _monthly_cache, _monthly_cache_ttl
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                now = datetime.now()
                
                # Load daily
                daily_ttl = data.get("daily_ttl", {})
                for k, v in data.get("daily", {}).items():
                    if k in daily_ttl:
                        ttl = datetime.fromisoformat(daily_ttl[k])
                        if now < ttl:
                            _daily_cache[k] = v
                            _daily_cache_ttl[k] = ttl
                
                # Load monthly
                monthly_ttl = data.get("monthly_ttl", {})
                for k, v in data.get("monthly", {}).items():
                    if k in monthly_ttl:
                        ttl = datetime.fromisoformat(monthly_ttl[k])
                        if now < ttl:
                            _monthly_cache[k] = v
                            _monthly_cache_ttl[k] = ttl
    except Exception as e:
        print(f"Cache load error: {e}")

# Initial load
_load_cache_from_disk()

def _get_cached_daily(cache_key: str):
    """Get cached daily panchang if still valid."""
    if cache_key in _daily_cache:
        if cache_key in _daily_cache_ttl:
            if datetime.now() < _daily_cache_ttl[cache_key]:
                return _daily_cache[cache_key]
            else:
                # Expired, remove from cache
                del _daily_cache[cache_key]
                del _daily_cache_ttl[cache_key]
    return None

def _set_cached_daily(cache_key: str, data: dict):
    """Cache daily panchang result with TTL."""
    _daily_cache[cache_key] = data
    _daily_cache_ttl[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS)

@lru_cache(maxsize=128)
def _cached_get_name(index: int, lang: str, name_type: str):
    """Cached name lookup to avoid repeated list access."""
    if name_type == 'tithi':
        names = TITHI_NAMES_HI if lang == 'hi' else (TITHI_NAMES_TE if lang == 'te' else TITHI_NAMES_EN)
    elif name_type == 'nakshatra':
        names = NAKSHATRA_NAMES_HI if lang == 'hi' else (NAKSHATRA_NAMES_TE if lang == 'te' else NAKSHATRA_NAMES_EN)
    elif name_type == 'yoga':
        names = YOGA_NAMES_HI if lang == 'hi' else (YOGA_NAMES_TE if lang == 'te' else YOGA_NAMES_EN)
    elif name_type == 'karana':
        names = KARANA_NAMES_HI if lang == 'hi' else (KARANA_NAMES_TE if lang == 'te' else KARANA_NAMES_EN)
    elif name_type == 'masa':
        names = MASA_NAMES_HI if lang == 'hi' else (MASA_NAMES_TE if lang == 'te' else MASA_NAMES_EN)
    elif name_type == 'samvatsara':
        names = SAMVATSARA_NAMES_HI if lang == 'hi' else (SAMVATSARA_NAMES_TE if lang == 'te' else SAMVATSARA_NAMES_EN)
    elif name_type == 'rashi':
        names = RASHI_NAMES_HI if lang == 'hi' else (RASHI_NAMES_TE if lang == 'te' else RASHI_NAMES_EN)
    else:
        return str(index)
    
    if 1 <= index < len(names):
        return names[index]
    return names[index % len(names)] if len(names) > 1 else str(index)

def _dms_to_hhmm(dms):
    """Convert a [h, m, s] array from panchanga.py to 'HH:MM' string."""
    if not dms or len(dms) < 2:
        return "00:00"
    try:
        h = int(dms[0])
        m = int(dms[1])
        
        # Handle negative values (next day)
        if h < 0 or m < 0:
            # Convert to next day time
            total_minutes = h * 60 + m
            if total_minutes < 0:
                total_minutes += 24 * 60  # Add 24 hours
            h = (total_minutes // 60) % 24
            m = total_minutes % 60
        
        # Ensure values are in valid range
        h = h % 24
        m = max(0, min(59, m))
        
        return f"{h:02d}:{m:02d}"
    except (ValueError, TypeError, IndexError):
        return "00:00"


def _get_name(index, en_list, te_list, lang, hi_list=None):
    """Safely look up a name from the EN/TE/HI lists by 1-based index."""
    index = int(index)
    if lang == "hi" and hi_list:
        names = hi_list
    elif lang == "te":
        names = te_list
    else:
        names = en_list
    
    if 1 <= index < len(names):
        return names[index]
    return names[index % len(names)] if len(names) > 1 else str(index)


@lru_cache(maxsize=64)
def _paksha_from_tithi(tithi_num):
    """Determine paksha from tithi number: 1-15 = Shukla, 16-30 = Krishna."""
    tithi_num = int(tithi_num)
    return "shukla" if 1 <= tithi_num <= 15 else "krishna"


@lru_cache(maxsize=64)
def _tithi_in_paksha(tithi_num):
    """Convert absolute tithi (1-30) to within-paksha tithi (1-15)."""
    tithi_num = int(tithi_num)
    if tithi_num <= 15:
        return tithi_num
    return tithi_num - 15


def _chandra_rashi(jd):
    """Compute Chandra Rashi (lunar zodiac sign) from lunar longitude."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon_long = _lunar_longitude(jd)
    lunar_nirayana = (moon_long - swe.get_ayanamsa_ut(jd)) % 360
    return int(ceil(lunar_nirayana / 30.0))


def _chandra_rashi_with_end_time(jd, place):
    """Compute Chandra Rashi and its end time."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    tz = place.timezone
    
    # Get sunrise time
    from panchanga import sunrise as _sunrise_fn
    rise = _sunrise_fn(jd, place)[0] - tz / 24
    
    # Current moon rashi at sunrise
    moon_long = _lunar_longitude(rise)
    lunar_nirayana = (moon_long - swe.get_ayanamsa_ut(rise)) % 360
    current_rashi = int(ceil(lunar_nirayana / 30.0))
    
    # Degrees left in current rashi
    degrees_left = current_rashi * 30 - lunar_nirayana
    
    # Compute lunar motion at intervals
    offsets = [0.25, 0.5, 0.75, 1.0]
    lunar_longs = []
    for t in offsets:
        moon_long_t = _lunar_longitude(rise + t)
        lunar_nirayana_t = (moon_long_t - swe.get_ayanamsa_ut(rise + t)) % 360
        lunar_longs.append(lunar_nirayana_t)
    
    # Check if rashi changes during the day
    from panchanga import unwrap_angles, inverse_lagrange, to_dms
    y = unwrap_angles([lunar_nirayana] + lunar_longs)
    x = [0.0] + offsets
    
    # Find when moon reaches next rashi boundary
    next_rashi_degree = current_rashi * 30
    if next_rashi_degree <= y[0]:
        next_rashi_degree += 360
    
    # Check if transition happens within the day
    if y[-1] >= next_rashi_degree or (y[-1] < y[0] and y[-1] + 360 >= next_rashi_degree):
        try:
            approx_end = inverse_lagrange(x, y, next_rashi_degree)
            ends = (rise + approx_end - jd) * 24 + tz
            end_time_dms = to_dms(ends)
            return current_rashi, end_time_dms
        except:
            return current_rashi, None
    
    return current_rashi, None


# ---------------------------------------------------------------------------
# Daily Panchang
# ---------------------------------------------------------------------------

async def get_daily_panchang(date_str: str, lat: float, lon: float,
                              tz_offset: float, lang: str = "en") -> dict:
    """Compute complete daily panchang for the given date and location.

    Args:
        date_str: Date in YYYY-MM-DD format.
        lat: Latitude (-90 to 90).
        lon: Longitude (-180 to 180).
        tz_offset: Timezone offset in hours (e.g. 5.5 for IST).
        lang: "en" or "te".

    Returns:
        Dict matching the DailyPanchangResponse schema.
    """
    # Check cache first
    cache_key = f"{date_str}|{lat:.4f}|{lon:.4f}|{tz_offset}|{lang}"
    if cache_key in _daily_cache:
        if datetime.now() < _daily_cache_ttl.get(cache_key, datetime.min):
            return _daily_cache[cache_key]
        else:
            del _daily_cache[cache_key]
            if cache_key in _daily_cache_ttl: del _daily_cache_ttl[cache_key]
    
    year, month, day = map(int, date_str.split("-"))
    date_obj = Date(year, month, day)
    place = Place(lat, lon, tz_offset)
    jd = gregorian_to_jd(date_obj)

    # Parallel astronomical calculations via asyncio.to_thread
    (
        tithi_result,
        nakshatra_result,
        yoga_result,
        karana_result,
        vaara_result,
        masa_result,
        sunrise_result,
        sunset_result,
        moonrise_result,
        moonset_result,
        sun_rashi_result,
        chandra_rashi_with_time,
    ) = await asyncio.gather(
        asyncio.to_thread(_tithi, jd, place),
        asyncio.to_thread(_nakshatra, jd, place),
        asyncio.to_thread(_yoga, jd, place),
        asyncio.to_thread(_karana, jd, place),
        asyncio.to_thread(_vaara, jd),
        asyncio.to_thread(_masa, jd, place),
        asyncio.to_thread(_sunrise, jd, place),
        asyncio.to_thread(_sunset, jd, place),
        asyncio.to_thread(_moonrise, jd, place),
        asyncio.to_thread(_moonset, jd, place),
        asyncio.to_thread(_raasi, jd),
        asyncio.to_thread(_chandra_rashi_with_end_time, jd, place),
    )
    
    chandra_rashi_result, chandra_rashi_end_dms = chandra_rashi_with_time

    # --- Extract tithi ---
    tithi_num = int(tithi_result[0])
    tithi_end_dms = tithi_result[1] if len(tithi_result) > 1 else [0, 0, 0]
    tithi_name = _get_name(tithi_num, TITHI_NAMES_EN, TITHI_NAMES_TE, lang)
    tithi_end_time = _dms_to_hhmm(tithi_end_dms)

    # Check for skipped tithi (4 elements)
    next_tithi_name = None
    next_tithi_end_time = None
    if len(tithi_result) >= 4:
        next_tithi_num = int(tithi_result[2])
        next_tithi_end_dms = tithi_result[3]
        next_tithi_name = _get_name(next_tithi_num, TITHI_NAMES_EN, TITHI_NAMES_TE, lang)
        next_tithi_end_time = _dms_to_hhmm(next_tithi_end_dms)

    # --- Extract nakshatra ---
    nak_num = int(nakshatra_result[0])
    nak_end_dms = nakshatra_result[1] if len(nakshatra_result) > 1 else [0, 0, 0]
    nak_name = _get_name(nak_num, NAKSHATRA_NAMES_EN, NAKSHATRA_NAMES_TE, lang)
    nak_end_time = _dms_to_hhmm(nak_end_dms)

    next_nak_name = None
    next_nak_end_time = None
    if len(nakshatra_result) >= 4:
        next_nak_num = int(nakshatra_result[2])
        next_nak_end_dms = nakshatra_result[3]
        next_nak_name = _get_name(next_nak_num, NAKSHATRA_NAMES_EN, NAKSHATRA_NAMES_TE, lang)
        next_nak_end_time = _dms_to_hhmm(next_nak_end_dms)

    # --- Extract yoga ---
    yoga_num = int(yoga_result[0])
    yoga_end_dms = yoga_result[1] if len(yoga_result) > 1 else [0, 0, 0]
    yoga_name = _get_name(yoga_num, YOGA_NAMES_EN, YOGA_NAMES_TE, lang)
    yoga_end_time = _dms_to_hhmm(yoga_end_dms)

    next_yoga_name = None
    next_yoga_end_time = None
    if len(yoga_result) >= 4:
        next_yoga_num = int(yoga_result[2])
        next_yoga_end_dms = yoga_result[3]
        next_yoga_name = _get_name(next_yoga_num, YOGA_NAMES_EN, YOGA_NAMES_TE, lang)
        next_yoga_end_time = _dms_to_hhmm(next_yoga_end_dms)

    # --- Extract karana ---
    karana_list = []
    for i in range(0, len(karana_result), 2):
        if i + 1 < len(karana_result):
            karana_num = int(karana_result[i])
            # Wrap karana number to 1-60 range
            if karana_num > 60:
                karana_num = ((karana_num - 1) % 60) + 1
            karana_end_dms = karana_result[i + 1]
            ki = _karana_index(karana_num)
            karana_name = _get_name(ki, KARANA_NAMES_EN, KARANA_NAMES_TE, lang)
            karana_end_time = _dms_to_hhmm(karana_end_dms)
            karana_list.append({
                "name": karana_name,
                "number": karana_num,
                "end_time": karana_end_time
            })
        else:
            # Last karana without end time (extends to next day)
            karana_num = int(karana_result[i])
            # Wrap karana number to 1-60 range
            if karana_num > 60:
                karana_num = ((karana_num - 1) % 60) + 1
            ki = _karana_index(karana_num)
            karana_name = _get_name(ki, KARANA_NAMES_EN, KARANA_NAMES_TE, lang)
            karana_list.append({
                "name": karana_name,
                "number": karana_num,
                "end_time": None
            })
    
    # Fallback if no karanas found
    if not karana_list:
        karana_num = int(karana_result[0]) if karana_result else 1
        if karana_num > 60:
            karana_num = ((karana_num - 1) % 60) + 1
        ki = _karana_index(karana_num)
        karana_name = _get_name(ki, KARANA_NAMES_EN, KARANA_NAMES_TE, lang)
        karana_list.append({
            "name": karana_name,
            "number": karana_num,
            "end_time": None
        })

    # --- Vaara ---
    vaara_result = int(vaara_result)
    vaara_name = VAARA_NAMES_TE[vaara_result] if lang == "te" else VAARA_NAMES_EN[vaara_result]

    # --- Masa, Paksha, Samvat, Samvatsara ---
    masa_num = int(masa_result[0])
    masa_name = _get_name(masa_num, MASA_NAMES_EN, MASA_NAMES_TE, lang)

    paksha_key = _paksha_from_tithi(tithi_num)
    paksha_name = PAKSHA_NAMES.get(lang, PAKSHA_NAMES["en"])[paksha_key]
    paksha_num = 1 if paksha_key == "shukla" else 2

    # Elapsed year → Saka Samvat
    kali, saka = await asyncio.to_thread(_elapsed_year, jd, masa_num)
    samvat = saka

    # Samvatsara (60-year cycle)
    samvatsara_idx = int(await asyncio.to_thread(_samvatsara, jd, masa_num))
    # Library returns 0-59; our table is 1-indexed
    samvatsara_name = _get_name(
        samvatsara_idx + 1 if samvatsara_idx < 60 else samvatsara_idx,
        SAMVATSARA_NAMES_EN, SAMVATSARA_NAMES_TE, lang,
    )

    # --- Solar / Lunar times ---
    # sunrise returns [jd, [h,m,s]], sunset returns [jd, [h,m,s]]
    sunrise_jd = sunrise_result[0]
    sunrise_hhmm = _dms_to_hhmm(sunrise_result[1])
    sunset_jd = sunset_result[0]
    sunset_hhmm = _dms_to_hhmm(sunset_result[1])
    # moonrise/moonset return [h,m,s]
    # Handle "No Moonrise" or "No Moonset" cases
    if moonrise_result and moonrise_result[0] >= 0:
        moonrise_hhmm = _dms_to_hhmm(moonrise_result)
    else:
        moonrise_hhmm = "No Moonrise"
    
    if moonset_result and moonset_result[0] >= 0:
        moonset_hhmm = _dms_to_hhmm(moonset_result)
    else:
        moonset_hhmm = "No Moonset"

    # --- Rashi ---
    sun_rashi_result = int(sun_rashi_result)
    sun_rashi_name = _get_name(sun_rashi_result, RASHI_NAMES_EN, RASHI_NAMES_TE, lang)
    chandra_rashi_name = _get_name(chandra_rashi_result, RASHI_NAMES_EN, RASHI_NAMES_TE, lang)
    chandra_rashi_end_time = _dms_to_hhmm(chandra_rashi_end_dms) if chandra_rashi_end_dms else None

    # --- Muhurta timings ---
    # sunrise_jd and sunset_jd from panchanga are in local JD; convert to UT for muhurta
    sunrise_jd_ut = sunrise_jd - tz_offset / 24.0
    sunset_jd_ut = sunset_jd - tz_offset / 24.0

    rahu_start, rahu_end = await asyncio.to_thread(
        calc_rahu_kalam, sunrise_jd_ut, sunset_jd_ut, vaara_result, tz_offset)
    gulikai_start, gulikai_end = await asyncio.to_thread(
        calc_gulikai_kalam, sunrise_jd_ut, sunset_jd_ut, vaara_result, tz_offset)
    yamaganda_start, yamaganda_end = await asyncio.to_thread(
        calc_yamaganda, sunrise_jd_ut, sunset_jd_ut, vaara_result, tz_offset)
    abhijit_start, abhijit_end = await asyncio.to_thread(
        calc_abhijit_muhurta, sunrise_jd_ut, sunset_jd_ut, tz_offset)
    dur_muhurtam_list = await asyncio.to_thread(
        calc_dur_muhurtam, sunrise_jd_ut, sunset_jd_ut, vaara_result, tz_offset)
    amrit_start, amrit_end = await asyncio.to_thread(
        calc_amrit_kalam, nak_num, sunrise_jd_ut, sunset_jd_ut, tz_offset)
    varjyam_start, varjyam_end = await asyncio.to_thread(
        calc_varjyam, nak_num, sunrise_jd_ut, sunset_jd_ut, tz_offset)

    # --- Festivals ---
    tithi_in_paksha = _tithi_in_paksha(tithi_num)
    festivals = await asyncio.to_thread(
        get_festivals, masa_num, paksha_num, tithi_in_paksha, lang)

    # --- Build response ---
    result = {
        "date": date_str,
        # Header
        "masa": masa_name,
        "paksha": paksha_name,
        "samvat": samvat,
        "samvatsara": samvatsara_name,
        # Pancha Anga
        "tithi": {
            "number": tithi_num,
            "name": tithi_name,
            "end_time": tithi_end_time,
            "next_name": next_tithi_name,
            "next_end_time": next_tithi_end_time,
        },
        "nakshatra": {
            "number": nak_num,
            "name": nak_name,
            "end_time": nak_end_time,
            "next_name": next_nak_name,
            "next_end_time": next_nak_end_time,
        },
        "yoga": {
            "number": yoga_num,
            "name": yoga_name,
            "end_time": yoga_end_time,
            "next_name": next_yoga_name,
            "next_end_time": next_yoga_end_time,
        },
        "karana": karana_list,
        "vaara": vaara_name,
        # Solar / Lunar
        "sunrise": sunrise_hhmm,
        "sunset": sunset_hhmm,
        "moonrise": moonrise_hhmm,
        "moonset": moonset_hhmm,
        "sun_rashi": sun_rashi_name,
        "chandra_rashi": {
            "name": chandra_rashi_name,
            "end_time": chandra_rashi_end_time
        },
        # Muhurtas
        "muhurtas": {
            "rahu_kalam": {"start": rahu_start, "end": rahu_end},
            "gulikai_kalam": {"start": gulikai_start, "end": gulikai_end},
            "yamaganda": {"start": yamaganda_start, "end": yamaganda_end},
            "abhijit_muhurta": {"start": abhijit_start, "end": abhijit_end},
            "dur_muhurtam": [{"start": s, "end": e} for s, e in dur_muhurtam_list],
            "amrit_kalam": {"start": amrit_start, "end": amrit_end},
            "varjyam": {"start": varjyam_start, "end": varjyam_end},
        },
        # Festivals
        "festivals": festivals,
    }
    
    # Cache the result
    _daily_cache[cache_key] = result
    _daily_cache_ttl[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS)
    _save_cache_to_disk()
    return result


# ---------------------------------------------------------------------------
# Monthly Panchang
# ---------------------------------------------------------------------------

async def _compute_day_summary(year: int, month: int, day: int,
                                lat: float, lon: float, tz_offset: float,
                                lang: str) -> dict:
    """Compute a detailed daily summary for the monthly grid (optimized version)."""
    date_obj = Date(year, month, day)
    place = Place(lat, lon, tz_offset)
    jd = gregorian_to_jd(date_obj)

    # Parallel fetch only essential data for monthly view
    (
        tithi_result,
        nakshatra_result,
        vaara_result,
        masa_result,
        sunrise_result,
        sunset_result,
        chandra_rashi_num,
    ) = await asyncio.gather(
        asyncio.to_thread(_tithi, jd, place),
        asyncio.to_thread(_nakshatra, jd, place),
        asyncio.to_thread(_vaara, jd),
        asyncio.to_thread(_masa, jd, place),
        asyncio.to_thread(_sunrise, jd, place),
        asyncio.to_thread(_sunset, jd, place),
        asyncio.to_thread(_chandra_rashi, jd),
    )

    tithi_num = int(tithi_result[0])
    tithi_end_dms = tithi_result[1] if len(tithi_result) > 1 else [0, 0, 0]
    
    nak_num = int(nakshatra_result[0])
    nak_end_dms = nakshatra_result[1] if len(nakshatra_result) > 1 else [0, 0, 0]
    
    vaara_val = int(vaara_result)
    masa_num = int(masa_result[0])

    paksha_key = _paksha_from_tithi(tithi_num)
    paksha_num = 1 if paksha_key == "shukla" else 2
    paksha_name = PAKSHA_NAMES.get(lang, PAKSHA_NAMES["en"])[paksha_key]

    tithi_in_paksha = _tithi_in_paksha(tithi_num)
    
    # Get festivals synchronously (it's a simple dict lookup)
    festivals = get_festivals(masa_num, paksha_num, tithi_in_paksha, lang)
    
    # Get sunrise/sunset times
    sunrise_hhmm = _dms_to_hhmm(sunrise_result[1])
    sunset_hhmm = _dms_to_hhmm(sunset_result[1])
    
    # Get nakshatra end time
    nak_end_time = _dms_to_hhmm(nak_end_dms)
    
    # Get chandra rashi name (no end time needed for monthly view)
    chandra_rashi_name = _get_name(chandra_rashi_num, RASHI_NAMES_EN, RASHI_NAMES_TE, lang)

    return {
        "date": f"{year:04d}-{month:02d}-{day:02d}",
        "tithi_name": _get_name(tithi_num, TITHI_NAMES_EN, TITHI_NAMES_TE, lang),
        "tithi_number": tithi_num,
        "tithi_end_time": _dms_to_hhmm(tithi_end_dms),
        "nakshatra_name": _get_name(nak_num, NAKSHATRA_NAMES_EN, NAKSHATRA_NAMES_TE, lang),
        "nakshatra_number": nak_num,
        "nakshatra_end_time": nak_end_time,
        "vaara": VAARA_NAMES_TE[vaara_val] if lang == "te" else VAARA_NAMES_EN[vaara_val],
        "paksha": paksha_name,
        "sunrise": sunrise_hhmm,
        "sunset": sunset_hhmm,
        "chandra_rashi": {
            "name": chandra_rashi_name,
            "end_time": None  # Skip end time calculation for monthly view (performance)
        },
        "moon_phase": tithi_num,
        "festivals": festivals,
    }


async def get_monthly_panchang(year: int, month: int, lat: float, lon: float,
                                tz_offset: float, lang: str = "en") -> dict:
    """Compute monthly panchang summaries for every day in the month.

    Args:
        year: Gregorian year.
        month: Gregorian month (1-12).
        lat: Latitude.
        lon: Longitude.
        tz_offset: Timezone offset in hours.
        lang: "en" or "te".

    Returns:
        Dict matching the MonthlyPanchangResponse schema.
    """
    # Check cache first
    cache_key = f"{year}|{month}|{lat:.4f}|{lon:.4f}|{tz_offset}|{lang}"
    if cache_key in _monthly_cache:
        if datetime.now() < _monthly_cache_ttl.get(cache_key, datetime.min):
            return _monthly_cache[cache_key]
        else:
            del _monthly_cache[cache_key]
            if cache_key in _monthly_cache_ttl: del _monthly_cache_ttl[cache_key]

    num_days = calendar.monthrange(year, month)[1]

    # Batch all days in parallel
    tasks = [
        _compute_day_summary(year, month, d, lat, lon, tz_offset, lang)
        for d in range(1, num_days + 1)
    ]
    days = await asyncio.gather(*tasks)

    # Determine masa from the first day for the header
    first_date = Date(year, month, 1)
    place = Place(lat, lon, tz_offset)
    jd_first = gregorian_to_jd(first_date)
    masa_result = await asyncio.to_thread(_masa, jd_first, place)
    masa_num = int(masa_result[0])
    masa_name = _get_name(masa_num, MASA_NAMES_EN, MASA_NAMES_TE, lang)

    kali, saka = await asyncio.to_thread(_elapsed_year, jd_first, masa_num)

    result = {
        "year": year,
        "month": month,
        "masa": masa_name,
        "samvat": saka,
        "days": list(days),
    }

    # Cache the result
    _monthly_cache[cache_key] = result
    _monthly_cache_ttl[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS)
    _save_cache_to_disk()
    
    return result
