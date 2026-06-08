from math import radians, cos, sin, atan2, sqrt, exp, pi, degrees
from services.terrain import generate_grid_around_point
from services.weather import compute_fuel_moisture

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Standard haversine formula, returns distance in km.
    """
    R = 6371.0  # Earth radius in km
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat / 2) * sin(dLat / 2) + \
        cos(radians(lat1)) * cos(radians(lat2)) * \
        sin(dLon / 2) * sin(dLon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def bearing_to(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns compass bearing in degrees (0=north, 90=east, 180=south, 270=west) from point 1 to point 2.
    """
    dLon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    
    y = sin(dLon) * cos(lat2_rad)
    x = cos(lat1_rad) * sin(lat2_rad) - \
        sin(lat1_rad) * cos(lat2_rad) * cos(dLon)
    
    theta = atan2(y, x)
    return (degrees(theta) + 360) % 360

def compute_alignment(bearing_a: float, bearing_b: float) -> float:
    """
    Returns cos(radians(angle_diff)) where angle_diff is the smallest difference between two bearings.
    """
    angle_diff = abs(((bearing_a - bearing_b) + 180) % 360 - 180)
    return cos(radians(angle_diff))

def rothermel_spread_rate(wind_speed_ms, wind_alignment, slope_pct, slope_alignment, fuel_moisture) -> float:
    """
    Simplified Rothermel spread rate calculation.
    """
    base_rate = 1.0
    fuel_factor = exp(-0.108 * max(1.0, fuel_moisture))
    wind_factor = 0.3 * wind_speed_ms * max(0.0, wind_alignment)
    slope_factor = 0.174 * ((slope_pct / 100) ** 0.715) * max(0.0, slope_alignment)
    
    return max(0.0, base_rate * fuel_factor * (1 + wind_factor + slope_factor))

def compute_risk_grid(hotspots: list[dict], radius_km: float = 30.0, cell_size_km: float = 2.0) -> list[dict]:
    """
    Computes a grid of wildfire spread risk based on hotspots and environmental factors.
    """
    if not hotspots:
        return []

    aggregated_cells = {}
    
    for hotspot in hotspots:
        # Generate a grid of candidate cells around the hotspot
        grid = generate_grid_around_point(hotspot['lat'], hotspot['lon'], radius_km, cell_size_km)
        
        for cell in grid:
            # Find the nearest hotspot to this cell
            nearest_hotspot = hotspot
            
            dist_km = haversine_km(nearest_hotspot['lat'], nearest_hotspot['lon'], cell['lat'], cell['lon'])
            
            # Skip if distance is zero (it's the hotspot itself) or too far
            if dist_km == 0:
                dist_km = 0.1 # avoid division by zero or log issues, though not used here
            
            bearing_fire_to_cell = bearing_to(nearest_hotspot['lat'], nearest_hotspot['lon'], cell['lat'], cell['lon'])
            
            # Alignments
            wind_alignment = compute_alignment(nearest_hotspot.get('wind_dir_deg') or 0, bearing_fire_to_cell)
            slope_alignment = compute_alignment(nearest_hotspot.get('wind_dir_deg') or 0, cell.get('aspect_deg', 0))
            
            # Fuel Moisture
            fuel_moisture = compute_fuel_moisture(
                nearest_hotspot.get('temp_c'), 
                nearest_hotspot.get('humidity_pct')
            )
            
            # Spread Rate
            spread_rate = rothermel_spread_rate(
                nearest_hotspot.get('wind_speed_ms') or 5,
                wind_alignment,
                cell.get('slope_pct', 0),
                slope_alignment,
                fuel_moisture
            )
            
            # Distance Decay
            distance_decay = exp(-0.12 * dist_km)
            
            # Risk Score
            risk_score = min(1.0, spread_rate * distance_decay)
            
            # Aggregation by grid cell key (round lat/lon to 2 decimal places)
            key = (round(cell['lat'], 2), round(cell['lon'], 2))
            
            if key not in aggregated_cells or risk_score > aggregated_cells[key]['risk_score']:
                aggregated_cells[key] = {
                    "lat": key[0],
                    "lon": key[1],
                    "risk_score": risk_score,
                    "distance_km": dist_km,
                    "wind_alignment": wind_alignment,
                    "spread_rate": spread_rate
                }

    # Filter and sort
    results = [
        cell for cell in aggregated_cells.values() 
        if cell['risk_score'] >= 0.05
    ]
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return results
