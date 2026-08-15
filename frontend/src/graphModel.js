export function normalizeEndpoint(v) {
  return v && typeof v === 'object' && 'id' in v ? v.id : v;
}

export function buildAdjacency(links) {
  const adjacency = new Map();
  for (const link of links) {
    const sourceId = normalizeEndpoint(link.source);
    const targetId = normalizeEndpoint(link.target);
    if (!adjacency.has(sourceId)) adjacency.set(sourceId, new Set());
    if (!adjacency.has(targetId)) adjacency.set(targetId, new Set());
    adjacency.get(sourceId).add(targetId);
    adjacency.get(targetId).add(sourceId);
  }
  return adjacency;
}

export function seedIds(nodes) {
  const seeds = new Set();
  for (const node of nodes) {
    if (node.label === 'Engine' && node.props && node.props.risk_state === 'Critical') {
      seeds.add(node.id);
    }
  }
  return seeds;
}

export function expand(visibleIds, adjacency, clickedId) {
  const newSet = new Set(visibleIds);
  const neighbours = adjacency.get(clickedId);
  if (neighbours) {
    for (const neighbor of neighbours) {
      newSet.add(neighbor);
    }
  }
  return newSet;
}
