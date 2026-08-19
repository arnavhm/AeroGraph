import React, { useState, useEffect, useRef } from 'react';
import GraphView from './GraphView.jsx';
import GlobeView from './GlobeView.jsx';
import { buildAdjacency, seedIds, expand } from './graphModel.js';
import './layout.css';

const NAME_KEY = {
  Airport: 'icao', MaintenanceHub: 'hub_code', Aircraft: 'tail',
  Engine: 'engine_id', FlightRoute: 'flight_no',
};

function App() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  
  const [viewMode, setViewMode] = useState('graph');
  const [visibleIds, setVisibleIds] = useState(new Set());
  const adjacencyRef = useRef(null);

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

        const parsedNodes = resNodes.rows.map(r => ({
          id: r.id,
          label: r.label,
          name: String(r.props?.[NAME_KEY[r.label]] ?? r.label),
          props: r.props
        }));

        const parsedLinks = resLinks.rows.map(r => ({
          source: r.source,
          target: r.target,
          type: r.type
        }));

        setNodes(parsedNodes);
        setLinks(parsedLinks);
        
        const adj = buildAdjacency(parsedLinks);
        adjacencyRef.current = adj;
        
        const seeds = seedIds(parsedNodes);
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

  const handleNodeClick = (node) => {
    if (adjacencyRef.current) {
      const next = expand(visibleIds, adjacencyRef.current, node.id);
      setVisibleIds(next);
    }
  };

  if (loading) return <div>loading</div>;
  if (error) return <div>{error}</div>;

  const VIEWS = [['graph', 'Graph'], ['globe', 'Globe'], ['agent', 'Agent']];

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', margin: 0, display: 'flex', flexDirection: 'column' }}>
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 16px',
        backgroundColor: 'var(--ag-panel)',
        borderBottom: '1px solid var(--ag-border)',
        color: 'var(--ag-text)'
      }}>
        <span>AeroGraph</span>
        <div style={{ display: 'flex', gap: '5px' }}>
          {VIEWS.map(([mode, label]) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                padding: '5px 10px',
                backgroundColor: 'var(--ag-panel)',
                color: viewMode === mode ? 'var(--ag-accent)' : 'var(--ag-text)',
                border: `1px solid ${viewMode === mode ? 'var(--ag-accent)' : 'var(--ag-border)'}`,
                cursor: 'pointer'
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {viewMode === 'graph' ? (
          <GraphView
            nodes={nodes}
            links={links}
            visibleIds={visibleIds}
            onNodeClick={handleNodeClick}
          />
        ) : viewMode === 'globe' ? (
          <GlobeView nodes={nodes} links={links} />
        ) : (
          <div>Agent view</div>
        )}
      </div>
    </div>
  );
}

export default App;
