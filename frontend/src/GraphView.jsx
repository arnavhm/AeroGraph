import React, { useRef, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { normalizeEndpoint } from './graphModel.js';

const TYPE_LABEL = {
  Engine: 'Engine', Aircraft: 'Aircraft', Airport: 'Airport',
  FlightRoute: 'Flight', MaintenanceHub: 'Maintenance hub',
};

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

export default function GraphView({ nodes, links, visibleIds, onNodeClick }) {
  const fgRef = useRef(null);

  const graphData = useMemo(() => ({
    nodes: nodes.filter(n => visibleIds.has(n.id)),
    links: links
      .filter(l => visibleIds.has(normalizeEndpoint(l.source)) && visibleIds.has(normalizeEndpoint(l.target)))
      .map(l => ({ ...l, source: normalizeEndpoint(l.source), target: normalizeEndpoint(l.target) }))
  }), [nodes, links, visibleIds]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', margin: 0 }}>
      <div className="status-text" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '40px', lineHeight: '40px', textAlign: 'center', zIndex: 10, pointerEvents: 'none' }}>
        Showing {visibleIds.size} of {nodes.length} nodes — click a node to expand
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
        onNodeClick={onNodeClick}
        width={window.innerWidth}
        height={window.innerHeight}
      />
    </div>
  );
}
