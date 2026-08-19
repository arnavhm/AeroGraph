import React, { useRef, useMemo, useState, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { normalizeEndpoint } from './graphModel.js';

const TYPE_LABEL = {
  Engine: 'Engine', Aircraft: 'Aircraft', Airport: 'Airport',
  FlightRoute: 'Flight', MaintenanceHub: 'Maintenance hub',
};

// Canvas needs resolved colour strings, not var() references. Resolved once at
// module level; an empty resolution is a failure, never silently defaulted.
const readToken = (name) => {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (value === '') {
    throw new Error(`Design token ${name} resolved to an empty string`);
  }
  return value;
};

const COLOR = {
  critical: readToken('--ag-critical'),
  degrading: readToken('--ag-degrading'),
  healthy: readToken('--ag-healthy'),
  aircraft: readToken('--ag-aircraft'),
  airport: readToken('--ag-airport'),
  flight: readToken('--ag-flight'),
  hub: readToken('--ag-hub'),
  text: readToken('--ag-text'),
  textDim: readToken('--ag-text-dim'),
  link: readToken('--ag-link'),
};

const getNodeColor = (node) => {
  if (node.label === 'Engine') {
    const state = node.props?.risk_state;
    if (state === 'Critical') return COLOR.critical;
    if (state === 'Degrading') return COLOR.degrading;
    if (state === 'Healthy') return COLOR.healthy;
    return COLOR.airport;
  }
  if (node.label === 'Aircraft') return COLOR.aircraft;
  if (node.label === 'Airport') return COLOR.airport;
  if (node.label === 'FlightRoute') return COLOR.flight;
  if (node.label === 'MaintenanceHub') return COLOR.hub;
  return COLOR.airport;
};

export default function GraphView({ nodes, links, visibleIds, onNodeClick }) {
  const fgRef = useRef(null);
  const wrapRef = useRef(null);
  const [size, setSize] = useState(null);

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      if (width > 0 && height > 0) setSize({ width, height });
    });
    observer.observe(wrapRef.current);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(() => ({
    nodes: nodes.filter(n => visibleIds.has(n.id)),
    links: links
      .filter(l => visibleIds.has(normalizeEndpoint(l.source)) && visibleIds.has(normalizeEndpoint(l.target)))
      .map(l => ({ ...l, source: normalizeEndpoint(l.source), target: normalizeEndpoint(l.target) }))
  }), [nodes, links, visibleIds]);

  return (
    <div ref={wrapRef} style={{ position: 'relative', width: '100%', height: '100%', margin: 0 }}>
      <div className="status-text" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '40px', lineHeight: '40px', textAlign: 'center', zIndex: 10, pointerEvents: 'none' }}>
        Showing {visibleIds.size} of {nodes.length} nodes — click a node to expand
      </div>
      {size && <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel="name"
        nodeColor={getNodeColor}
        nodeCanvasObject={(node, ctx, globalScale) => {
          ctx.fillStyle = getNodeColor(node);
          ctx.beginPath();
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
          ctx.fill();

          ctx.fillStyle = COLOR.text;
          ctx.font = `${12 / globalScale}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillText(node.name, node.x, node.y + 8 / globalScale);

          ctx.fillStyle = COLOR.textDim;
          ctx.font = `${9 / globalScale}px sans-serif`;
          ctx.fillText(TYPE_LABEL[node.label] ?? node.label, node.x, node.y + 21 / globalScale);
        }}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        linkColor={() => COLOR.link}
        linkWidth={2}
        linkDirectionalArrowLength={4}
        onNodeClick={onNodeClick}
        width={size.width}
        height={size.height}
      />}
    </div>
  );
}
