import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from services.firms import fetch_firms_hotspots, DEFAULT_BBOX
from services.weather import fetch_weather_for_points
from services.spread_risk import compute_risk_grid
from services.cache import risk_cache

async def refresh_risk_data(api_key: str):
    """
    Runs the full pipeline: fetch hotspots → enrich weather → compute risk grid
    Stores result in risk_cache.
    """
    try:
        # 1. Fetch raw hotspots
        # Use default 'days=1' as in routers/risk.py
        hotspots = await fetch_firms_hotspots(api_key, DEFAULT_BBOX, days=2)
        
        # 2. Enrich with weather
        enriched_hotspots = await fetch_weather_for_points(hotspots)
        
        # 3. Compute risk grid
        risk_grid = compute_risk_grid(enriched_hotspots, radius_km=30.0, cell_size_km=2.0)
        
        # Store in cache
        data = {
            "hotspot_count": len(enriched_hotspots),
            "grid_cell_count": len(risk_grid),
            "hotspots": enriched_hotspots,
            "risk_grid": risk_grid,
            "generated_at": datetime.utcnow().isoformat()
        }
        risk_cache.set("conus_risk", data, ttl_seconds=1800)
        
        # Store metadata
        meta = {
            "hotspot_count": len(enriched_hotspots),
            "grid_cell_count": len(risk_grid),
            "refreshed_at": datetime.utcnow().isoformat()
        }
        risk_cache.set("conus_meta", meta, ttl_seconds=1800)
        
        print(f"Risk cache refreshed: {len(enriched_hotspots)} hotspots, {len(risk_grid)} grid cells")
        
    except Exception as e:
        print(f"Error refreshing risk data: {e}")

def start_scheduler(api_key: str) -> BackgroundScheduler:
    """
    Creates and starts the APScheduler BackgroundScheduler.
    """
    scheduler = BackgroundScheduler()
    
    # Add job that calls refresh_risk_data every 1800 seconds
    # APScheduler runs functions, we need to bridge with asyncio
    def job():
        asyncio.run(refresh_risk_data(api_key))
        
    scheduler.add_job(job, 'interval', seconds=1800)
    
    # Immediately trigger one run
    scheduler.add_job(job, next_run_time=datetime.now())
    
    scheduler.start()
    return scheduler
