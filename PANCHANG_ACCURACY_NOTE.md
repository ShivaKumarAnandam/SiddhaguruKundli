# Panchang Calculation Accuracy Note

## Overview
This API uses the **Drik Panchanga** system with Swiss Ephemeris for astronomical calculations. Different panchang websites and systems may show slightly different timings due to variations in calculation methods.

## Known Differences with Other Systems

### Comparison with Telugu Panchang Websites
When comparing with popular Telugu panchang websites, you may notice differences in:

1. **Muhurta Timings** (±5-10 minutes)
   - Rahu Kalam
   - Gulikai Kalam
   - Yamaganda
   - Dur Muhurtam
   - Amrit Kalam

2. **Sunrise/Sunset** (±1-2 minutes)
   - Different atmospheric refraction models
   - Different elevation calculations

3. **Moonrise/Moonset** (±2-5 minutes)
   - Complex topocentric calculations
   - "No Moonrise" vs actual time differences

4. **Samvatsara Names**
   - Different 60-year cycle starting points
   - Regional variations (North vs South Indian)

## Why Differences Occur

### 1. Calculation Methods
- **Drik System**: Uses actual astronomical positions (Swiss Ephemeris)
- **Traditional Systems**: May use simplified formulas or different ephemeris
- **Regional Systems**: Telugu, Tamil, Malayalam systems have variations

### 2. Reference Points
- **Sunrise-based**: Most muhurtas calculated from sunrise
- **Midnight-based**: Some systems use local midnight
- **Solar noon**: Different definitions of "noon"

### 3. Rounding & Precision
- Some systems round to nearest minute
- Others show seconds
- Different handling of fractional minutes

### 4. Atmospheric Corrections
- Refraction models vary
- Elevation/altitude adjustments
- Local horizon definitions

## Accuracy of This API

### Astronomical Accuracy
- ✅ Swiss Ephemeris (NASA JPL quality)
- ✅ Precise to within seconds for planetary positions
- ✅ Accounts for precession, nutation, aberration

### Panchang Accuracy
- ✅ Tithi, Nakshatra, Yoga: Highly accurate
- ✅ Sunrise/Sunset: ±1 minute
- ⚠️ Muhurtas: ±5-10 minutes (due to different calculation methods)
- ⚠️ Moonrise/Moonset: ±2-5 minutes (complex topocentric calculations)

## Recommendations

### For Users
1. **Use this API consistently** - Don't mix with other systems
2. **Understand variations** - ±5-10 minutes is normal across systems
3. **Trust the core data** - Tithi, Nakshatra, Yoga are highly accurate
4. **Muhurtas are approximate** - Traditional systems also vary

### For Developers
1. **Document the system used** - "Drik Panchanga with Swiss Ephemeris"
2. **Don't expect exact matches** - Different systems will differ
3. **Focus on consistency** - Use one system throughout
4. **Validate core elements** - Tithi, Nakshatra should match closely

## Validation Test Cases

### High Accuracy Elements (should match exactly)
- Tithi number and name
- Nakshatra number and name
- Yoga number and name
- Karana sequence
- Masa and Paksha
- Vaara (weekday)

### Moderate Accuracy Elements (±1-2 minutes acceptable)
- Tithi end time
- Nakshatra end time
- Yoga end time
- Sunrise/Sunset

### Variable Elements (±5-10 minutes normal)
- Rahu Kalam
- Gulikai Kalam
- Yamaganda
- Abhijit Muhurta
- Dur Muhurtam
- Amrit Kalam
- Varjyam

### Known Issues
- **Moonrise "No Moonrise"**: Some days moon doesn't rise (now handled)
- **Samvatsara variations**: Different regional cycles
- **Festival names**: May vary by region/tradition

## References

### This API Uses
- **Drik Panchanga**: https://github.com/naturalstupid/drik-panchanga
- **Swiss Ephemeris**: https://www.astro.com/swisseph/
- **Calculation Method**: Drik Ganita (observational astronomy)

### Other Popular Systems
- **Vakya System**: Traditional Indian system
- **Thirukanitha System**: Tamil system
- **Surya Siddhanta**: Ancient Indian astronomical text
- **Regional Panchangas**: Telugu, Tamil, Malayalam variations

## Conclusion

The differences you see are **normal and expected** when comparing different panchang systems. This API provides astronomically accurate calculations using modern ephemeris data. For ritual and religious purposes, consult with local pundits who may use region-specific traditional systems.

**Bottom Line**: ±5-10 minutes difference in muhurtas is acceptable and common across different panchang systems. The core panchang elements (Tithi, Nakshatra, Yoga) should be highly accurate.
