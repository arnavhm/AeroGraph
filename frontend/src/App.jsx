import React, { useState, useEffect, useRef, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { buildAdjacency, seedIds, expand, normalizeEndpoint } from './graphModel.js';
import './layout.css';

const NAME_KEY = {
  Airport: 'icao', MaintenanceHub: 'hub_code', Aircraft: 'tail',
  Engine: 'engine_id', FlightRoute: 'flight_no',
};

const TYPE_LABEL = {
  Engine: 'Engine', Aircraft: 'Aircraft', Airport: 'Airport',
  FlightRoute: 'Flight', MaintenanceHub: 'Maintenance hub',
};

function App() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const rawNodes = useRef([]);
  const rawLinks = useRef([]);
  const adjacencyRef = useRef(null);
  const [visibleIds, setVisibleIds] = useState(new Set());
  const fgRef = useRef(null);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const resNodes = await fetch('http://localhost:8000/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'MATCH (n) RETURN elementId(n) AS id, labels(n)[0] AS label, n AS props' })
        }).then(r => r.json());

        if (!resNodes.ok) {
          setError(resNodes.error || "Query rejected");
          setLoading(false);
          return;
        }

        const resLinks = await fetch('http://localhost:8000/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'MATCH (a)-[r]->(b) RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type' })
        }).then(r => r.json());

        if (!resLinks.ok) {
          setError(resLinks.error || "Query rejected");
          setLoading(false);
          return;
        }

        const nodes = resNodes.rows.map(r => ({
          id: r.id,
          label: r.label,
          name: String(r.props?.[NAME_KEY[r.label]] ?? r.label),
          props: r.props
        }));

        const links = resLinks.rows.map(r => ({
          source: r.source,
          target: r.target,
          type: r.type
        }));

        rawNodes.current = nodes;
        rawLinks.current = links;
        
        const adj = buildAdjacency(links);
        adjacencyRef.current = adj;
        
        const seeds = seedIds(nodes);
        let initialVisible = new Set(seeds);
        for (const seed of seeds) {
          initialVisible = expand(initialVisible, adj, seed);
        }
        setVisibleIds(initialVisible);
      } catch (err) {
        setError(err.toString());
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, []);

  const graphData = useMemo(() => ({
    nodes: rawNodes.current.filter(n => visibleIds.has(n.id)),
    links: rawLinks.current
      .filter(l => visibleIds.has(normalizeEndpoint(l.source)) && visibleIds.has(normalizeEndpoint(l.target)))
      .map(l => ({ ...l, source: normalizeEndpoint(l.source), target: normalizeEndpoint(l.target) }))
  }), [visibleIds]);

  if (loading) return <div>loading</div>;
  if (error) return <div>{error}</div>;

  const getNodeColor = (node) => {
    if (node.label === 'Engine') {
      const state = node.props?.risk_state;
      if (state === 'Critical') return '#ff4d4f';
      if (state === 'Degrading') return '#ffa940';
      if (state === 'Healthy') return '#52c41a';
      return '#8fa3b8';
    }
    if (node.label === 'Aircraft') return '#b8c4d0';
    if (node.label === 'Airport') return '#8fa3b8';
    if (node.label === 'FlightRoute') return '#6b7a8a';
    if (node.label === 'MaintenanceHub') return '#566473';
    return '#8fa3b8';
  };

  const handleNodeClick = (node) => {
    const next = expand(visibleIds, adjacencyRef.current, node.id);
    setVisibleIds(next);
  };

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', margin: 0 }}>
      <div className="status-text" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '40px', lineHeight: '40px', textAlign: 'center', zIndex: 10, pointerEvents: 'none' }}>
        Showing {visibleIds.size} of {rawNodes.current.length} nodes — click a node to expand
      </div>
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel="name"
        nodeColor={getNodeColor}
        nodeCanvasObject={(node, ctx, globalScale) => {
          ctx.fillStyle = getNodeColor(node);
          ctx.beginPath();
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
          ctx.fill();

          ctx.fillStyle = '#e8eaed';
          ctx.font = `${12 / globalScale}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillText(node.name, node.x, node.y + 8 / globalScale);

          ctx.fillStyle = '#8b93a1';
          ctx.font = `${9 / globalScale}px sans-serif`;
          ctx.fillText(TYPE_LABEL[node.label] ?? node.label, node.x, node.y + 21 / globalScale);
        }}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        linkColor={() => '#4a5462'}
        linkWidth={2}
        linkDirectionalArrowLength={4}
        onNodeClick={handleNodeClick}
        width={window.innerWidth}
        height={window.innerHeight}
      />
    </div>
  );
}

export default App;
