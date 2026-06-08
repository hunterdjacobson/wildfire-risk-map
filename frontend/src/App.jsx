import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ScatterplotLayer } from '@deck.gl/layers';
import { GridCellLayer } from '@deck.gl/layers';
import MapView from './components/MapView';
import HudPanel from './components/HudPanel';

function App() {
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cacheAge, setCacheAge] = useState(0);
  const [hoveredObject, setHoveredObject] = useState(null);
  const [pointerPos, setPointerPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [gridRes, statusRes] = await Promise.all([
          axios.get('/api/risk/grid'),
          axios.get('/api/risk/grid/status')
        ]);
        
        setRiskData(gridRes.data);
        setCacheAge(statusRes.data.cache_age_seconds || 0);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleHover = ({ object, x, y }) => {
    setHoveredObject(object);
    setPointerPos({ x, y });
  };

  // Dynamic Layer Construction Suite
  const buildDeckLayers = () => {
    if (!riskData) return [];

    return [
      // Layer 1: The Risk Grid (38,757 Matrix Blocks)
      new GridCellLayer({
        id: 'risk-grid-layer',
        data: riskData.risk_grid || [],
        cellSize: 2000, // Matching your backend 2km step design
        extruded: false, // Keep flat for scannable dashboard rendering
        getPosition: d => [d.lon, d.lat], // WebGL X, Y order requirement
        // Dynamic heat gradient mapping: closer to 1.0 risk -> deeper red color
        getFillColor: d => [
          255, 
          Math.floor((1 - d.risk_score) * 200), 
          0, 
          Math.floor(d.risk_score * 180) + 50
        ],
        updateTriggers: {
          data: riskData.risk_grid
        }
      }),

      // Layer 2: Raw Core Hotspots (1,377 Detections overlaid on top)
      new ScatterplotLayer({
        id: 'hotspots-layer',
        data: riskData.hotspots || [],
        getPosition: d => [d.lon, d.lat],
        getRadius: d => (d.frp || 1) * 50, // Scales radius on fire power footprint
        getFillColor: [255, 69, 0, 230], // Vibrant orange-red core embers
        radiusMinPixels: 4,
        radiusMaxPixels: 25,
        updateTriggers: {
          data: riskData.hotspots
        }
      })
    ];
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#111' }}>
      <MapView 
        layers={buildDeckLayers()} // <-- Firing our dynamically computed layers!
        onHover={handleHover} 
      />
      
      <HudPanel 
        loading={loading} 
        hotspotCount={riskData?.hotspot_count || 0} 
        lastUpdated={riskData?.generated_at || ''} 
        cacheAge={cacheAge} 
      />

      {/* Tooltip Overlay */}
      {hoveredObject && (
        <div style={{
          position: 'absolute',
          zIndex: 1000,
          pointerEvents: 'none',
          left: pointerPos.x + 15,
          top: pointerPos.y + 15,
          backgroundColor: 'rgba(20, 20, 20, 0.9)',
          color: '#fff',
          padding: '8px 12px',
          borderRadius: '4px',
          fontSize: '12px',
          border: '1px solid rgba(255, 69, 0, 0.4)',
          fontFamily: 'monospace'
        }}>
          {hoveredObject.risk_score !== undefined ? (
            <>
              <strong>Risk Grid Cell</strong><br />
              Risk Score: {(hoveredObject.risk_score * 100).toFixed(1)}%<br />
              Spread VelocityMultiplier: {hoveredObject.spread_rate?.toFixed(2)}<br />
              Distance to Fire: {hoveredObject.distance_km?.toFixed(2)} km
            </>
          ) : (
            <>
              <strong>Satellite Hotspot</strong><br />
              Radiative Power (FRP): {hoveredObject.frp} MW<br />
              Brightness: {hoveredObject.brightness} K<br />
              Confidence: {hoveredObject.confidence}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;