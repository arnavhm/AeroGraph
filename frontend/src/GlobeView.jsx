import React, { useMemo, useRef, useState, useEffect } from 'react';
import Globe from 'react-globe.gl';
import { deriveRouteArcs } from './routeArcs.js';
import { deriveAirportMarkers } from './airportMarkers.js';

export default function GlobeView({ nodes, links }) {
  const wrapRef = useRef(null);
  const [size, setSize] = useState(null);

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      if (width > 0 && height > 0) setSize({ width, height });
    });
    observer.observe(wrapRef.current);
    return () => observer.disconnect();
  }, []);

  const arcs = useMemo(() => deriveRouteArcs(nodes, links), [nodes, links]);
  const markers = useMemo(() => deriveAirportMarkers(nodes), [nodes]);

  return (
    <div ref={wrapRef} style={{ margin: 0, overflow: 'hidden', width: '100%', height: '100%' }}>
      {size && <Globe
        width={size.width}
        height={size.height}
        arcsData={arcs}
        arcStartLat={d => d.origin_lat}
        arcStartLng={d => d.origin_lon}
        arcEndLat={d => d.destination_lat}
        arcEndLng={d => d.destination_lon}
        pointsData={markers}
        pointLat={d => d.lat}
        pointLng={d => d.lon}
        pointAltitude={d => d.altitude}
        pointColor={d => d.color}
        pointLabel={d => `${d.icao} - ${d.delay} minutes per arrival`}
      />}
    </div>
  );
}
