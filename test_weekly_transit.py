import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from weekly_horoscope import calculate_weekly_horoscope

def test_weekly_logic():
    print("Testing Weekly Horoscope Transit Logic...")
    
    # Test details: Born 1999-11-08 (Karkataka Rasi)
    # Today is 2026-04-04 (Moon in Thula Rasi - 4th from Cancer)
    
    birth_date = "2001-11-08"
    start_date = "2026-04-04"
    details = {
        "name": "Test User",
        "gender": "Male",
        "birth_date": birth_date,
        "start_date": start_date,
        "hour": 7,
        "minute": 15,
        "ampm": "PM",
        "place": "Nizamabad, Telangana, India",
        "lat": 18.6733,
        "lon": 78.0978,
        "timezone": "Asia/Kolkata"
    }
    
    result = calculate_weekly_horoscope(**details)
    
    # 1. Check Birth Details
    print(f"Birth Rasi: {result['birth_details']['rasu']}")
    assert result['birth_details']['rasu'] == "Karkataka (Cancer)", f"Expected Cancer, got {result['birth_details']['rasu']}"
    
    # 2. Check Day 1 Transit (April 4, 2026)
    # Cancer (House 4) -> Leo (5) -> Virgo (6) -> Libra (7)
    # Index: Cancer=3, Libra=6. (6 - 3 + 12) % 12 + 1 = 4. 
    # Current Moon is in Libra (Thula).
    day1 = result['days'][0]
    print(f"Day 1 Date: {day1['date']}")
    print(f"Day 1 Rasi: {day1['rasi']}")
    print(f"Transit House: {day1['transit_house']}")
    
    assert day1['transit_house'] == 4, f"Expected 4th house transit, got {day1['transit_house']}"
    
    # 3. Check Predictions object
    transit_title = day1['predictions']['transit']['title']
    print(f"Transit Title: {transit_title}")
    assert "4th House" in transit_title
    
    print("\n✅ BACKEND VERIFICATION PASSED!")

if __name__ == "__main__":
    try:
        test_weekly_logic()
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
