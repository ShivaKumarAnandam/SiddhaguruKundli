  # Siddhaguru Kundli - Complete Technical Documentation
  ## Comprehensive Process Flow for All Features

  **Last Updated**: March 15, 2026  
  **Version**: 2.0.0  
  **Author**: Technical Documentation Team

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Architecture Diagram](#3-architecture-diagram)
4. [Feature 1: Nakshatra Calculator (Traditional)](#4-feature-1-nakshatra-calculator-traditional)
5. [Feature 2: Nakshatra Calculator AI](#5-feature-2-nakshatra-calculator-ai)
6. [Feature 3: Full Horoscope (7-Day Panchang)](#6-feature-3-full-horoscope-7-day-panchang)
7. [Feature 4: Full Horoscope AI](#7-feature-4-full-horoscope-ai)
8. [Feature 5: Gochara Transit Chart AI](#8-feature-5-gochara-transit-chart-ai)
9. [Feature 6: Name Nakshatra Lookup](#9-feature-6-name-nakshatra-lookup)
10. [Supporting Systems](#10-supporting-systems)
11. [Performance Optimizations](#11-performance-optimizations)
12. [Error Handling & Quota Management](#12-error-handling--quota-management)
13. [API Reference](#13-api-reference)
14. [Deployment Guide](#14-deployment-guide)

---

## 1. System Overview

### Purpose
Siddhaguru Kundli is a comprehensive Vedic astrology platform that provides:
- Traditional astronomical calculations using Swiss Ephemeris
- AI-powered predictions using Google Gemini 2.5 Flash
- Name-based nakshatra lookup (108 Telugu syllables)
- Transit chart generation with South Indian style visualization

### Key Features
1. **Nakshatra Calculator** - Birth star calculation with 27 nakshatras
2. **Full Horoscope** - 7-day Panchang predictions (Tithi, Karana, Yoga)
3. **Gochara Chart** - Current planetary transits with AI interpretations
4. **Name Lookup** - Find Rashi & Nakshatra from name syllables
5. **AI Versions** - Gemini-powered alternatives for all calculations
6. **Place Search** - 11M+ places worldwide with autocomplete

### User Base
- Vedic astrology enthusiasts
- Astrologers and practitioners
- Individuals seeking birth chart information
- Researchers studying Vedic astrology

---

## 2. Technology Stack

### Backend (Python 3.8+)
```
FastAPI 0.104.1          - Modern async web framework
pyswisseph 2.10.3.2      - Swiss Ephemeris astronomical calculations
google-genai 0.3.0       - Google Gemini AI integration
Pillow 10.2.0            - Image generation for charts
pytz 2023.3              - Timezone handling
httpx 0.25.1             - Async HTTP client
python-dotenv 1.0.0      - Environment variable management
pydantic 2.5.0           - Data validation
```

### Frontend (React 18+)
```
React 18.2.0             - UI framework
Vite 5.0.8               - Build tool and dev server
Custom Hooks             - useApiLockout for quota management
localStorage             - Cross-page state persistence
CSS3                     - Styling with animations
```

### External APIs
```
Google Gemini 2.5 Flash  - AI predictions (15 RPM free tier)
GeoNames API             - Place search (11M+ locations)
Photon API               - Fallback geocoding (OpenStreetMap)
```

### Development Tools
```
uvicorn                  - ASGI server
npm/vite                 - Frontend tooling
Git                      - Version control
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER (React)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Nakshatra │  │Horoscope │  │ Gochara  │  │   Name   │   │
│  │Calculator│  │  (7-Day) │  │  Chart   │  │ Nakshatra│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        │ HTTP POST   │ HTTP POST   │ HTTP POST   │ HTTP POST
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (main.py)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Endpoints (7 total)                              │  │
│  │  /api/nakshatra, /api/horoscope, /api/gochara, etc.  │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐     │
│  │ geocode  │        │ephemeris │        │  Gemini  │     │
│  │  .py     │        │   .py    │        │   API    │     │
│  └────┬─────┘        └────┬─────┘        └────┬─────┘     │
└───────┼──────────────────┼──────────────────┼─────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   GeoNames   │  │    Swiss     │  │    Google    │
│     API      │  │  Ephemeris   │  │   Gemini     │
│ (11M places) │  │  (Moshier)   │  │ 2.5 Flash    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Data Flow
1. User fills form in React component
2. Frontend validates input and sends HTTP POST
3. Backend receives request, validates with Pydantic
4. Geocoding resolves place to coordinates
5. Swiss Ephemeris calculates planetary positions
6. Nakshatra/Horoscope logic processes data
7. (Optional) Gemini AI generates predictions
8. Response formatted as JSON
9. Frontend displays results with styling

---

## 4. Feature 1: Nakshatra Calculator (Traditional)

### Overview
Calculates birth nakshatra, rashi, and pada using Swiss Ephemeris astronomical calculations.

### User Journey
```
User clicks "Rashi & Nakshatra" 
  → Form displays
  → User enters: Name, Gender, DOB, Time, Place
  → Place autocomplete suggests locations
  → User selects place from dropdown
  → User clicks "Calculate Nakshatra"
  → Loading animation shows
  → Results display with all attributes
```

### Technical Process (Step-by-Step)

#### Step 1: Frontend Form Submission
**File**: `SiddhaguruKundliUI/src/components/NakshatraCalculator.jsx`
**Lines**: 80-120

**Process**:
1. User fills form fields
2. Frontend validates all required fields
3. Builds request body with birth details
4. If place selected from dropdown, includes lat/lon/timezone
5. Sends POST request to `/api/nakshatra`

**Request Body**:
```json
{
  "name": "Shiva Kumar",
  "gender": "Male",
  "date": "1999-11-08",
  "hour": 7,
  "minute": 15,
  "ampm": "PM",
  "place": "Nizamabad, Telangana, India",
  "latitude": 18.6725,
  "longitude": 78.0941,
  "timezone": "Asia/Kolkata"
}
```

#### Step 2: Backend Endpoint Processing
**File**: `main.py`
**Lines**: 175-200
**Endpoint**: `POST /api/nakshatra`

**Process**:
1. Receives BirthDetails model (Pydantic validation)
2. Calls `resolve_geo()` to get coordinates
3. Parses date string to year/month/day
4. Converts 12-hour time to 24-hour format
5. Calculates Julian Day using `local_to_julian_day()`
6. Gets Moon's longitude using `get_moon_longitude()`
7. Calculates nakshatra using `calculate_nakshatra()`
8. Returns combined result as JSON

**Code Flow**:
```python
geo = resolve_geo(details)  # Get lat/lon/timezone
year, month, day = map(int, details.date.split("-"))
hour24, minute = parse_to_24h(details.hour, details.minute, details.ampm)
jd = local_to_julian_day(year, month, day, hour24, minute, geo["timezone"])
moon_lon, moon_speed = get_moon_longitude(jd)
nk = calculate_nakshatra(moon_lon, moon_speed)
return {**input_details, **nk}
```

#### Step 3: Geographic Coordinate Resolution
**File**: `geocode.py`
**Function**: `geocode_place(place_name: str)`

**Process**:
1. Checks if `GEONAMES_USERNAME` environment variable is set
2. If yes → Uses GeoNames API (requires free account)
3. If no → Uses Photon API (OpenStreetMap, no account)
4. Searches for place name
5. Returns first match with coordinates and timezone

**GeoNames API**:
- 11M+ places worldwide
- Includes villages, hamlets, towns, cities
- Requires free username from geonames.org
- Returns: lat, lon, timezone, display_name

**Photon API**:
- OpenStreetMap data
- No registration required
- Fallback option
- Returns: lat, lon, timezone, display_name

#### Step 4: Julian Day Calculation
**File**: `ephemeris.py`
**Function**: `local_to_julian_day(year, month, day, hour, minute, timezone_str)`

**Purpose**: Convert local date/time to Julian Day (JD) in UTC

**Process**:
1. Create timezone-aware datetime object
2. Localize to specified timezone (e.g., Asia/Kolkata)
3. Convert to UTC
4. Calculate Julian Day using Swiss Ephemeris `swe.julday()`
5. Return JD as float

**Example**:
```
Input: 1999-11-08, 19:15, Asia/Kolkata
Local: 1999-11-08 19:15:00 IST (UTC+5:30)
UTC:   1999-11-08 13:45:00 UTC
JD:    2451492.073611
```

**What is Julian Day?**
- Continuous count of days since noon UTC on January 1, 4713 BCE
- Used in astronomy for precise time calculations
- Eliminates calendar complexities (leap years, etc.)

#### Step 5: Moon Longitude Calculation
**File**: `ephemeris.py`
**Function**: `get_moon_longitude(julian_day: float)`

**Purpose**: Calculate Moon's sidereal longitude using Lahiri ayanamsa

**Process**:
1. Set ayanamsa to SIDM_LAHIRI (standard for Vedic astrology)
2. Set calculation flags:
   - FLG_MOSEPH: Use built-in Moshier ephemeris (no external files)
   - FLG_SIDEREAL: Sidereal zodiac (Vedic), not tropical (Western)
   - FLG_SPEED: Include speed calculation
3. Call `swe.calc_ut()` for Moon position
4. Extract longitude (0-360°) and speed (degrees/day)
5. Return both values

**Example**:
```
JD: 2451492.073611
Moon Longitude: 67.5432° (in Gemini)
Moon Speed: 13.2456°/day (direct motion)
```

**Ayanamsa Explained**:
- Difference between tropical and sidereal zodiac
- Lahiri ayanamsa is standard in Indian astrology
- Currently ~24° difference
- Accounts for precession of equinoxes

#### Step 6: Nakshatra Calculation
**File**: `nakshatra.py`
**Function**: `calculate_nakshatra(moon_lon: float, moon_speed: float)`

**Purpose**: Calculate nakshatra, pada, and rasi from Moon's longitude

**Constants**:
```python
NAKSHATRA_SPAN = 360 / 27  # 13.3333° per nakshatra
PADA_SPAN = NAKSHATRA_SPAN / 4  # 3.3333° per pada
```

**Process**:
1. Calculate nakshatra index: `int(moon_lon / 13.3333) % 27` → 0-26
2. Calculate pada: `int((moon_lon % 13.3333) / 3.3333) + 1` → 1-4
3. Calculate rasi index: `int(moon_lon / 30) % 12` → 0-11
4. Lookup nakshatra data from NAKSHATRAS array (27 elements)
5. Calculate nakshatra range (start and end longitude)
6. Build result dictionary with all attributes

**Example Calculation**:
```
Moon Longitude: 67.5432°

Nakshatra Index: 67.5432 / 13.3333 = 5.065 → 5 (Ardra)
Pada: (67.5432 % 13.3333) / 3.3333 = 0.2596 → 1 (1st pada)
Rasi Index: 67.5432 / 30 = 2.251 → 2 (Mithuna/Gemini)

Result:
- Nakshatra: Ardra 1st Pada
- Chandra Rasi: Mithuna (Gemini)
- Deity: Rudra
- Gana: Manushya
- Animal: Dog
- Color: Green
- Birthstone: Emerald
- Syllables: ["Ku", "Gha", "Ng", "Chha"]
- Best Direction: West
- Symbol: Teardrop
```

**Nakshatra Data Structure**:
Each of 27 nakshatras has:
- name, deity, gana, animal, color, stone
- syllables (4 per nakshatra)
- direction, symbol, zodiac

#### Step 7: Response to Frontend
**Format**: JSON with all birth details + nakshatra attributes

```json
{
  "name": "Shiva Kumar",
  "gender": "Male",
  "date": "1999-11-08",
  "time": "7:15 PM",
  "place": "Nizamabad, Telangana, India",
  "timezone": "Asia/Kolkata",
  "latitude": 18.6725,
  "longitude": 78.0941,
  "julian_day": 2451492.073611,
  "nakshatra": "Ardra",
  "pada": 1,
  "pada_label": "1st",
  "chandra_rasi": "Mithuna (Gemini)",
  "deity": "Rudra",
  "gana": "Manushya",
  "animal_sign": "Dog",
  "color": "Green",
  "birthstone": "Emerald",
  "syllables": ["Ku", "Gha", "Ng", "Chha"],
  "best_direction": "West",
  "symbol": "Teardrop",
  "zodiac_sign": "Gemini",
  "moon_longitude": 67.5432,
  "nakshatra_range": "66.6667° – 80.0000°",
  "moon_speed_deg_per_day": 13.2456
}
```

#### Step 8: Frontend Display
**File**: `NakshatraCalculator.jsx`
**Lines**: 150-180

**Process**:
1. Receives JSON response
2. Stores in `result` state
3. Renders result card with grid layout
4. Highlights important fields (nakshatra, rasi)
5. Displays all attributes in organized sections

**Performance Metrics**:
- Total Time: 2-3 seconds
- Breakdown:
  - Frontend validation: <50ms
  - Network request: 100-200ms
  - Geocoding (if needed): 500-1000ms
  - Swiss Ephemeris: 50-100ms
  - Nakshatra logic: <10ms
  - Response formatting: <10ms
  - Frontend rendering: 50-100ms

---

## 5. Feature 2: Nakshatra Calculator AI

### Overview
AI-powered nakshatra calculation using Google Gemini 2.5 Flash. Returns same format as traditional calculator but uses AI instead of astronomical calculations.

### Key Differences from Traditional
1. Uses Gemini API instead of Swiss Ephemeris
2. AI generates all values (not real astronomical data)
3. Includes global quota management (15 RPM limit)
4. 64-second lockout on quota exhaustion
5. Cross-page lockout using localStorage

### Technical Process

#### Step 1: Global Lockout Hook
**File**: `SiddhaguruKundliUI/src/hooks/useApiLockout.js`

**Purpose**: Prevent quota exhaustion by locking ALL AI features when limit is hit

**How It Works**:
1. Uses `localStorage` to share state across all AI pages
2. Stores unlock timestamp (not duration)
3. Checks every second if still locked
4. Updates countdown timer in all components
5. Auto-unlocks when time expires
6. Works across browser tabs and page refreshes

**Code**:
```javascript
export function useApiLockout() {
  const [isLocked, setIsLocked] = useState(false)
  const [timeLeft, setTimeLeft] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      const unlockTime = localStorage.getItem('ai_unlock_time')
      if (unlockTime) {
        const remaining = parseInt(unlockTime) - Date.now()
        if (remaining > 0) {
          setIsLocked(true)
          setTimeLeft(Math.ceil(remaining / 1000))
        } else {
          setIsLocked(false)
          setTimeLeft(0)
          localStorage.removeItem('ai_unlock_time')
        }
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const triggerLockout = () => {
    const lockoutDuration = 64 * 1000  // 64 seconds
    localStorage.setItem('ai_unlock_time', Date.now() + lockoutDuration)
    setIsLocked(true)
    setTimeLeft(64)
  }

  return { isLocked, timeLeft, triggerLockout }
}
```
