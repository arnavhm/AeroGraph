import { test } from 'node:test';
import assert from 'node:assert';
import topology from 'world-atlas/countries-50m.json' with { type: 'json' };
import { toCountryFeatures, cameraPOV } from './worldPolygons.js';

test('cameraPOV returns the exact midpoint of a two-airport fixture', () => {
  const airports = {
    A: { lat: 0, lon: 0, name: 'A' },
    B: { lat: 10, lon: 20, name: 'B' },
  };
  const pov = cameraPOV(airports);
  assert.strictEqual(pov.lat, 5);
  assert.strictEqual(pov.lng, 10);
});

test('cameraPOV uses every entry, not just the first', () => {
  const base = {
    A: { lat: 0, lon: 0, name: 'A' },
    B: { lat: 10, lon: 10, name: 'B' },
  };
  const withOutlier = {
    ...base,
    C: { lat: 80, lon: -170, name: 'C' },
  };
  const povBase = cameraPOV(base);
  const povOutlier = cameraPOV(withOutlier);
  assert.notStrictEqual(povBase.lat, povOutlier.lat);
  assert.notStrictEqual(povBase.lng, povOutlier.lng);
});

test('cameraPOV is deterministic on repeated calls with the same input', () => {
  const airports = {
    A: { lat: 12.5, lon: -3.25, name: 'A' },
    B: { lat: -40, lon: 100, name: 'B' },
  };
  assert.deepStrictEqual(cameraPOV(airports), cameraPOV(airports));
});

test('cameraPOV throws on an empty object', () => {
  assert.throws(() => cameraPOV({}));
});

test('toCountryFeatures on the real world-atlas topology returns valid Features', () => {
  const features = toCountryFeatures(topology);
  assert.ok(Array.isArray(features));
  assert.ok(features.length > 0);
  for (const f of features) {
    assert.strictEqual(f.type, 'Feature');
    assert.notStrictEqual(f.geometry, null);
  }
});

test('toCountryFeatures throws when the countries object is absent', () => {
  assert.throws(() => toCountryFeatures({ objects: {} }));
});

test('toCountryFeatures throws when the countries object is a single geometry, not a GeometryCollection', () => {
  const singleGeometryTopology = {
    type: 'Topology',
    arcs: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    objects: {
      countries: { type: 'Polygon', arcs: [[0]] },
    },
  };
  assert.throws(() => toCountryFeatures(singleGeometryTopology));
});
