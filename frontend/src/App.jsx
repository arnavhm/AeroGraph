import React, { useState, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

function get_name(label, props) {
    if (label === "Airport") return props.icao || "Unknown";
    if (label === "MaintenanceHub") return props.hub_code || "Unknown";
    if (label === "Aircraft") return props.tail || "Unknown";
    if (label === "Engine") return String(props.engine_id || "Unknown");
    if (label === "FlightRoute") return props.flight_no || "Unknown";
    return "Unknown";
}

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

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
          name: get_name(r.label, r.props)
        }));

        const links = resLinks.rows.map(r => ({
          source: r.source,
          target: r.target,
          type: r.type
        }));

        setData({ nodes, links });
      } catch (err) {
        setError(err.toString());
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, []);

  if (loading) return <div>loading</div>;
  if (error) return <div>{error}</div>;

  return (
    <ForceGraph2D
      graphData={data}
      nodeLabel="name"
      nodeAutoColorBy="label"
      linkColor={() => '#00ff88'}
      linkWidth={2}
      linkDirectionalArrowLength={4}
    />
  );
}

export default App;
