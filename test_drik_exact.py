"""
test_drik_exact.py
==================
Test Drik Gochara implementation against exact DrikPanchang screenshots.
"""

from drik_gochara import generate_drik_gochara_chart, print_drik_chart
from drik_location_search import search_cities, get_timezone_offset


def test_march_19_2026():
    """
    Test case from DrikPanchang screenshot:
    Date: March 19, 2026 at 17:56:47 IST
    Location: Bhongir, India
    
    Expected house placements:
    - House 1: Ketu
    - House 7: Man, Bud, Rahu
    - House 8: Sur, Sha, Cha, Shu
    - House 11: Gur
    """
    
    print("=" * 100)
    print("TEST: DrikPanchang Screenshot - March 19, 2026 at 17:56:47 IST")
    print("=" * 100)
    print()
    
    # Search for Bhongir
    cities = search_cities("Bhongir")
    if not cities:
        print("ERROR: Bhongir not found in database")
        return False
    
    city = cities[0]
    print(f"Using city: {city['name']}")
    print(f"Coordinates: {city['latitude']}, {city['longitude']}")
    print(f"Timezone: {city['timezone']}")
    print()
    
    # Generate chart
    chart_data = generate_drik_gochara_chart(
        date_str="19/03/2026",
        time_str="17:56:47",
        place_name=city['name'],
        latitude=city['latitude'],
        longitude=city['longitude'],
        timezone_offset=get_timezone_offset(city['timezone']),
        ayanamsha="lahiri",
        rahu_type="mean",
    )
    
    # Print chart
    print_drik_chart(chart_data)
    
    # Verify house placements
    print("\n\nVERIFICATION:")
    print("-" * 100)
    
    chart = chart_data["chart"]
    
    expected = {
        1: ["Ketu"],
        7: ["Man", "Bud", "Rahu"],
        8: ["Sur", "Cha", "Shu", "Sha"],  # Order may vary
        11: ["Gur"],
    }
    
    all_pass = True
    
    for house, expected_planets in expected.items():
        actual_planets = [p for p in chart[house] if p != "Lagna"]  # Exclude Lagna for comparison
        
        # Check if all expected planets are present (order doesn't matter)
        expected_set = set(expected_planets)
        actual_set = set(actual_planets)
        
        if expected_set == actual_set:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_pass = False
        
        print(f"House {house:2d}: Expected {expected_planets}, Got {actual_planets} {status}")
    
    print("-" * 100)
    
    if all_pass:
        print("✅ ALL HOUSE PLACEMENTS MATCH DRIKPANCHANG!")
    else:
        print("❌ SOME HOUSE PLACEMENTS DON'T MATCH")
    
    return all_pass


def test_march_21_2026():
    """
    Test case from DrikPanchang screenshot:
    Date: March 21, 2026 at 17:36:56 IST
    Location: Bhongir, India
    
    Expected house placements:
    - House 1: Ketu
    - House 7: Man, Bud, Rahu
    - House 8: Sur, Shu, Sha
    - House 9: Cha
    - House 11: Gur
    """
    
    print("\n\n")
    print("=" * 100)
    print("TEST: DrikPanchang Screenshot - March 21, 2026 at 17:36:56 IST")
    print("=" * 100)
    print()
    
    # Search for Bhongir
    cities = search_cities("Bhongir")
    if not cities:
        print("ERROR: Bhongir not found in database")
        return False
    
    city = cities[0]
    
    # Generate chart
    chart_data = generate_drik_gochara_chart(
        date_str="21/03/2026",
        time_str="17:36:56",
        place_name=city['name'],
        latitude=city['latitude'],
        longitude=city['longitude'],
        timezone_offset=get_timezone_offset(city['timezone']),
        ayanamsha="lahiri",
        rahu_type="mean",
    )
    
    # Print chart
    print_drik_chart(chart_data)
    
    # Verify house placements
    print("\n\nVERIFICATION:")
    print("-" * 100)
    
    chart = chart_data["chart"]
    
    expected = {
        1: ["Ketu"],
        7: ["Man", "Bud", "Rahu"],
        8: ["Sur", "Shu", "Sha"],
        9: ["Cha"],
        11: ["Gur"],
    }
    
    all_pass = True
    
    for house, expected_planets in expected.items():
        actual_planets = [p for p in chart[house] if p != "Lagna"]
        
        expected_set = set(expected_planets)
        actual_set = set(actual_planets)
        
        if expected_set == actual_set:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_pass = False
        
        print(f"House {house:2d}: Expected {expected_planets}, Got {actual_planets} {status}")
    
    print("-" * 100)
    
    if all_pass:
        print("✅ ALL HOUSE PLACEMENTS MATCH DRIKPANCHANG!")
    else:
        print("❌ SOME HOUSE PLACEMENTS DON'T MATCH")
    
    return all_pass


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 98 + "╗")
    print("║" + " " * 25 + "DRIK GOCHARA TEST SUITE" + " " * 50 + "║")
    print("╚" + "=" * 98 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(("March 19, 2026", test_march_19_2026()))
    results.append(("March 21, 2026", test_march_21_2026()))
    
    # Summary
    print("\n\n")
    print("=" * 100)
    print("TEST SUMMARY")
    print("=" * 100)
    print()
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print()
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Implementation matches DrikPanchang exactly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
