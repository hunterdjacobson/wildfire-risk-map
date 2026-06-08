import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MapView from './components/MapView';
import HudPanel from './components/HudPanel';
import TooltipCard from './components/TooltipCard';
import { useFireLayers } from './layers/useFireLayers';

function App() {
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cacheAge, setCacheAge] = useState(0);
  const [hoveredObject, setHoveredObject] = useState(null);
  const [pointerPos, setPointerPos] = useState({ x: 0, y: 0 });
  const [layerVisibility, setLayerVisibility] = useState({
    hotspots: true,
    heatmap: true,
    wind: true
  });

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

  // Use the custom hook to generate Deck.gl layers
  const layers = useFireLayers(riskData, setHoveredObject, layerVisibility);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapView 
        layers={layers} 
        onHover={({ x, y }) => setPointerPos({ x, y })} 
      />
      
      <HudPanel 
        loading={loading} 
        hotspotCount={riskData?.hotspot_count || 0} 
        lastUpdated={riskData?.generated_at || ''} 
        cacheAge={cacheAge} 
      />

      <TooltipCard hoveredObject={hoveredObject} />
    </div>
  );
}

export default App;