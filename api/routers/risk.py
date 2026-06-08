import os
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from services.firms import fetch_firms_hotspots, DEFAULT_BBOX
from services.weather import fetch_weather_for_points
from services.spread_risk import compute_risk_grid
from services.cache import risk_cache

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/grid")
async def get_risk_grid(days: int = Query(1, ge=1, le=10)):
    """
    Main risk grid endpoint for the default US BBOX.
    Uses cache if available, else falls back to full pipeline.
    """
    # 1. Check cache first (Step 0)
    cached_data = risk_cache.get("conus_risk")
    if cached_data:
        return {**cached_data, "cached": True}

    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        return {
            "error": "FIRMS_API_KEY not configured",
            "hotspot_count": 0,
            "grid_cell_count": 0,
            "hotspots": [],
            "risk_grid": [],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    # 2. Fetch raw hotspots (Step A)
    hotspots = await fetch_firms_hotspots(api_key, DEFAULT_BBOX, days)
    
    # 3. Immediately enrich ONLY raw hotspots with weather (Step B)
    enriched_hotspots = await fetch_weather_for_points(hotspots)
    
    # 4. Pass weather-enriched hotspots into grid engine (Step C)
    risk_grid = compute_risk_grid(enriched_hotspots, radius_km=30.0, cell_size_km=2.0)
    
    result = {
        "hotspot_count": len(enriched_hotspots),
        "grid_cell_count": len(risk_grid),
        "hotspots": enriched_hotspots,
        "risk_grid": risk_grid,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    # Store in cache for next time
    risk_cache.set("conus_risk", result, ttl_seconds=1800)
    
    return {**result, "cached": False}

@router.get("/grid/status")
async def get_grid_status():
    """
    Returns the status and metadata of the risk cache.
    """
    meta = risk_cache.get("conus_meta") or {}
    return {
        "cache_meta": meta,
        "cache_age_seconds": risk_cache.age_seconds("conus_risk"),
        "cached": risk_cache.get("conus_risk") is not None
    }

@router.get("/grid/region")
async def get_risk_grid_region(
    west: float, 
    south: float, 
    east: float, 
    north: float, 
    days: int = Query(1, ge=1, le=5)
):
    """
    Regional risk grid endpoint for a user-specified BBOX.
    Follows strict pipeline: Fetch Hotspots -> Enrich Hotspots (Weather) -> Generate Risk Grid.
    """
    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        return {
            "error": "FIRMS_API_KEY not configured",
            "hotspot_count": 0,
            "grid_cell_count": 0,
            "hotspots": [],
            "risk_grid": [],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    bbox = (west, south, east, north)
    
    # 1. Fetch raw hotspots (Step A)
    hotspots = await fetch_firms_hotspots(api_key, bbox, days)
    
    # 2. Immediately enrich ONLY raw hotspots with weather (Step B)
    enriched_hotspots = await fetch_weather_for_points(hotspots)
    
    # 3. Pass weather-enriched hotspots into grid engine (Step C)
    risk_grid = compute_risk_grid(enriched_hotspots, radius_km=30.0, cell_size_km=2.0)
    
    return {
        "hotspot_count": len(enriched_hotspots),
        "grid_cell_count": len(risk_grid),
        "hotspots": enriched_hotspots,
        "risk_grid": risk_grid,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
