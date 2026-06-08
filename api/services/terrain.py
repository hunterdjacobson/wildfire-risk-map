import math

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on Earth in kilometers.
    """
    R = 6371.0  # Earth radius in km
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def generate_grid_around_point(center_lat: float, center_lon: float, radius_km: float = 30.0, cell_size_km: float = 2.0) -> list[dict]:
    """
    Generates a regular grid of points within a circular radius of a center point.
    """
    lat_deg_per_km = 1 / 111.0
    lon_deg_per_km = 1 / (111.0 * math.cos(math.radians(center_lat)))
    
    # Calculate bounds
    lat_step = cell_size_km * lat_deg_per_km
    lon_step = cell_size_km * lon_deg_per_km
    
    steps = int(radius_km / cell_size_km)
    grid = []
    
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            lat = center_lat + i * lat_step
            lon = center_lon + j * lon_step
            
            if haversine_km(center_lat, center_lon, lat, lon) <= radius_km:
                grid.append({"lat": lat, "lon": lon})
                
    return grid

def compute_slope_from_grid(grid_points: list[dict]) -> list[dict]:
    """
    Estimates slope percentage and aspect (bearing toward highest neighbor) for grid points.
    Expects points to have 'lat', 'lon', and 'elevation_m'.
    """
    # Create a spatial lookup for neighbors (tolerance to account for floating point)
    # Using a simple (lat, lon) rounded key as a quick lookup
    lookup = {(round(p['lat'], 5), round(p['lon'], 5)): p for p in grid_points}
    
    # Estimate degree steps from grid spacing (assuming roughly uniform)
    if len(grid_points) < 2:
        for p in grid_points:
            p['slope_pct'] = 0.0
            p['aspect_deg'] = 0.0
        return grid_points

    # Try to determine step size from first two points
    d_lat = abs(grid_points[0]['lat'] - grid_points[1]['lat']) or 0.018 # fallback ~2km
    d_lon = abs(grid_points[0]['lon'] - grid_points[1]['lon']) or 0.022 # fallback ~2km
    
    # Distance in meters for slope calc (approx cell size)
    cell_dist_m = 2000.0 # Default 2km in meters
    
    enriched_grid = []
    for p in grid_points:
        lat, lon = p['lat'], p['lon']
        elev = p.get('elevation_m', 0)
        
        # Find neighbors: North, South, East, West
        neighbors = [
            lookup.get((round(lat + d_lat, 5), round(lon, 5))), # N
            lookup.get((round(lat - d_lat, 5), round(lon, 5))), # S
            lookup.get((round(lat, 5), round(lon + d_lon, 5))), # E
            lookup.get((round(lat, 5), round(lon - d_lon, 5))), # W
        ]
        
        valid_neighbors = [n for n in neighbors if n is not None and 'elevation_m' in n]
        
        if not valid_neighbors:
            p['slope_pct'] = 0.0
            p['aspect_deg'] = 0.0
        else:
            max_diff = 0.0
            highest_neighbor = None
            
            for n in valid_neighbors:
                diff = n['elevation_m'] - elev
                if diff > max_diff:
                    max_diff = diff
                    highest_neighbor = n
            
            p['slope_pct'] = (max_diff / cell_dist_m) * 100
            
            if highest_neighbor:
                # Calculate bearing (aspect) toward highest neighbor
                d_lon_rad = math.radians(highest_neighbor['lon'] - lon)
                y = math.sin(d_lon_rad) * math.cos(math.radians(highest_neighbor['lat']))
                x = math.cos(math.radians(lat)) * math.sin(math.radians(highest_neighbor['lat'])) - \
                    math.sin(math.radians(lat)) * math.cos(math.radians(highest_neighbor['lat'])) * math.cos(d_lon_rad)
                
                bearing = math.degrees(math.atan2(y, x))
                p['aspect_deg'] = (bearing + 360) % 360
            else:
                p['aspect_deg'] = 0.0
                
        enriched_grid.append(p)
        
    return enriched_grid
