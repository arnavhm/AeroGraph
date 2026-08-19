import { test } from 'node:test';
import assert from 'node:assert';
import { resultFields, divergenceState, DIVERGENCE } from './agentModel.js';

// Verbatim rows array from the Phase 1 V1 capture (/tmp/ask_v1.json,
// 2026-08-19). Used as a shape fixture; assertions reference the fixture's own
// keys and values, never a free-standing "correct" tail or score.
const V1_ROWS = [
  {
    aircraftTail: 'G-AGDB',
    flightNumber: 'AG102',
    engineRiskScore: 0.6506809730737231,
  },
];

// Both V2 captures (cached and uncached) returned rows: [] — the live case.
const V2_ROWS = [];

// Derived fixtures: the real V1 row's structure — three keys, string/string/
// number value types — with obviously synthetic values so no reader mistakes
// them for captured results.
const SYNTH_ROW_A = [
  { aircraftTail: 'FIXTURE-A', flightNumber: 'FIXTURE-FLIGHT', engineRiskScore: 1111 },
];
const SYNTH_ROW_B = [
  { aircraftTail: 'FIXTURE-B', flightNumber: 'FIXTURE-FLIGHT', engineRiskScore: 2222 },
];

test('resultFields on the real V1 rows returns one entry per key, in source order', () => {
  const fields = resultFields(V1_ROWS);
  assert.deepStrictEqual(
    fields.map((f) => f.key),
    Object.keys(V1_ROWS[0])
  );
  for (const { key, value } of fields) {
    assert.strictEqual(value, V1_ROWS[0][key]);
  }
});

test('resultFields on [], null, and undefined each return []', () => {
  assert.deepStrictEqual(resultFields([]), []);
  assert.deepStrictEqual(resultFields(null), []);
  assert.deepStrictEqual(resultFields(undefined), []);
});

test('resultFields stringifies a nested object value rather than returning the object', () => {
  // Real V1 row structure with one value replaced by a nested object —
  // the shape V2's generated Cypher can produce via COLLECT(...).
  const rows = [
    {
      aircraftTail: 'FIXTURE-A',
      suggestions: [{ tail: 'FIXTURE-B', hub: 'FIXTURE-HUB' }],
    },
  ];
  const fields = resultFields(rows);
  const suggestions = fields.find((f) => f.key === 'suggestions');
  assert.strictEqual(typeof suggestions.value, 'string');
  assert.deepStrictEqual(JSON.parse(suggestions.value), rows[0].suggestions);
});

test('divergenceState returns both-empty when neither side has rows', () => {
  assert.strictEqual(divergenceState([], []), DIVERGENCE.BOTH_EMPTY);
  assert.strictEqual(divergenceState(null, undefined), DIVERGENCE.BOTH_EMPTY);
});

test('divergenceState returns one-empty when exactly one side has rows', () => {
  // The live Phase 1 capture: V1 returned a row, V2 returned [].
  assert.strictEqual(divergenceState(V1_ROWS, V2_ROWS), DIVERGENCE.ONE_EMPTY);
  assert.strictEqual(divergenceState(V2_ROWS, V1_ROWS), DIVERGENCE.ONE_EMPTY);
});

test('divergenceState returns differ when both have rows and first rows differ', () => {
  assert.strictEqual(divergenceState(SYNTH_ROW_A, SYNTH_ROW_B), DIVERGENCE.DIFFER);
});

test('divergenceState returns agree when both first rows are deep-equal', () => {
  assert.strictEqual(divergenceState(SYNTH_ROW_A, [{ ...SYNTH_ROW_A[0] }]), DIVERGENCE.AGREE);
});

test('divergenceState returns agree for identical content with different key insertion order', () => {
  const ordered = [
    { aircraftTail: 'FIXTURE-A', flightNumber: 'FIXTURE-FLIGHT', engineRiskScore: 1111 },
  ];
  const reordered = [
    { engineRiskScore: 1111, aircraftTail: 'FIXTURE-A', flightNumber: 'FIXTURE-FLIGHT' },
  ];
  assert.strictEqual(divergenceState(ordered, reordered), DIVERGENCE.AGREE);
});
