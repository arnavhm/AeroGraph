import { feature } from 'topojson-client';

const COUNTRIES_OBJECT_KEY = 'countries';

export function toCountryFeatures(topology) {
  const object = topology?.objects?.[COUNTRIES_OBJECT_KEY];
  if (!object) {
    throw new Error(`Topology has no "${COUNTRIES_OBJECT_KEY}" object`);
  }
  const { features } = feature(topology, object);
  if (!Array.isArray(features) || features.length === 0) {
    throw new Error(
      `Expected feature(topology, "${COUNTRIES_OBJECT_KEY}") to produce a non-empty features array, got: ${JSON.stringify(features)}`
    );
  }
  return features;
}

// Viewing choice, not a derived quantity: the centroid below comes from data,
// this does not. Confirmed only by Arnav's browser; a one-line change if wrong.
export const CAMERA_ALTITUDE = 1.5;

export function cameraPOV(airports) {
  if (airports == null || typeof airports !== 'object') {
    throw new Error('cameraPOV requires an airports object');
  }
  const entries = Object.values(airports);
  if (entries.length === 0) {
    throw new Error('cameraPOV requires at least one airport');
  }

  const totals = entries.reduce(
    (acc, { lat, lon }) => ({ lat: acc.lat + lat, lon: acc.lon + lon }),
    { lat: 0, lon: 0 }
  );

  return {
    lat: totals.lat / entries.length,
    lng: totals.lon / entries.length,
    altitude: CAMERA_ALTITUDE,
  };
}
