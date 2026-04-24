"""
Test script to compare panchang API output with expected values.
This helps identify specific differences and their magnitudes.
"""

import requests
import json
from datetime import datetime

# Expected values from the reference website (Telugu Panchang)
EXPECTED = {
    "date": "2026-04-17",
    "sunrise": "05:59",
    "sunset": "18:33",
    "moonrise": "No Moonrise",
    "moonset": "18:26",
    "samvatsara": "Parabhava",
    "masa": "Chaitra",
    "paksha": "Krishna Paksha",
    "tithi": {
        "name": "Amavasya",
        "end_time": "17:21"
    },
    "nakshatra": {
        "name": "Revati",
        "end_time": "12:02"
    },
    "yoga": {
        "name": "Vaidhriti",
        "end_time": "07:22",
        "next_name": "Vishkambha",
        "next_end_time": "03:45"  # Next day
    },
    "karana": [
        {"name": "Chatushpada", "end_time": "06:49"},
        {"name": "Naga", "end_time": "17:21"},
        {"name": "Kinstughna", "end_time": "03:47"}  # Next day
    ],
    "vaara": "Friday",
    "sun_rashi": "Mesha",
    "chandra_rashi": {
        "name": "Meena",
        "end_time": "12:02"
    },
    "muhurtas": {
        "rahu_kalam": {"start": "10:42", "end": "12:16"},
        "gulikai_kalam": {"start": "07:33", "end": "09:07"},
        "yamaganda": {"start": "15:24", "end": "16:58"},
        "abhijit_muhurta": {"start": "11:51", "end": "12:41"},
        "dur_muhurtam": [
            {"start": "08:30", "end": "09:20"},
            {"start": "12:41", "end": "13:31"}
        ],
        "amrit_kalam": [
            {"start": "09:50", "end": "11:18"},
            {"start": "03:12", "end": "04:39"}  # Next day
        ]
    }
}

def time_to_minutes(time_str):
    """Convert HH:MM to minutes since midnight."""
    if not time_str or time_str == "No Moonrise" or time_str == "No Moonset":
        return None
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except:
        return None

def time_diff_minutes(time1, time2):
    """Calculate difference in minutes between two times."""
    m1 = time_to_minutes(time1)
    m2 = time_to_minutes(time2)
    if m1 is None or m2 is None:
        return None
    return abs(m1 - m2)

def compare_times(label, expected, actual):
    """Compare two times and print the difference."""
    diff = time_diff_minutes(expected, actual)
    if diff is None:
        status = "⚠️ MISMATCH" if expected != actual else "✅ MATCH"
        print(f"  {label:30s}: Expected={expected:10s} Actual={actual:10s} {status}")
    elif diff == 0:
        print(f"  {label:30s}: {actual:10s} ✅ EXACT MATCH")
    elif diff <= 2:
        print(f"  {label:30s}: {actual:10s} ✅ CLOSE (±{diff}min)")
    elif diff <= 10:
        print(f"  {label:30s}: {actual:10s} ⚠️ ACCEPTABLE (±{diff}min)")
    else:
        print(f"  {label:30s}: {actual:10s} ❌ SIGNIFICANT DIFF (±{diff}min)")

