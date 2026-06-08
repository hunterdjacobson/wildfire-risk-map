import { ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';

export function useFireLayers(riskData, setHoveredObject, layerVisibility) {
  if (!riskData) return [];

  const layers = [];

  if (layerVisibility.hotspots) {
    layers.push(
      new ScatterplotLayer({
        id: 'fire-hotspots',
        data: riskData.hotspots || [],
        visible: layerVisibility.hotspots,
        getPosition: d => [d.lon, d.lat],
        getRadius: d => Math.max(3000, (d.frp || 10) * 250),
        radiusUnits: 'meters',
        getFillColor: d => 
          d.confidence === 'high' ? [255, 60, 0, 220] : 
          d.confidence === 'nominal' ? [255, 140, 0, 190] : [255, 200, 50, 160],
        stroked: true,
        getLineColor: [255, 255, 255, 50],
        lineWidthMinPixels: 0.5,
        pickable: true,
        onHover: ({ object, x, y }) => {
          setHoveredObject(object ? { data: object, x, y } : null);
        }
      })
    );
  }

  if (layerVisibility.heatmap) {
    layers.push(
      new HeatmapLayer({
        id: 'risk-heatmap',
        data: riskData.risk_grid || [],
        visible: layerVisibility.heatmap,
        getPosition: d => [d.lon, d.lat],
        getWeight: d => d.risk_score,
        radiusPixels: 45,
        intensity: 2.5,
        threshold: 0.05,
        colorRange: [
          [255, 255, 178, 0],
          [254, 204, 92, 100],
          [253, 141, 60, 160],
          [240, 59, 32, 210],
          [189, 0, 38, 240]
        ]
      })
    );
  }

  return layers;
}
