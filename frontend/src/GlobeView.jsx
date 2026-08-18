import React, { useMemo } from 'react';
import Globe from 'react-globe.gl';
import { deriveRouteArcs } from './routeArcs.js';
import { deriveAirportMarkers } from './airportMarkers.js';

export default function GlobeView({ nodes, links }) {
  const arcs = useMemo(() => deriveRouteArcs(nodes, links), [nodes, links]);
  const markers = useMemo(() => deriveAirportMarkers(nodes), [nodes]);

  return (
    <div style={{ margin: 0, overflow: 'hidden' }}>
      <Globe
        width={window.innerWidth}
        height={window.innerHeight}
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
      />
    </div>
  );
}
