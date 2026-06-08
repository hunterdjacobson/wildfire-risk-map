import csv
import httpx
import io

DEFAULT_BBOX = (-125.0, 24.0, -66.0, 50.0)

async def fetch_firms_hotspots(api_key: str, bbox: tuple = DEFAULT_BBOX, days: int = 1) -> list[dict]:
    """
    Fetches fire hotspot data from NASA FIRMS API and parses CSV response.
    """
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}/{days}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            hotspots = []
            for raw_row in reader:
                # 1. Clean and normalize: strip whitespace from keys and values
                row = {k.strip(): v.strip() for k, v in raw_row.items() if k is not None}
                
                try:
                    # 2. Update filtering check for single-letter format
                    confidence_raw = row.get('confidence', '').lower()
                    
                    if confidence_raw in ('n', 'h', 'nominal', 'high'):
                        # 3. Map single characters back to descriptive labels
                        confidence_label = "high" if confidence_raw in ('h', 'high') else "nominal"
                        
                        # 4. Robust data type parsing with safe fallbacks
                        hotspots.append({
                            "lat": float(row.get('latitude', 0)),
                            "lon": float(row.get('longitude', 0)),
                            "brightness": float(row.get('bright_ti4', 0) or 0),
                            "frp": float(row.get('frp', 0) or 0),
                            "confidence": confidence_label,
                            "acq_date": row.get('acq_date', ''),
                            "acq_time": row.get('acq_time', '')
                        })
                except (ValueError, KeyError):
                    # Skip corrupt fields or missing mandatory float conversions
                    continue
            
            # 5. Return hotspots after loop terminates in correct scope
            return hotspots
            
    except Exception as e:
        print(f"Error fetching FIRMS hotspots: {e}")
        return []
