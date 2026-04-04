# ProKerala-Style Location Search API

## Overview

This implementation replicates the ProKerala location search widget functionality using the GeoNames API (the same database that DrikPanchang and many astrology sites use).

## Features

✅ **Autocomplete Search** - Real-time location suggestions as you type  
✅ **11M+ Places** - Cities, towns, villages worldwide  
✅ **Timezone Information** - Automatic timezone detection with DST support  
✅ **ProKerala Compatible** - Same response format as ProKerala API  
✅ **Fast & Accurate** - Powered by GeoNames database  
✅ **No External Dependencies** - Uses free GeoNames API  

---

## Setup

### 1. Get GeoNames Account (Free)

1. Register at: https://www.geonames.org/login
2. Enable web services: https://www.geonames.org/enablefreewebservice
3. Set your username in environment variable:

```bash
export GEONAMES_USERNAME=your_username
```

Or set it in `.env` file:
```
GEONAMES_USERNAME=your_username
```

**Free tier**: 30,000 calls/day, 2,000 calls/hour

---

## API Endpoints

### 1. Search Locations

**Endpoint:** `GET /api/location/search`

**Parameters:**
- `q` (required): Search query (minimum 2 characters)
- `max_results` (optional): Maximum results (default: 10, max: 50)

**Example:**
```bash
GET /api/location/search?q=Bhongir
GET /api/location/search?q=Mumbai&max_results=5
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "1269843",
      "name": "Bhongir",
      "full_name": "Bhongir, Telangana, India",
      "latitude": 17.51083,
      "longitude": 78.88889,
      "timezone": "Asia/Kolkata",
      "country_code": "IN",
      "country_name": "India",
      "state": "Telangana"
    }
  ],
  "count": 1
}
```

### 2. Get Location Details

**Endpoint:** `GET /api/location/{location_id}`

**Example:**
```bash
GET /api/location/1269843
```

**Response:**
```json
{
  "status": "success",
  "location": {
    "id": "1269843",
    "name": "Bhongir",
    "full_name": "Bhongir, Telangana, India",
    "latitude": 17.51083,
    "longitude": 78.88889,
    "timezone": "Asia/Kolkata",
    "timezone_offset": 5.5,
    "country_code": "IN",
    "country_name": "India",
    "state": "Telangana",
    "population": 50000
  }
}
```

---

## Integration

### Already Integrated in main.py

The endpoints are already added to your main FastAPI application:

```bash
python main.py
```

Then access:
- **Swagger UI**: http://localhost:8000/swagger
- **Demo Page**: http://localhost:8000/static/prokerala-location-demo.html

### Standalone API (Optional)

You can also run it as a standalone service:

```bash
python prokerala_location_api.py
```

Then access:
- **Swagger UI**: http://localhost:8001/docs
- **API**: http://localhost:8001/api/location/search?q=Bhongir

---

## Frontend Integration

### HTML/JavaScript Example

