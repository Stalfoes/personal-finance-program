import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Settings, RefreshCw, ZoomIn, ZoomOut, DollarSign, PieChart, ArrowRight } from 'lucide-react';

// --- MOCK DATA ---
const MOCK_NODES = [
  { id: 'salary', label: 'Primary Salary', value: 6500, type: 'income', col: 0 },
  { id: 'side_hustle', label: 'Side Hustle', value: 1200, type: 'income', col: 0 },
  { id: 'checking', label: 'Checking Account', value: 7700, type: 'account', col: 1 },
  { id: 'housing', label: 'Housing & Utilities', value: 2400, type: 'expense', col: 2 },
  { id: 'food', label: 'Groceries & Dining', value: 1100, type: 'expense', col: 2 },
  { id: 'savings', label: 'High Yield Savings', value: 1500, type: 'savings', col: 2 },
  { id: 'investments', label: 'Brokerage / IRA', value: 1200, type: 'investments', col: 2 },
  { id: 'lifestyle', label: 'Lifestyle & Fun', value: 1500, type: 'expense', col: 2 },
];

const MOCK_LINKS = [
  { source: 'salary', target: 'checking', value: 6500 },
  { source: 'side_hustle', target: 'checking', value: 1200 },
  { source: 'checking', target: 'housing', value: 2400 },
  { source: 'checking', target: 'food', value: 1100 },
  { source: 'checking', target: 'savings', value: 1500 },
  { source: 'checking', target: 'investments', value: 1200 },
  { source: 'checking', target: 'lifestyle', value: 1500 },
];

// --- UTILS ---
const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

// Color mapping for nodes based on type
const NODE_COLORS = {
  income: { fill: '#dcfce7', stroke: '#22c55e', text: '#166534' },      // Green
  account: { fill: '#dbeafe', stroke: '#3b82f6', text: '#1e40af' },     // Blue
  expense: { fill: '#fee2e2', stroke: '#ef4444', text: '#991b1b' },     // Red
  savings: { fill: '#f3e8ff', stroke: '#a855f7', text: '#6b21a8' },     // Purple
  investments: { fill: '#fef08a', stroke: '#eab308', text: '#854d0e' }, // Yellow
};

