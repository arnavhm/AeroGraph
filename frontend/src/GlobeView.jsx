import React, { useMemo, useRef, useState, useEffect } from 'react';
import Globe from 'react-globe.gl';
import { deriveRouteArcs } from './routeArcs.js';
import { deriveAirportMarkers } from './airportMarkers.js';
import { AIRPORTS } from './airports.js';
import { toCountryFeatures, cameraPOV } from './worldPolygons.js';
import worldTopology from 'world-atlas/countries-50m.json' with { type: 'json' };

// Canvas needs resolved colour strings, not var() references. Resolved once at
// module level; an empty resolution is a failure, never silently defaulted.
const readToken = (name) => {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (value === '') {
    throw new Error(`Design token ${name} resolved to an empty string`);
  }
  return value;
};

const COLOR = {
  bg: readToken('--ag-bg'),
  grid: readToken('--ag-grid'),
  border: readToken('--ag-border'),
  accent: readToken('--ag-accent'),
};

export default function GlobeView({ nodes, links }) {
  const wrapRef = useRef(null);
  const globeRef = useRef(null);
  const hasSetInitialPOV = useRef(false);
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
  const countries = useMemo(() => toCountryFeatures(worldTopology), []);

  useEffect(() => {
    if (size && globeRef.current && !hasSetInitialPOV.current) {
      globeRef.current.pointOfView(cameraPOV(AIRPORTS));
      hasSetInitialPOV.current = true;
    }
  }, [size]);

  return (
    <div ref={wrapRef} style={{ margin: 0, overflow: 'hidden', width: '100%', height: '100%' }}>
      {size && <Globe
        ref={globeRef}
        width={size.width}
        height={size.height}
        backgroundColor={COLOR.bg}
        polygonsData={countries}
        polygonCapColor={COLOR.grid}
        polygonSideColor={COLOR.border}
        polygonStrokeColor={COLOR.accent}
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