```html
<input 
    type="text" 
    id="location" 
    placeholder="Start typing a city name..." 
    autocomplete="off"
>
<div id="suggestions"></div>

<script>
const locationInput = document.getElementById('location');
const suggestionsDiv = document.getElementById('suggestions');

locationInput.addEventListener('input', async function(e) {
    const query = e.target.value.trim();
    
    if (query.length < 2) {
        suggestionsDiv.innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(
            `http://localhost:8000/api/location/search?q=${encodeURIComponent(query)}`
        );
        const data = await response.json();
        
        // Display suggestions
        suggestionsDiv.innerHTML = data.results.map(loc => `
            <div onclick="selectLocation(${JSON.stringify(loc).replace(/"/g, '&quot;')})">
                ${loc.full_name}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Search failed:', error);
    }
});

function selectLocation(location) {
    locationInput.value = location.full_name;
    console.log('Selected:', location);
    // Use location.latitude, location.longitude, location.timezone
}
</script>
```

### React Example

```jsx
import { useState, useEffect } from 'react';

function LocationSearch() {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [selected, setSelected] = useState(null);
    
    useEffect(() => {
        if (query.length < 2) {
            setSuggestions([]);
            return;
        }
        
        const timer = setTimeout(async () => {
            try {
                const response = await fetch(
                    `http://localhost:8000/api/location/search?q=${encodeURIComponent(query)}`
                );
                const data = await response.json();
                setSuggestions(data.results);
            } catch (error) {
                console.error('Search failed:', error);
            }
        }, 300);
        
        return () => clearTimeout(timer);
    }, [query]);
    
    return (
        <div>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Start typing a city name..."
            />
            
            {suggestions.length > 0 && (
                <div className="suggestions">
                    {suggestions.map(loc => (
                        <div 
                            key={loc.id}
                            onClick={() => {
                                setSelected(loc);
                                setQuery(loc.full_name);
                                setSuggestions([]);
                            }}
                        >
                            {loc.full_name}
                        </div>
                    ))}
                </div>
            )}
            
            {selected && (
                <div>
                    <p>Latitude: {selected.latitude}</p>
                    <p>Longitude: {selected.longitude}</p>
                    <p>Timezone: {selected.timezone}</p>
                </div>
            )}
        </div>
    );
}
```

---

## Demo Page

A complete working demo is available at:

```
http://localhost:8000/static/prokerala-location-demo.html
```

Features:
- Real-time autocomplete search
- Beautiful UI matching ProKerala style
- Shows selected location details
- Copy-paste ready code

---

## Comparison with ProKerala

| Feature | ProKerala | This Implementation |
|---------|-----------|---------------------|
| Database | GeoNames | GeoNames ✅ |
| Places | 11M+ | 11M+ ✅ |
| Autocomplete | Yes | Yes ✅ |
| Timezone | Yes | Yes ✅ |
| DST Support | Yes | Yes ✅ |
| API Format | JSON | JSON ✅ |
| Cost | Paid API | Free ✅ |

---

## Usage in Gochara Chart

The location search integrates seamlessly with the Gochara chart endpoint:

```javascript
// 1. Search for location
const searchResponse = await fetch('/api/location/search?q=Bhongir');
const searchData = await searchResponse.json();
const location = searchData.results[0];

// 2. Generate Gochara chart
const chartResponse = await fetch('/api/gochara/chart', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        date: '19/03/2026',
        time: '17:56:47',
        place: location.full_name,
        latitude: location.latitude,
        longitude: location.longitude,
        timezone_offset: 5.5,  // Calculate from location.timezone
        ayanamsha: 'lahiri',
        rahu_type: 'mean'
    })
});
const chart = await chartResponse.json();
```

---

## Error Handling

### Common Errors

**1. GeoNames Username Not Set**
```json
{
  "detail": "GeoNames error: user account not enabled"
}
```
**Solution**: Set `GEONAMES_USERNAME` environment variable

**2. Rate Limit Exceeded**
```json
{
  "detail": "GeoNames error: hourly limit exceeded"
}
```
**Solution**: Wait for next hour or upgrade GeoNames account

**3. Location Not Found**
```json
{
  "status": "success",
  "results": [],
  "count": 0
}
```
**Solution**: Try different spelling or nearby city

---

## Performance

- **Search Speed**: ~200-500ms (network latency to GeoNames)
- **Caching**: Consider implementing Redis cache for popular searches
- **Rate Limits**: 2,000 calls/hour (free tier)

---

## Files

- `prokerala_location_api.py` - Standalone API (optional)
- `main.py` - Integrated endpoints (already added)
- `static/prokerala-location-demo.html` - Demo page
- `PROKERALA_LOCATION_API.md` - This documentation

---

## Testing

### Test in Swagger UI

1. Go to http://localhost:8000/swagger
2. Find "ProKerala Location" section
3. Try `/api/location/search` endpoint
4. Enter query: "Bhongir"
5. Click "Execute"

### Test in Browser

1. Go to http://localhost:8000/static/prokerala-location-demo.html
2. Type "Bhongir" in the search box
3. Select from suggestions
4. See location details

### Test with cURL

```bash
# Search
curl "http://localhost:8000/api/location/search?q=Bhongir"

# Get details
curl "http://localhost:8000/api/location/1269843"
```

---

## Support

For issues:
1. Check GeoNames account is enabled
2. Verify `GEONAMES_USERNAME` is set
3. Check rate limits (2,000/hour)
4. Try the demo page to test

---

## Credits

- **GeoNames**: https://www.geonames.org/
- **ProKerala**: Inspiration for API format
- **DrikPanchang**: Uses same GeoNames database

---

## Version History

- **1.0.0** (2026-03-19): Initial release
  - ProKerala-compatible API format
  - GeoNames integration
  - Demo page
  - Integrated into main.py