export default function App() {
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoveredLink, setHoveredLink] = useState(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 1000, height: 600 });
  const [tension, setTension] = useState(0.4); // For bezier curve shape

  // Responsive SVG wrapper
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Compute node layouts dynamically
  const layout = useMemo(() => {
    const { width, height } = dimensions;
    
    // Group nodes by column
    const cols = [];
    MOCK_NODES.forEach(node => {
      if (!cols[node.col]) cols[node.col] = [];
      cols[node.col].push(node);
    });

    const colWidth = width / (cols.length || 1);
    const nodesWithPositions = MOCK_NODES.map(node => {
      const colNodes = cols[node.col];
      const indexInCol = colNodes.indexOf(node);
      
      // Distribute nodes evenly on the Y axis within their column
      const ySpacing = height / (colNodes.length + 1);
      const y = ySpacing * (indexInCol + 1);
      
      // Center the columns on the X axis
      const x = (colWidth * node.col) + (colWidth / 2);

      // Area of circle proportional to value: Area = pi * r^2 -> r = sqrt(Area/pi)
      // Base scale factor so they look nice on screen
      const areaScale = 1.2; 
      const radius = Math.max(25, Math.sqrt(node.value / Math.PI) * areaScale);

      return { ...node, x, y, radius };
    });

    // Create a quick lookup map
    const nodeMap = nodesWithPositions.reduce((acc, n) => ({ ...acc, [n.id]: n }), {});

    // Compute link paths
    const linksWithPaths = MOCK_LINKS.map(link => {
      const source = nodeMap[link.source];
      const target = nodeMap[link.target];
      
      // Calculate link stroke width (linear mapping so it's visible but respects volume)
      // A pure volume mapping might make small expenses invisible, so we use a min width + scaling
      const strokeWidth = Math.max(4, (link.value / 7700) * 40);

      // standard cubic bezier curve logic for smooth horizontal flows
      const controlPointXOffset = (target.x - source.x) * tension;
      const d = `M ${source.x} ${source.y} C ${source.x + controlPointXOffset} ${source.y}, ${target.x - controlPointXOffset} ${target.y}, ${target.x} ${target.y}`;

      // Calculate the midpoint for the label (approximation using standard bezier logic)
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;

      return { ...link, sourceNode: source, targetNode: target, strokeWidth, d, midX, midY };
    });

    return { nodes: nodesWithPositions, links: linksWithPaths };
  }, [dimensions, tension]);

  // Determine opacity states based on hover
  const getLinkOpacity = (link) => {
    if (!hoveredNode && !hoveredLink) return 0.3;
    if (hoveredLink === link) return 0.7;
    if (hoveredNode && (link.source === hoveredNode.id || link.target === hoveredNode.id)) return 0.6;
    return 0.05;
  };

  const getNodeOpacity = (node) => {
    if (!hoveredNode && !hoveredLink) return 1;
    if (hoveredNode === node) return 1;
    if (hoveredLink && (hoveredLink.source === node.id || hoveredLink.target === node.id)) return 1;
    
    // Check if connected to hovered node
    if (hoveredNode) {
      const isConnected = layout.links.some(l => 
        (l.source === hoveredNode.id && l.target === node.id) || 
        (l.target === hoveredNode.id && l.source === node.id)
      );
      if (isConnected) return 0.9;
    }
    return 0.3;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-4 sm:p-8 font-sans">
      {/* Header Area */}
      <div className="max-w-6xl mx-auto mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <PieChart className="text-blue-600" size={28} />
            Cash Flow Explorer
          </h1>
          <p className="text-slate-500 mt-1">Visualize your money as interconnected pools.</p>
        </div>
        
        {/* Controls */}
        <div className="flex bg-white rounded-lg p-1 border border-slate-200 shadow-sm">
          <div className="px-3 py-1 text-sm font-medium text-slate-500 border-r border-slate-100 flex items-center gap-2">
            Curve Style
          </div>
          <button 
            onClick={() => setTension(0.2)}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${tension === 0.2 ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Direct
          </button>
          <button 
            onClick={() => setTension(0.5)}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${tension === 0.5 ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Flowing
          </button>
        </div>
      </div>

      {/* Main Diagram Area */}
      <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden relative">
        
        {/* Quick Stats Overlay (Optional context for a finance app) */}
        <div className="absolute top-6 left-6 flex gap-4 pointer-events-none z-10">
           <div className="bg-white/80 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-200 shadow-sm">
             <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Total In</div>
             <div className="text-xl font-bold text-green-600">$7,700</div>
           </div>
           <div className="bg-white/80 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-200 shadow-sm">
             <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Total Out</div>
             <div className="text-xl font-bold text-blue-600">$7,700</div>
           </div>
        </div>

        {/* Drawing Canvas */}
        <div ref={containerRef} className="w-full h-[650px] cursor-crosshair">
          <svg width="100%" height="100%" className="block">
            <defs>
              {/* Optional: Define gradients for links */}
              {layout.links.map((link, i) => (
                <linearGradient key={`grad-${i}`} id={`grad-${link.source}-${link.target}`} x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={NODE_COLORS[link.sourceNode.type].stroke} />
                  <stop offset="100%" stopColor={NODE_COLORS[link.targetNode.type].stroke} />
                </linearGradient>
              ))}
            </defs>

            {/* Render Links (Paths) */}
            {layout.links.map((link, i) => (
              <g key={`link-group-${i}`}>
                {/* The actual flow curve */}
                <path
                  d={link.d}
                  fill="none"
                  stroke={`url(#grad-${link.source}-${link.target})`}
                  strokeWidth={link.strokeWidth}
                  strokeLinecap="round"
                  opacity={getLinkOpacity(link)}
                  className="transition-opacity duration-300 ease-in-out"
                  onMouseEnter={() => setHoveredLink(link)}
                  onMouseLeave={() => setHoveredLink(null)}
                  style={{ cursor: 'pointer' }}
                />
                
                {/* The edge label container (rendered via foreignObject to use normal HTML/Tailwind) */}
                <foreignObject
                  x={link.midX - 45} // Offset by half the width to center
                  y={link.midY - 14} // Offset by half the height to center
                  width={90}
                  height={28}
                  className={`overflow-visible transition-opacity duration-300 pointer-events-none ${
                    hoveredNode || hoveredLink 
                      ? (getLinkOpacity(link) > 0.3 ? 'opacity-100 z-50' : 'opacity-0')
                      : 'opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-center w-full h-full">
                    <span className="flex items-center justify-center px-2 py-1 text-[11px] sm:text-xs font-bold text-slate-600 bg-white/95 backdrop-blur-sm border border-slate-200 rounded-full shadow-sm">
                      {formatCurrency(link.value)}
                    </span>
                  </div>
                </foreignObject>
              </g>
            ))}

            {/* Render Nodes (Circles) */}
            {layout.nodes.map((node) => {
              const colors = NODE_COLORS[node.type];
              const isHovered = hoveredNode === node;
              const opacity = getNodeOpacity(node);
              
              return (
                <g 
                  key={`node-${node.id}`} 
                  transform={`translate(${node.x}, ${node.y})`}
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: 'pointer', opacity, transition: 'opacity 0.3s ease-in-out' }}
                >
                  {/* Outer glow ring for interaction */}
                  <circle
                    r={node.radius + 6}
                    fill="none"
                    stroke={colors.stroke}
                    strokeWidth="2"
                    opacity={isHovered ? 0.3 : 0}
                    className="transition-opacity duration-300"
                  />
                  
                  {/* Main Circle */}
                  <circle
                    r={node.radius}
                    fill={colors.fill}
                    stroke={colors.stroke}
                    strokeWidth="3"
                    className="shadow-xl"
                  />

                  {/* Inside Circle Value (Only if circle is large enough) */}
                  {node.radius > 35 && (
                    <text
                      y={4}
                      textAnchor="middle"
                      fill={colors.text}
                      className="text-sm font-bold pointer-events-none"
                    >
                      {formatCurrency(node.value)}
                    </text>
                  )}

                  {/* Node Label (Positioned above or below depending on column) */}
                  <text
                    y={node.radius > 35 ? node.radius + 20 : node.radius + 15}
                    textAnchor="middle"
                    fill="#334155"
                    className="text-xs sm:text-sm font-semibold pointer-events-none drop-shadow-sm"
                  >
                    {node.label}
                  </text>
                  
                  {/* Fallback Value display if circle was too small */}
                  {node.radius <= 35 && (
                     <text
                     y={node.radius + 32}
                     textAnchor="middle"
                     fill="#64748b"
                     className="text-xs font-medium pointer-events-none"
                   >
                     {formatCurrency(node.value)}
                   </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Description / Instructions */}
      <div className="max-w-6xl mx-auto mt-6 text-center text-slate-500 text-sm">
        <p>Hover over any pool or flow to isolate its connections. Edge amounts are placed at the exact midpoint of the curve.</p>
      </div>
    </div>
  );
}