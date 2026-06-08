import React from 'react';

const TooltipCard = ({ hoveredObject }) => {
  if (!hoveredObject || !hoveredObject.data) return null;

  const { data, x, y } = hoveredObject;

  const style = {
    position: 'absolute',
    left: x + 12,
    top: y + 12,
    pointerEvents: 'none',
    background: 'rgba(0, 0, 0, 0.85)',
    color: 'white',
    padding: '10px 14px',
    borderRadius: '8px',
    fontSize: '12px',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    lineHeight: '1.7',
    zIndex: 2000,
  };

  const badgeColor = data.confidence === 'high' ? '#ff3c00' : 
                    data.confidence === 'nominal' ? '#ff8c00' : '#ffc832';

  const isWeatherMissing = data.wind_speed_ms == null || data.humidity_pct == null || data.temp_c == null;

  return (
    <div style={style}>
      <div>
        <span style={{ fontWeight: 'bold' }}>Confidence: </span>
        <span style={{ 
          color: badgeColor, 
          background: 'rgba(0,0,0,0.3)', 
          padding: '2px 6px', 
          borderRadius: '4px',
          textTransform: 'capitalize'
        }}>
          {data.confidence || 'Unknown'}
        </span>
      </div>
      <div>
        <span style={{ fontWeight: 'bold' }}>FRP:</span> {data.frp != null ? `${data.frp.toFixed(1)} MW` : "n/a"}
      </div>
      <div>
        <span style={{ fontWeight: 'bold' }}>Acquired:</span> {data.acq_date ? `${data.acq_date} ${data.acq_time || ''}` : "n/a"}
      </div>
      <div>
        <span style={{ fontWeight: 'bold' }}>Temperature:</span> {data.temp_c != null ? `${data.temp_c.toFixed(1)}°C` : "n/a"}
      </div>
      <div>
        <span style={{ fontWeight: 'bold' }}>Wind:</span> {data.wind_speed_ms != null ? `${data.wind_speed_ms.toFixed(1)} m/s from ${data.wind_dir_deg ?? '?'}°` : "n/a"}
      </div>
      <div>
        <span style={{ fontWeight: 'bold' }}>Humidity:</span> {data.humidity_pct != null ? `${data.humidity_pct}%` : "n/a"}
      </div>
      <div>
        <span style={{ fontWeight: 'bold' }}>Position:</span> {data.lat?.toFixed(3)}, {data.lon?.toFixed(3)}
      </div>
      
      {isWeatherMissing && (
        <div style={{ 
          marginTop: '8px', 
          fontSize: '10px', 
          color: '#ff6b2b', 
          borderTop: '1px solid rgba(255,255,255,0.1)', 
          paddingTop: '4px' 
        }}>
          Weather data fallback applied (API rate-limited)
        </div>
      )}
    </div>
  );
};

export default TooltipCard;
