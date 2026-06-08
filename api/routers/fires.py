import os
from fastapi import APIRouter, Query
from services.firms import fetch_firms_hotspots, DEFAULT_BBOX

router = APIRouter(prefix="/fires", tags=["fires"])

@router.get("/hotspots")
async def get_hotspots(days: int = Query(1, ge=1, le=10)):
    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        return {"error": "FIRMS_API_KEY not configured", "hotspots": [], "count": 0}
    
    hotspots = await fetch_firms_hotspots(api_key, DEFAULT_BBOX, days)
    return {
        "count": len(hotspots),
        "hotspots": hotspots
    }

@router.get("/hotspots/region")
async def get_hotspots_region(
    west: float, 
    south: float, 
    east: float, 
    north: float, 
    days: int = Query(1, ge=1, le=5)
):
    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        return {"error": "FIRMS_API_KEY not configured", "hotspots": [], "count": 0}
    
    bbox = (west, south, east, north)
    hotspots = await fetch_firms_hotspots(api_key, bbox, days)
    return {
        "count": len(hotspots),
        "hotspots": hotspots
    }
