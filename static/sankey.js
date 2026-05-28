// --- STATE & UTILS ---
let currentTension = 0.5; // Default flowing
let hoveredNode = null;
let hoveredLink = null;

// Store calculated layout so hover functions can access topology
let currentLayout = { nodes: [], links: [] }; 

const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

const NODE_COLORS = {
    income: { fill: '#dcfce7', stroke: '#22c55e', text: '#166534' },      // Green
    asset: { fill: '#dbeafe', stroke: '#3b82f6', text: '#1e40af' },       // Blue
    expense: { fill: '#fee2e2', stroke: '#ef4444', text: '#991b1b' },     // Red
    equity: { fill: '#f3e8ff', stroke: '#a855f7', text: '#6b21a8' },      // Purple
    liability: { fill: '#fef08a', stroke: '#eab308', text: '#854d0e' },   // Yellow
};

// --- MAIN RENDER FUNCTION ---
function renderSankeyDiagram() {
    // 1. Get raw data from the DOM (acts as our state store, updatable by HTMX)
    const dataScript = document.getElementById('chart-data');
    if (!dataScript) return;
    
    const rawData = JSON.parse(dataScript.textContent);
    const rawNodes = JSON.parse(JSON.stringify(rawData.nodes)); // Deep copy to avoid mutating source
    const rawLinks = JSON.parse(JSON.stringify(rawData.links));

    // 2. Get container dimensions
    const container = document.getElementById('chart-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // --- DYNAMIC SCALING ---
    // Find the highest values in the dataset to dynamically set the visual ceilings
    const maxNodeValue = d3.max(rawNodes, d => d.value) || 1;
    const maxLinkValue =  d3.max(rawLinks, d => d.value) || 1;
    console.log(maxNodeValue, maxLinkValue)

    // scaleSqrt maps the values to a radius, meaning the AREA of the circle 
    // scales linearly. Max radius is capped at 85px regardless of dollar amount.
    const radiusScale = d3.scalePow()
        .domain([0, maxNodeValue])
        .range([20, 85])
        .exponent(1);

    // scaleLinear maps link values to line thickness. Max thickness is 45px.
    const strokeScale = d3.scaleLinear()
        .domain([0, maxLinkValue])
        .range([4, 45]);

    // 3. Compute Layout Math
    const cols = [];
    rawNodes.forEach(node => {
        if (!cols[node.col]) cols[node.col] = [];
        cols[node.col].push(node);
    });

    const colWidth = width / (cols.length || 1);
    
    const nodesWithPositions = rawNodes.map(node => {
        const colNodes = cols[node.col];
        const indexInCol = colNodes.indexOf(node);
        
        // Distribute nodes evenly on the Y axis
        const ySpacing = height / (colNodes.length + 1);
        const y = ySpacing * (indexInCol + 1);
        
        // Center columns on X axis
        const x = (colWidth * node.col) + (colWidth / 2);

        // Apply our dynamic D3 scale!
        const radius = radiusScale(node.value);

        return { ...node, x, y, radius };
    });

    const nodeMap = nodesWithPositions.reduce((acc, n) => ({ ...acc, [n.id]: n }), {});

    const linksWithPaths = rawLinks.map(link => {
        const source = nodeMap[link.source];
        const target = nodeMap[link.target];
        
        // Apply our dynamic line thickness scale!
        const strokeWidth = strokeScale(link.value);
        
        const controlPointXOffset = (target.x - source.x) * currentTension;
        const d = `M ${source.x} ${source.y} C ${source.x + controlPointXOffset} ${source.y}, ${target.x - controlPointXOffset} ${target.y}, ${target.x} ${target.y}`;
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;

        return { ...link, sourceNode: source, targetNode: target, strokeWidth, d, midX, midY };
    });

    currentLayout = { nodes: nodesWithPositions, links: linksWithPaths };

    // Update Quick Stats overlay
    const totalIn = rawNodes.filter(n => n.type === 'income').reduce((sum, n) => sum + n.value, 0);
    const totalOut = rawLinks.filter(l => nodeMap[l.target].type !== 'asset').reduce((sum, l) => sum + l.value, 0);
    document.getElementById('stat-total-in').innerText = formatCurrency(totalIn);
    document.getElementById('stat-total-out').innerText = formatCurrency(totalOut);

    // --- D3 DRAWING LOGIC ---
    const svg = d3.select("#d3-svg");
    svg.selectAll("*").remove(); // Clear previous drawing

    // Define Gradients
    const defs = svg.append("defs");
    linksWithPaths.forEach((link, i) => {
        const grad = defs.append("linearGradient")
            .attr("id", `grad-${link.source}-${link.target}`)
            .attr("gradientUnits", "userSpaceOnUse")
            .attr("x1", "0%").attr("y1", "0%")
            .attr("x2", "100%").attr("y2", "0%");
        grad.append("stop")
            .attr("offset", "0%")
            .attr("stop-color", NODE_COLORS[link.sourceNode.type].stroke);
        grad.append("stop")
            .attr("offset", "100%")
            .attr("stop-color", NODE_COLORS[link.targetNode.type].stroke);
    });

    // 1. Draw Links
    const linkGroup = svg.append("g").attr("class", "links-layer");
    
    const linkElements = linkGroup.selectAll(".link-path")
        .data(linksWithPaths)
        .enter()
        .append("path")
        .attr("class", "link-path")
        .attr("d", d => d.d)
        .attr("fill", "none")
        .attr("stroke", d => `url(#grad-${d.source}-${d.target})`)
        .attr("stroke-width", d => d.strokeWidth)
        .attr("stroke-linecap", "round")
        .attr("opacity", 0.3)
        .on("mouseenter", (event, d) => { hoveredLink = d; updateHighlights(); })
        .on("mouseleave", () => { hoveredLink = null; updateHighlights(); });

    // 2. Draw Link Labels (ForeignObjects)
    const labelGroup = svg.append("g").attr("class", "labels-layer");

    const labelElements = labelGroup.selectAll(".link-label")
        .data(linksWithPaths)
        .enter()
        .append("foreignObject")
        .attr("class", "link-label overflow-visible")
        .attr("x", d => d.midX - 45)
        .attr("y", d => d.midY - 14)
        .attr("width", 90)
        .attr("height", 28)
        .attr("opacity", 1);

    labelElements.append("xhtml:div")
        .attr("class", "flex items-center justify-center w-full h-full")
        .html(d => `
            <span class="flex items-center justify-center px-2 py-1 text-[11px] sm:text-xs font-bold text-slate-600 bg-white/95 backdrop-blur-sm border border-slate-200 rounded-full shadow-sm">
                ${formatCurrency(d.value)}
            </span>
        `);

    // 3. Draw Nodes
    const nodeGroupLayer = svg.append("g").attr("class", "nodes-layer");

    const nodes = nodeGroupLayer.selectAll(".node-group")
        .data(nodesWithPositions)
        .enter()
        .append("g")
        .attr("class", "node-group")
        .attr("transform", d => `translate(${d.x}, ${d.y})`)
        .on("mouseenter", (event, d) => { hoveredNode = d; updateHighlights(); })
        .on("mouseleave", () => { hoveredNode = null; updateHighlights(); });

    // Node Outer Glow
    nodes.append("circle")
        .attr("class", "node-glow")
        .attr("r", d => d.radius + 6)
        .attr("fill", "none")
        .attr("stroke", d => NODE_COLORS[d.type].stroke)
        .attr("stroke-width", 2)
        .attr("opacity", 0);

    // Node Main Circle
    nodes.append("circle")
        .attr("r", d => d.radius)
        .attr("fill", d => NODE_COLORS[d.type].fill)
        .attr("stroke", d => NODE_COLORS[d.type].stroke)
        .attr("stroke-width", 3)
        .attr("class", "drop-shadow-md");

    // Node Inner Text (Value)
    nodes.filter(d => d.radius > 35)
        .append("text")
        .attr("y", 4)
        .attr("text-anchor", "middle")
        .attr("fill", d => NODE_COLORS[d.type].text)
        .attr("class", "text-sm font-bold pointer-events-none")
        .text(d => formatCurrency(d.value));

    // Node Outer Text (Label)
    nodes.append("text")
        .attr("y", d => d.radius > 35 ? d.radius + 20 : d.radius + 15)
        .attr("text-anchor", "middle")
        .attr("fill", "#334155")
        .attr("class", "text-xs sm:text-sm font-semibold pointer-events-none drop-shadow-sm")
        .text(d => d.label);

    // Node Fallback Text (If circle too small)
    nodes.filter(d => d.radius <= 35)
        .append("text")
        .attr("y", d => d.radius + 32)
        .attr("text-anchor", "middle")
        .attr("fill", "#64748b")
        .attr("class", "text-xs font-medium pointer-events-none")
        .text(d => formatCurrency(d.value));

    // Initial Highlight state evaluation
    updateHighlights();
}

// --- INTERACTIVITY / HIGHLIGHT LOGIC ---
function updateHighlights() {
    // Helper function to check connections
    const isConnected = (nodeA, nodeB) => {
        return currentLayout.links.some(l => 
            (l.source === nodeA.id && l.target === nodeB.id) || 
            (l.target === nodeA.id && l.source === nodeB.id)
        );
    };

    // 1. Update Link Opacities
    d3.selectAll(".link-path").attr("opacity", d => {
        if (!hoveredNode && !hoveredLink) return 0.3;
        if (hoveredLink === d) return 0.7;
        if (hoveredNode && (d.source === hoveredNode.id || d.target === hoveredNode.id)) return 0.6;
        return 0.05;
    });

    // 2. Update Label Opacities (Mirroring Links logic exactly)
    d3.selectAll(".link-label").attr("opacity", d => {
        if (!hoveredNode && !hoveredLink) return 1.0; // Labels visible by default
        
        let linkOpacity;
        if (hoveredLink === d) linkOpacity = 0.7;
        else if (hoveredNode && (d.source === hoveredNode.id || d.target === hoveredNode.id)) linkOpacity = 0.6;
        else linkOpacity = 0.05;

        return linkOpacity > 0.3 ? 1.0 : 0.0;
    });

    // 3. Update Node Opacities
    d3.selectAll(".node-group").attr("opacity", d => {
        if (!hoveredNode && !hoveredLink) return 1;
        if (hoveredNode === d) return 1;
        if (hoveredLink && (hoveredLink.source === d.id || hoveredLink.target === d.id)) return 1;
        if (hoveredNode && isConnected(hoveredNode, d)) return 0.9;
        return 0.3;
    });

    // 4. Toggle Node Glow
    d3.selectAll(".node-glow").attr("opacity", d => d === hoveredNode ? 0.3 : 0);
}

// --- SETUP & EVENT LISTENERS ---
function initSankey() {
    const container = document.getElementById("chart-container");
    if (!container) return; // Exit if the tab isn't currently active
    
    renderSankeyDiagram();

    // UI Controls Logic
    const btnDirect = document.getElementById("btn-tension-direct");
    const btnFlowing = document.getElementById("btn-tension-flowing");

    const updateTensionUI = () => {
        if(currentTension === 0.2) {
            if(btnDirect) btnDirect.className = "px-3 py-1 text-sm font-medium rounded-md transition-colors bg-slate-100 text-slate-900";
            if(btnFlowing) btnFlowing.className = "px-3 py-1 text-sm font-medium rounded-md transition-colors text-slate-500 hover:text-slate-700";
        } else {
            if(btnDirect) btnDirect.className = "px-3 py-1 text-sm font-medium rounded-md transition-colors text-slate-500 hover:text-slate-700";
            if(btnFlowing) btnFlowing.className = "px-3 py-1 text-sm font-medium rounded-md transition-colors bg-slate-100 text-slate-900";
        }
    }

    // Prevent duplicate listeners if initialized multiple times
    if (btnDirect && !btnDirect.hasAttribute('data-init')) {
        btnDirect.addEventListener("click", () => { currentTension = 0.2; updateTensionUI(); renderSankeyDiagram(); });
        btnDirect.setAttribute('data-init', 'true');
    }
    if (btnFlowing && !btnFlowing.hasAttribute('data-init')) {
        btnFlowing.addEventListener("click", () => { currentTension = 0.5; updateTensionUI(); renderSankeyDiagram(); });
        btnFlowing.setAttribute('data-init', 'true');
    }

    // // Handle window resizing
    // if (!window.sankeyResizeObserver) {
    //     window.sankeyResizeObserver = new ResizeObserver(() => {
    //         window.requestAnimationFrame(() => renderSankeyDiagram());
    //     });
    //     window.sankeyResizeObserver.observe(container);
    // }
}


async function initialSankeyDataLoad() {
    // --- Load the entire dataset on load ---
    const response = await fetch(`/api/sankey-data`);
    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }
    const htmlContent = await response.text();
    document.getElementById('data-store').innerHTML = htmlContent;
    console.log('Successfully fetched and injected HTML.')
}


document.body.addEventListener("drawSankey", function() {
    // I don't care about HTMX swaps, I just wait for my specific bat-signal!
    initSankey(); 
    // initialSankeyDataLoad();
});



// initialSankeyDataLoad();

// // Initial Render on direct load (fallback)
// // document.addEventListener("DOMContentLoaded", initSankey);
// initSankey(); //renderChart();

// // --- HTMX INTEGRATION ---
// // This listens for when HTMX swaps out elements. 
// // We attach to 'document' instead of 'document.body' because if the script 
// // is loaded in the <head>, document.body is null and will crash the script!
// document.addEventListener("htmx:afterSwap", function(evt) {
//     // If we just loaded the tab into #main-content, initialize the graph
//     if (evt.target.id === "main-content") {
//         initSankey();
//     }
//     // If we just fetched new data from FastAPI into #data-store, re-render
//     else if (evt.target.id === "data-store") {
//         renderSankeyDiagram();
//     }
// });