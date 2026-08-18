/**
 * This is a diagnostic requiring a running API and a running Aura instance;
 * it is NOT part of the test suite and node --test must never pick it up.
 * Filename deliberately ends .mjs and not .test.mjs for that reason.
 */
import { buildAdjacency, seedIds, expand } from './graphModel.js';

async function run() {
  const resNodes = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'MATCH (n) RETURN elementId(n) AS id, labels(n)[0] AS label, n AS props' })
  }).then(r => r.json());

  const resLinks = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'MATCH (a)-[r]->(b) RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type' })
  }).then(r => r.json());

  const nodes = resNodes.rows.map(r => ({
    id: r.id,
    label: r.label,
    props: r.props
  }));
  const links = resLinks.rows;

  const adj = buildAdjacency(links);
  const seeds = seedIds(nodes);

  console.log("node count:", nodes.length);
  console.log("adjacency map size:", adj.size);
  console.log("seed count:", seeds.size);

  const seedEngineIds = nodes.filter(n => seeds.has(n.id)).map(n => n.props.engine_id);
  console.log("seed engine_id list:");
  for (const eid of seedEngineIds) {
    console.log("  " + eid);
  }

  let visible = new Set(seeds);
  let prevSize;
  do {
    prevSize = visible.size;
    const currentIds = Array.from(visible);
    for (const id of currentIds) {
      visible = expand(visible, adj, id);
    }
  } while (visible.size > prevSize);

  console.log("transitive closure size from all seeds:", visible.size);
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
