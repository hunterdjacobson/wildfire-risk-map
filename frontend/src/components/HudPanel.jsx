import React from 'react';

const HudPanel = ({ loading, hotspotCount, lastUpdated, cacheAge }) => {
  const panelStyle = {
    position: 'fixed',
    top: '16px',
    right: '16px',
    background: 'rgba(10, 10, 10, 0.8)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '10px',
    padding: '16px',
    minWidth: '220px',
    color: 'white',
    fontFamily: 'sans-serif',
    zIndex: 1000
  };

  const titleStyle = {
    fontSize: '16px',
    fontWeight: 'bold',
    marginBottom: '12px'
  };

  const statusStyle = {
    color: loading ? '#ff6b2b' : 'white',
    fontSize: '14px'
  };

  const subLineStyle = {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '12px',
    marginTop: '4px'
  };

  return (
    <div style={panelStyle}>
      <div style={titleStyle}>Wildfire Risk Map</div>
      <div style={statusStyle}>
        {loading ? 'Fetching fire data...' : `${hotspotCount} active hotspots`}
      </div>
      {!loading && (
        <div style={subLineStyle}>
          Updated {cacheAge}s ago
        </div>
      )}
    </div>
  );
};

export default HudPanel;
