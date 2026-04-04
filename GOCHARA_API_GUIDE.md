# Gochara (Transit Chart) API Guide

This document explains all Gochara chart endpoints available in the API.

---

## Overview

You now have **TWO different Gochara implementations**:

1. **Drik Panchanga Style** (`/api/gochara/chart`) - Uses drik-panchanga methodology
2. **South Indian Style** (`/api/gochara/south-indian`) - Uses your existing nakshatra/horoscope calculation logic

---

## 1. DRIK PANCHANGA STYLE ENDPOINTS

### 1.1 Search Cities
**Endpoint**: `GET /api/gochara/search`

**Query Parameters**:
```
q: Bhongir
max_results: 10
```

**Example**:
```
GET /api/gochara/search?q=Bhongir&max_results=10
```

**Response**:
```json
{
  "query": "Bhongir",
  "count": 1,
  "results": [
    {
      "name": "Bhongir",
      "latitude": 17.51083,
      "longitude": 78.88889,
      "timezone": "Asia/Kolkata"
    }
  ]
}
```

---

### 1.2 Generate Drik Chart - GET
**Endpoint**: `GET /api/gochara/chart`

**Query Parameters**:
```
date: 21/03/2026
time: 11:21:10
place: Bhongir
ayanamsha: lahiri
rahu_type: mean
```

**Example**:
```
GET /api/gochara/chart?date=21/03/2026&time=11:21:10&place=Bhongir&ayanamsha=lahiri&rahu_type=mean
```

---

### 1.3 Generate Drik Chart - POST
**Endpoint**: `POST /api/gochara/chart`

**Request Body**:
```json
{
  "date": "21/03/2026",
  "time": "11:21:10",
  "place": "Bhongir",
  "ayanamsha": "lahiri",
  "rahu_type": "mean"
}
```

**With Optional Coordinates** (faster):
```json
{
  "date": "21/03/2026",
  "time": "11:21:10",
  "place": "Bhongir",
  "latitude": 17.51083,
  "longitude": 78.88889,
  "timezone_offset": 5.5,
  "ayanamsha": "lahiri",
  "rahu_type": "mean"
}
```

**Response**:
```json
{
  "chart": {
    "1": ["Lagna"],
    "2": ["Gur"],
    "4": ["Ketu"],
    "10": ["Man", "Bud", "Rahu"],
    "11": ["Sur", "Shu", "Sha"],
    "12": ["Cha"]
  },
  "planets_table": [
    {
      "planet": "Lagna",
      "longitude": "29° Vrish 35' 00.03\"",
      "nakshatra": "Mrigashira",
      "pada": 2,
      "full_degree": 59.58,
      "speed_deg_per_day": 0.0,
      "right_ascension": 85.23,
      "declination": 23.45,
      "latitude": 0.0
    }
    // ... more planets
  ],
  "metadata": {
    "place": "Bhongir",
    "date": "21/03/2026",
    "time": "11:21:10",
    "latitude": 17.51083,
    "longitude": 78.88889,
    "tz_offset": 5.5,
    "ayanamsha": "lahiri",
    "rahu_type": "mean",
    "julian_day": 2461120.743866
  }
}
```

---

## 2. SOUTH INDIAN STYLE ENDPOINTS (NEW!)

### 2.1 Generate South Indian Chart - POST
**Endpoint**: `POST /api/gochara/south-indian`

**Request Body**:
```json
{
  "date": "2026-03-21",
  "time": "11:21:10",
  "place": "Bhongir, India"
}
```

**With Optional Coordinates** (faster):
```json
{
  "date": "2026-03-21",
  "time": "11:21:10",
  "place": "Bhongir, India",
  "latitude": 17.51083,
  "longitude": 78.88889,
  "timezone": "Asia/Kolkata"
}
```

---

### 2.2 Generate South Indian Chart - GET
**Endpoint**: `GET /api/gochara/south-indian`

