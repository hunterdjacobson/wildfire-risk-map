import httpx
import asyncio

async def fetch_weather_for_points(points: list[dict]) -> list[dict]:
    """
    Enriches a list of points (lat, lon) with current weather data from Open-Meteo.
    Deduplicates spatially (11km grid) to minimize API requests and implements rate-limit safety.
    """
    if not points:
        return []

    # 1. DEDUPLICATION STEP
    # Round to 1 decimal place (~11km) and pick one representative point per cell
    weather_cells = {}
    for p in points:
        key = (round(p['lat'], 1), round(p['lon'], 1))
        if key not in weather_cells:
            weather_cells[key] = p

    deduplicated_points = list(weather_cells.values())
    
    # 2. FETCH STEP
    enriched_results = []
    chunk_size = 50
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(deduplicated_points), chunk_size):
            chunk = deduplicated_points[i : i + chunk_size]
            lats = ",".join(str(p["lat"]) for p in chunk)
            lons = ",".join(str(p["lon"]) for p in chunk)
            
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lats,
                "longitude": lons,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation",
                "wind_speed_unit": "ms",
                "timezone": "auto"
            }
            
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not isinstance(data, list):
                    data = [data]
                
                for idx, result in enumerate(data):
                    current = result.get("current", {})
                    enriched_results.append({
                        "lat": result.get("latitude"),
                        "lon": result.get("longitude"),
                        "temp_c": current.get("temperature_2m"),
                        "humidity_pct": current.get("relative_humidity_2m"),
                        "wind_speed_ms": current.get("wind_speed_10m"),
                        "wind_dir_deg": current.get("wind_direction_10m"),
                        "precip_mm": current.get("precipitation"),
                        "elevation_m": result.get("elevation", 0)
                    })
                    
            except Exception as e:
                print(f"Error fetching weather for chunk starting at index {i}: {e}")
                # Fallback for failed points in chunk
                for p in chunk:
                    enriched_results.append({
                        "lat": p["lat"],
                        "lon": p["lon"],
                        "temp_c": None,
                        "humidity_pct": None,
                        "wind_speed_ms": None,
                        "wind_dir_deg": None,
                        "precip_mm": None,
                        "elevation_m": 0
                    })
            
            # Rate limit safety delay
            if i + chunk_size < len(deduplicated_points):
                await asyncio.sleep(0.5)

    # Build lookup dict for mapping step
    weather_lookup = {
        (round(r['lat'], 1), round(r['lon'], 1)): r 
        for r in enriched_results
    }

    # 3. MAPPING STEP
    final_enriched_list = []
    for p in points:
        point_copy = p.copy()
        key = (round(p['lat'], 1), round(p['lon'], 1))
        
        weather_data = weather_lookup.get(key)
        if weather_data:
            point_copy.update({
                "temp_c": weather_data.get("temp_c"),
                "humidity_pct": weather_data.get("humidity_pct"),
                "wind_speed_ms": weather_data.get("wind_speed_10m") if "wind_speed_10m" in weather_data else weather_data.get("wind_speed_ms"), # Handle possible naming variations
                "wind_dir_deg": weather_data.get("wind_direction_10m") if "wind_direction_10m" in weather_data else weather_data.get("wind_dir_deg"),
                "precip_mm": weather_data.get("precip_mm"),
                "elevation_m": weather_data.get("elevation_m")
            })
            # Ensure wind fields are correctly mapped if they came from our enriched_results structure
            point_copy["wind_speed_ms"] = weather_data.get("wind_speed_ms")
            point_copy["wind_dir_deg"] = weather_data.get("wind_dir_deg")
        else:
            point_copy.update({
                "temp_c": None, "humidity_pct": None, "wind_speed_ms": None,
                "wind_dir_deg": None, "precip_mm": None, "elevation_m": 0
            })
            
        final_enriched_list.append(point_copy)

    return final_enriched_list

def compute_fuel_moisture(temp_c: float, humidity_pct: float) -> float:
    """
    Computes an estimated fuel moisture percentage based on temp and humidity.
    Formula: 0.942 * humidity_pct - 0.0191 * temp_c + 1.4
    Clamped to [1.0, 30.0]
    """
    if temp_c is None or humidity_pct is None:
        return 12.0
    
    moisture = 0.942 * humidity_pct - 0.0191 * temp_c + 1.4
    return max(1.0, min(30.0, moisture))
