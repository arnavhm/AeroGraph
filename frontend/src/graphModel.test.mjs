import { test } from 'node:test';
import assert from 'node:assert';
import { normalizeEndpoint, buildAdjacency, seedIds, expand } from './graphModel.js';

test('A1 buildAdjacency is undirected', () => {
  const links = [{ source: 'x', target: 'y' }];
  const adj = buildAdjacency(links);
  assert.ok(adj.get('x').has('y'));
  assert.ok(adj.get('y').has('x'));
});

test('A2 normalizeEndpoint handles both shapes', () => {
  assert.strictEqual(normalizeEndpoint('x'), 'x');
  assert.strictEqual(normalizeEndpoint({ id: 'x' }), 'x');
});

test('A3 buildAdjacency works when endpoints are objects', () => {
  const links = [{ source: { id: 'a' }, target: { id: 'b' } }];
  const adj = buildAdjacency(links);
  assert.ok(adj.get('a').has('b'));
  assert.ok(adj.get('b').has('a'));
});

test('A4 seedIds selects Critical engines only', () => {
  const nodes = [
    { id: '1', label: 'Engine', props: { risk_state: 'Critical' } },
    { id: '2', label: 'Engine', props: { risk_state: 'Degrading' } },
    { id: '3', label: 'Engine', props: { risk_state: 'Healthy' } },
    { id: '4', label: 'Airport', props: { risk_state: 'Critical' } }
  ];
  const seeds = seedIds(nodes);
  assert.strictEqual(seeds.size, 1);
  assert.ok(seeds.has('1'));
});

test('A5 expand does not mutate its input Set', () => {
  const visible = new Set(['x']);
  const adj = new Map([['x', new Set(['y'])]]);
  const newVisible = expand(visible, adj, 'x');
  assert.strictEqual(visible.size, 1);
  assert.ok(visible.has('x'));
  assert.strictEqual(newVisible.size, 2);
  assert.ok(newVisible.has('y'));
});

test('A6 expand on an unknown id returns a Set equal to the input', () => {
  const visible = new Set(['x']);
  const adj = new Map([['x', new Set(['y'])]]);
  const newVisible = expand(visible, adj, 'z');
  assert.strictEqual(newVisible.size, 1);
  assert.ok(newVisible.has('x'));
  assert.notStrictEqual(newVisible, visible);
});

test('A7 Component isolation', () => {
  const links = [
    { source: 'P', target: 'Q' },
    { source: 'Q', target: 'R' },
    { source: 'R', target: 'S' },
    { source: 'X', target: 'Y' },
    { source: 'Y', target: 'Z' }
  ];
  const adj = buildAdjacency(links);
  let visible = new Set(['P']);
  
  let prevSize;
  do {
    prevSize = visible.size;
    const currentIds = Array.from(visible);
    for (const id of currentIds) {
      visible = expand(visible, adj, id);
    }
  } while (visible.size > prevSize);

  assert.strictEqual(visible.size, 4);
  assert.ok(visible.has('P'));
  assert.ok(visible.has('Q'));
  assert.ok(visible.has('R'));
  assert.ok(visible.has('S'));
  assert.strictEqual(visible.has('X'), false);
  assert.strictEqual(visible.has('Y'), false);
  assert.strictEqual(visible.has('Z'), false);
});

test('A8 seed-plus-one-ring initial set', () => {
  const nodes = [
    { id: 'e1', label: 'Engine', props: { risk_state: 'Critical' } },
    { id: 'e2', label: 'Engine', props: { risk_state: 'Healthy' } },
    { id: 'a1', label: 'Aircraft' },
    { id: 'f1', label: 'FlightRoute' }
  ];
  const links = [
    { source: 'e1', target: 'a1' },
    { source: 'a1', target: 'f1' },
    { source: 'e2', target: 'a1' }
  ];
  const seeds = seedIds(nodes);
  const adj = buildAdjacency(links);
  
  let visible = new Set(seeds);
  for (const seed of seeds) {
    visible = expand(visible, adj, seed);
  }
  
  assert.strictEqual(visible.size, 2);
  assert.ok(visible.has('e1'));
  assert.ok(visible.has('a1'));
  assert.strictEqual(visible.has('f1'), false);
  assert.strictEqual(visible.has('e2'), false);
});