**Query Parameters**:
```
date: 2026-03-21
time: 11:21:10
place: Bhongir, India
```

**Example**:
```
GET /api/gochara/south-indian?date=2026-03-21&time=11:21:10&place=Bhongir,%20India
```

**Response**:
```json
{
  "chart": {
    "1": ["Lagna", "Sur", "Shu", "Sha"],
    "2": ["Cha"],
    "4": ["Gur"],
    "6": ["Ketu"],
    "12": ["Man", "Bud", "Rahu"]
  },
  "planets_table": [
    {
      "planet": "Lagna",
      "longitude": "06° Pisc 23' 58.41\"",
      "sign": "Pisces",
      "nakshatra": "Uttara Bhadrapada",
      "house": 1,
      "full_degree": 336.40,
      "speed_deg_per_day": 0.0
    }
    // ... more planets
  ],
  "metadata": {
    "place": "Bhongir, India",
    "date": "2026-03-21",
    "time": "11:21:10",
    "latitude": 17.51083,
    "longitude": 78.88889,
    "timezone": "Asia/Kolkata",
    "julian_day": 2461120.74375,
    "calculation_type": "Gochara (Transit Chart)",
    "chart_style": "South Indian (Whole Sign Houses)"
  }
}
```

---

## Key Differences

| Feature | Drik Panchanga Style | South Indian Style |
|---------|---------------------|-------------------|
| **Date Format** | DD/MM/YYYY | YYYY-MM-DD |
| **Timezone** | UTC offset (5.5) | Timezone name ("Asia/Kolkata") |
| **Calculation** | drik-panchanga library | Your existing ephemeris.py |
| **Extra Data** | RA, Declination, Latitude | Sign names, simpler format |
| **Ayanamsha** | Configurable (lahiri/raman/kp) | Uses your default settings |
| **City Search** | Local drik-panchanga DB | GeoNames API |

---

## Test Cases

### Test Case 1: March 21, 2026 Morning (Drik Style)
```json
{
  "date": "21/03/2026",
  "time": "11:21:10",
  "place": "Bhongir",
  "ayanamsha": "lahiri",
  "rahu_type": "mean"
}
```

### Test Case 2: March 21, 2026 Morning (South Indian Style)
```json
{
  "date": "2026-03-21",
  "time": "11:21:10",
  "place": "Bhongir, India",
  "latitude": 17.51083,
  "longitude": 78.88889,
  "timezone": "Asia/Kolkata"
}
```

### Test Case 3: Current Date/Time (South Indian)
```json
{
  "date": "2026-03-21",
  "time": "17:30:00",
  "place": "Mumbai, India"
}
```

---

## How to Test

1. **Start the server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Open Swagger UI**:
   ```
   http://localhost:8000/swagger
   ```

3. **Find "Gochara Chart" section** - You'll see all endpoints

4. **Test in this order**:
   - First: `/api/gochara/search` - Search for your city
   - Second: `/api/gochara/south-indian` (POST) - Easiest to use
   - Third: `/api/gochara/chart` (POST) - Drik Panchanga style

---

## Which One Should You Use?

### Use **South Indian Style** (`/api/gochara/south-indian`) if:
- ✅ You want consistency with your existing nakshatra/horoscope APIs
- ✅ You prefer YYYY-MM-DD date format
- ✅ You want simpler output format
- ✅ You're building a unified system

### Use **Drik Panchanga Style** (`/api/gochara/chart`) if:
- ✅ You need exact DrikPanchang.com replication
- ✅ You want Right Ascension, Declination data
- ✅ You need configurable ayanamsha (Lahiri/Raman/KP)
- ✅ You want to match official DrikPanchang screenshots

---

## Notes

- Both implementations use **Whole Sign House System** (Rashi chart)
- Both sort planets in standard order: Sur, Cha, Man, Bud, Gur, Shu, Sha, Rahu, Ketu
- Both calculate accurate planetary positions using Swiss Ephemeris
- The main difference is the calculation methodology and output format
