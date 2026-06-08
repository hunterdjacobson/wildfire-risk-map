import httpx
import asyncio

async def fetch_weather_for_points(points: list[dict]) -> list[dict]:
    """
    Enriches a list of points (lat, lon) with current weather data from Open-Meteo.
    Batches requests in chunks of 50 to comply with API limits and efficiency.
    """
    if not points:
        return []

    enriched_points = []
    chunk_size = 50
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(points), chunk_size):
            chunk = points[i : i + chunk_size]
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
                
                # Open-Meteo returns a list if multiple locations are requested
                # If only one point is requested, it might return a single dict, but we treat it as a list
                if not isinstance(data, list):
                    data = [data]
                
                for idx, result in enumerate(data):
                    original_point = chunk[idx].copy()
                    current = result.get("current", {})
                    
                    original_point.update({
                        "temp_c": current.get("temperature_2m"),
                        "humidity_pct": current.get("relative_humidity_2m"),
                        "wind_speed_ms": current.get("wind_speed_10m"),
                        "wind_dir_deg": current.get("wind_direction_10m"),
                        "precip_mm": current.get("precipitation"),
                        "elevation_m": result.get("elevation", 0)
                    })
                    enriched_points.append(original_point)
                    
            except Exception as e:
                print(f"Error fetching weather for chunk starting at index {i}: {e}")
                # Append original points with None values if request fails
                for p in chunk:
                    point_copy = p.copy()
                    point_copy.update({
                        "temp_c": None,
                        "humidity_pct": None,
                        "wind_speed_ms": None,
                        "wind_dir_deg": None,
                        "precip_mm": None,
                        "elevation_m": 0
                    })
                    enriched_points.append(point_copy)
                    
    return enriched_points

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
