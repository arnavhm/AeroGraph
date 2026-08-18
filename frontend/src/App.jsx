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

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', position: 'relative', margin: 0 }}>
      <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 100 }}>
        <button 
          onClick={() => setViewMode('graph')}
          style={{ 
            marginRight: '5px', 
            padding: '5px 10px', 
            backgroundColor: viewMode === 'graph' ? '#ccc' : '#fff',
            color: '#000',
            border: '1px solid #999',
            cursor: 'pointer'
          }}
        >
          Graph
        </button>
        <button 
          onClick={() => setViewMode('globe')}
          style={{ 
            padding: '5px 10px', 
            backgroundColor: viewMode === 'globe' ? '#ccc' : '#fff',
            color: '#000',
            border: '1px solid #999',
            cursor: 'pointer'
          }}
        >
          Globe
        </button>
      </div>
      
      {viewMode === 'graph' ? (
        <GraphView 
          nodes={nodes} 
          links={links} 
          visibleIds={visibleIds} 
          onNodeClick={handleNodeClick} 
        />
      ) : (
        <GlobeView nodes={nodes} links={links} />
      )}
    </div>
  );
}

export default App;
