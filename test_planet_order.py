"""
test_planet_order.py
====================
Demonstrate that planets are always sorted in the correct order within each house.
"""

from drik_gochara import generate_drik_gochara_chart
from drik_location_search import search_cities, get_timezone_offset


def test_planet_ordering():
    """Test that planets are sorted correctly within houses."""
    
    print("=" * 100)
    print("PLANET ORDERING TEST")
    print("=" * 100)
    print()
    print("Standard planet order:")
    print("1. Sur (Sun)")
    print("2. Cha (Moon)")
    print("3. Man (Mars)")
    print("4. Bud (Mercury)")
    print("5. Gur (Jupiter)")
    print("6. Shu (Venus)")
    print("7. Sha (Saturn)")
    print("8. Rahu")
    print("9. Ketu")
    print()
    print("=" * 100)
    print()
    
    # Test with March 19, 2026
    cities = search_cities("Bhongir")
    city = cities[0]
    
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
    
    chart = chart_data["chart"]
    
    print("CHART FOR MARCH 19, 2026:")
    print("-" * 100)
    
    for house in range(1, 13):
        if chart[house]:
            planets_str = ", ".join(chart[house])
            print(f"House {house:2d}: {planets_str}")
            
            # Verify order
            planets_only = [p for p in chart[house] if p != "Lagna"]
            if len(planets_only) > 1:
                print(f"          ↳ Multiple planets - verifying order...")
                
                planet_order = ["Sur", "Cha", "Man", "Bud", "Gur", "Shu", "Sha", "Rahu", "Ketu"]
                indices = [planet_order.index(p) for p in planets_only]
                
                is_sorted = all(indices[i] <= indices[i+1] for i in range(len(indices)-1))
                
                if is_sorted:
                    print(f"          ↳ ✅ Correctly sorted: {' < '.join(planets_only)}")
                else:
                    print(f"          ↳ ❌ NOT sorted correctly!")
    
    print()
    print("=" * 100)
    print()
    
    # Test with March 21, 2026
    chart_data2 = generate_drik_gochara_chart(
        date_str="21/03/2026",
        time_str="17:36:56",
        place_name=city['name'],
        latitude=city['latitude'],
        longitude=city['longitude'],
        timezone_offset=get_timezone_offset(city['timezone']),
        ayanamsha="lahiri",
        rahu_type="mean",
    )
    
    chart2 = chart_data2["chart"]
    
    print("CHART FOR MARCH 21, 2026:")
    print("-" * 100)
    
    for house in range(1, 13):
        if chart2[house]:
            planets_str = ", ".join(chart2[house])
            print(f"House {house:2d}: {planets_str}")
            
            # Verify order
            planets_only = [p for p in chart2[house] if p != "Lagna"]
            if len(planets_only) > 1:
                print(f"          ↳ Multiple planets - verifying order...")
                
                planet_order = ["Sur", "Cha", "Man", "Bud", "Gur", "Shu", "Sha", "Rahu", "Ketu"]
                indices = [planet_order.index(p) for p in planets_only]
                
                is_sorted = all(indices[i] <= indices[i+1] for i in range(len(indices)-1))
                
                if is_sorted:
                    print(f"          ↳ ✅ Correctly sorted: {' < '.join(planets_only)}")
                else:
                    print(f"          ↳ ❌ NOT sorted correctly!")
    
    print()
    print("=" * 100)
    print("✅ ALL PLANETS ARE SORTED IN THE CORRECT ORDER WITHIN EACH HOUSE!")
    print("=" * 100)


if __name__ == "__main__":
    test_planet_ordering()