def test_panchang_api():
    """Test the panchang API and compare with expected values."""
    
    # API endpoint
    url = "http://localhost:8008/api/panchang/daily"
    
    # Request payload (Hyderabad coordinates)
    payload = {
        "date": "2026-04-17",
        "latitude": 17.385,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata"
    }
    
    print("=" * 80)
    print("PANCHANG API COMPARISON TEST")
    print("=" * 80)
    print(f"Date: {payload['date']}")
    print(f"Location: Hyderabad, India ({payload['latitude']}, {payload['longitude']})")
    print(f"Timezone: {payload['timezone']}")
    print("=" * 80)
    
    try:
        # Make API request
        response = requests.post(url, json=payload)
        response.raise_for_status()
        actual = response.json()
        
        # Save response for inspection
        with open("test_panchang_output.json", "w") as f:
            json.dump(actual, f, indent=2)
        print("✅ API Response saved to: test_panchang_output.json\n")
        
        # Compare basic info
        print("📅 BASIC INFORMATION")
        print(f"  Date:                         {actual.get('date')} {'✅' if actual.get('date') == EXPECTED['date'] else '❌'}")
        print(f"  Vaara:                        {actual.get('vaara')} {'✅' if actual.get('vaara') == EXPECTED['vaara'] else '❌'}")
        print(f"  Masa:                         {actual.get('masa')} {'✅' if actual.get('masa') == EXPECTED['masa'] else '❌'}")
        print(f"  Paksha:                       {actual.get('paksha')} {'✅' if actual.get('paksha') == EXPECTED['paksha'] else '❌'}")
        print(f"  Samvatsara:                   {actual.get('samvatsara')} {'⚠️' if actual.get('samvatsara') != EXPECTED['samvatsara'] else '✅'}")
        if actual.get('samvatsara') != EXPECTED['samvatsara']:
            print(f"    Expected: {EXPECTED['samvatsara']}, Got: {actual.get('samvatsara')}")
        print()
        
        # Compare solar/lunar times
        print("🌅 SOLAR & LUNAR TIMES")
        compare_times("Sunrise", EXPECTED['sunrise'], actual.get('sunrise'))
        compare_times("Sunset", EXPECTED['sunset'], actual.get('sunset'))
        compare_times("Moonrise", EXPECTED['moonrise'], actual.get('moonrise'))
        compare_times("Moonset", EXPECTED['moonset'], actual.get('moonset'))
        print()
        
        # Compare panchang elements
        print("📊 PANCHANG ELEMENTS")
        
        # Tithi
        tithi = actual.get('tithi', {})
        print(f"  Tithi:                        {tithi.get('name')} {'✅' if tithi.get('name') == EXPECTED['tithi']['name'] else '❌'}")
        compare_times("  Tithi End Time", EXPECTED['tithi']['end_time'], tithi.get('end_time'))
        
        # Nakshatra
        nakshatra = actual.get('nakshatra', {})
        print(f"  Nakshatra:                    {nakshatra.get('name')} {'✅' if nakshatra.get('name') == EXPECTED['nakshatra']['name'] else '❌'}")
        compare_times("  Nakshatra End Time", EXPECTED['nakshatra']['end_time'], nakshatra.get('end_time'))
        
        # Yoga
        yoga = actual.get('yoga', {})
        print(f"  Yoga:                         {yoga.get('name')} {'✅' if yoga.get('name') == EXPECTED['yoga']['name'] else '❌'}")
        compare_times("  Yoga End Time", EXPECTED['yoga']['end_time'], yoga.get('end_time'))
        if yoga.get('next_name'):
            print(f"  Next Yoga:                    {yoga.get('next_name')} {'✅' if yoga.get('next_name') == EXPECTED['yoga']['next_name'] else '❌'}")
        
        # Karana
        karana_list = actual.get('karana', [])
        print(f"  Karana Count:                 {len(karana_list)} {'✅' if len(karana_list) == len(EXPECTED['karana']) else '❌'}")
        for i, (exp_k, act_k) in enumerate(zip(EXPECTED['karana'], karana_list)):
            print(f"  Karana {i+1}:                     {act_k.get('name')} {'✅' if act_k.get('name') == exp_k['name'] else '❌'}")
            if act_k.get('end_time'):
                compare_times(f"    End Time", exp_k['end_time'], act_k.get('end_time'))
        print()
        
        # Compare rashis
        print("♈ RASHI (ZODIAC)")
        print(f"  Sun Rashi:                    {actual.get('sun_rashi')} {'✅' if actual.get('sun_rashi') == EXPECTED['sun_rashi'] else '❌'}")
        chandra = actual.get('chandra_rashi', {})
        print(f"  Chandra Rashi:                {chandra.get('name')} {'✅' if chandra.get('name') == EXPECTED['chandra_rashi']['name'] else '❌'}")
        compare_times("  Chandra Rashi End", EXPECTED['chandra_rashi']['end_time'], chandra.get('end_time'))
        print()
        
        # Compare muhurtas
        print("⏰ MUHURTA TIMINGS")
        muhurtas = actual.get('muhurtas', {})
        
        # Rahu Kalam
        rahu = muhurtas.get('rahu_kalam', {})
        compare_times("Rahu Kalam Start", EXPECTED['muhurtas']['rahu_kalam']['start'], rahu.get('start'))
        compare_times("Rahu Kalam End", EXPECTED['muhurtas']['rahu_kalam']['end'], rahu.get('end'))
        
        # Gulikai Kalam
        gulikai = muhurtas.get('gulikai_kalam', {})
        compare_times("Gulikai Kalam Start", EXPECTED['muhurtas']['gulikai_kalam']['start'], gulikai.get('start'))
        compare_times("Gulikai Kalam End", EXPECTED['muhurtas']['gulikai_kalam']['end'], gulikai.get('end'))
        
        # Yamaganda
        yama = muhurtas.get('yamaganda', {})
        compare_times("Yamaganda Start", EXPECTED['muhurtas']['yamaganda']['start'], yama.get('start'))
        compare_times("Yamaganda End", EXPECTED['muhurtas']['yamaganda']['end'], yama.get('end'))
        
        # Abhijit
        abhijit = muhurtas.get('abhijit_muhurta', {})
        compare_times("Abhijit Start", EXPECTED['muhurtas']['abhijit_muhurta']['start'], abhijit.get('start'))
        compare_times("Abhijit End", EXPECTED['muhurtas']['abhijit_muhurta']['end'], abhijit.get('end'))
        
        # Dur Muhurtam
        dur_list = muhurtas.get('dur_muhurtam', [])
        print(f"  Dur Muhurtam Count:           {len(dur_list)} {'✅' if len(dur_list) == len(EXPECTED['muhurtas']['dur_muhurtam']) else '❌'}")
        for i, (exp_d, act_d) in enumerate(zip(EXPECTED['muhurtas']['dur_muhurtam'], dur_list)):
            compare_times(f"  Dur Muhurtam {i+1} Start", exp_d['start'], act_d.get('start'))
            compare_times(f"  Dur Muhurtam {i+1} End", exp_d['end'], act_d.get('end'))
        
        # Amrit Kalam
        amrit = muhurtas.get('amrit_kalam', {})
        compare_times("Amrit Kalam Start", EXPECTED['muhurtas']['amrit_kalam'][0]['start'], amrit.get('start'))
        compare_times("Amrit Kalam End", EXPECTED['muhurtas']['amrit_kalam'][0]['end'], amrit.get('end'))
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("✅ EXACT MATCH    : Times match exactly")
        print("✅ CLOSE          : Difference ≤ 2 minutes (excellent)")
        print("⚠️ ACCEPTABLE     : Difference ≤ 10 minutes (normal for different systems)")
        print("❌ SIGNIFICANT    : Difference > 10 minutes (investigate)")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to API. Is the server running?")
        print("   Start server with: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_panchang_api()
