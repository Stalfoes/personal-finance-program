// --- STATE & UTILS ---
// let hoveredLine = null;

// Store calculated layout so hover functions can access topology
// let currentLayout = { nodes: [], links: [] }; 

// --- MAIN RENDER FUNCTION ---
function renderNetWorthChart() {
    // 1. Get raw data from the DOM (acts as our state store, updatable by HTMX)
    const dataScript = document.getElementById('chart-data');
    if (!dataScript) return;

    const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
    const formatDate = (date) => date.toLocaleString("en", {month:"short", day:"numeric", year:"numeric", timeZone:"UTC"});

    const rawData = JSON.parse(dataScript.textContent).data;

    const parseTime = d3.timeParse("%Y-%m-%d %H:%M:%S");
    const formattedData = rawData.map(d => ({
            line: d.line,
            date: parseTime(d.time) || new Date(d.time), 
            value: +d.value 
        })).filter(d => d.date != null && !isNaN(d.value)) // Drop invalid data to prevent D3 crashes
          .sort((a, b) => a.date - b.date); 

    // 2. Get container dimensions
    const container = document.getElementById('chart-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    const marginTop = 40; const marginRight = 80; const marginBottom = 40; const marginLeft = 80;

    // currentLayout = { nodes: nodesWithPositions, links: linksWithPaths };

    // Update Quick Stats overlay
    // const totalIn = rawNodes.filter(n => n.type === 'income').reduce((sum, n) => sum + n.value, 0);
    // const totalOut = rawLinks.filter(l => nodeMap[l.target].type !== 'asset').reduce((sum, l) => sum + l.value, 0);
    // document.getElementById('stat-total-in').innerText = formatCurrency(totalIn);
    // document.getElementById('stat-total-out').innerText = formatCurrency(totalOut);

    // Create the positional scales.
    const x = d3.scaleUtc()
        .domain(d3.extent(formattedData, d => d.date))
        .range([marginLeft, width - marginRight]);

    const y = d3.scaleLinear()
        .domain([d3.min([d3.min(formattedData, d => d.value), 0]), d3.max(formattedData, d => d.value)]).nice()
        .range([height - marginBottom, marginTop]);

    const NETWORTH_LINE_COLORS = {
        "Net Worth": '#cc8213',             // Orange
        "Asset Value": '#1cb416',           // Green
        "Liability Value": '#cc1313',       // Red
    };

    // --- D3 DRAWING LOGIC ---
    const svg = d3.select("#d3-svg");
    svg.selectAll("*").remove(); // Clear previous drawing

    // Add the horizontal (bottom) axis.
    svg.append("g")
        .attr("transform", `translate(0,${height - marginBottom})`)
        .call(d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0));

    // Add the vertical axis.
    svg.append("g")
        .attr("transform", `translate(${marginLeft},0)`)
        .call(d3.axisLeft(y))
        .call(g => g.select(".domain").remove())
        .call(false ? () => {} : g => g.selectAll(".tick line").clone()
            .attr("x2", width - marginLeft - marginRight)
            .attr("stroke-opacity", 0.1))
        .call(g => g.append("text")
            .attr("x", -marginLeft / 2)
            .attr("y", 20)
            .attr("fill", "currentColor")
            .attr("text-anchor", "start")
            .text("Value ($)"));

    // Compute the points in pixel space as [x, y, z], where z is the name of the series.
    const points = formattedData.map((d) => [x(d.date), y(d.value), d.line]);

    // Group the points by series.
    // const groups = d3.rollup(points, v => Object.assign(v, {z: v[0][2]}), d => d[2]);
    const groups = d3.group(formattedData, d => d.line)
    // console.log(groups)

    // Update Quick Stats overlay
    const networthFinal = groups.get("Net Worth").at(-1).value;
    const assetValueFinal = groups.get("Asset Value").at(-1).value;
    const liabilityValueFinal = groups.get("Liability Value").at(-1).value;
    document.getElementById('stat-total-networth').innerText = formatCurrency(networthFinal);
    document.getElementById('stat-total-assets').innerText = formatCurrency(assetValueFinal);
    document.getElementById('stat-total-liabilities').innerText = formatCurrency(liabilityValueFinal);

    // Draw the lines.
    const line = d3.line()      // Function that takes in an object and outputs x,y coordinates
        .x(d => x(d.date))
        .y(d => y(d.value));

    const path = svg.append("g")
            .attr("fill", "none")
            .attr("stroke-width", 2.5)
            .attr("stroke-linejoin", "round")
            .attr("stroke-linecap", "round")
        .selectAll("path")                          // find all objects that are "path"s
        .data(groups)
        .join("path")                               // Create a new "path" for each piece of data that doesn't already have one
            .attr("stroke", g => NETWORTH_LINE_COLORS[g[0]] || "black") // `g` here is a 2-element array: [key,value] where key=(the name/line) and value=(the array of data points)
            .style("mix-blend-mode", "multiply")
            .attr("d", g => line(g[1]));

    // Draw the permanent points along the line
    // const dotGroup = svg.append("g").selectAll("circle").data(formattedData).join("circle")
    //     .attr("cx", d => x(d.date))
    //     .attr("cy", d => y(d.value))
    //     .attr("r", 4)
    //     .attr("fill", g => NETWORTH_LINE_COLORS[g.line] || "black")
    //     .attr("stroke", "white")
    //     .attr("stroke-width", 1.5)
    //     .style("mix-blend-mode", "multiply");

    // Add an invisible layer for the interactive tip.
    const tooltip = svg.append("g");
    const bisect = d3.bisector(d => d.date).center;

    // const dot = svg.append("g")
    //     .attr("display", "none");

    // dot.append("circle")
    //     .attr("r", 5);

    // dot.append("text")
    //     .attr("text-anchor", "middle")
    //     .attr("y", -8);

    svg.on("pointerenter", pointerentered)
        .on("pointermove", pointermoved)
        .on("pointerleave", pointerleft)
        .on("touchstart", event => event.preventDefault());

    // svg.on("pointerenter pointermove", pointermoved)
    //     .on("pointerleave", pointerleft)
    //     .on("touchstart", event => event.preventDefault());

    function pointermoved(event) {
        const [xm, ym] = d3.pointer(event);
        const i = d3.leastIndex(points, ([x, y]) => Math.hypot(x - xm, y - ym));
        // const [x, y, k] = points[i];
        const k = points[i][2];
        path.style("stroke", ([key]) => key === k ? null : "#ddd").filter(([key]) => key === k).raise();
        // dot.attr("transform", `translate(${x},${y})`);
        // dot.select("text").text(`${(formattedData[i].value).toLocaleString('en-US', {style:'currency',currency:'USD'})}`);
        // svg.property("value", formattedData[i]).dispatch("input", {bubbles: true});
        tooltip.style("display", null);
        tooltip.attr("transform", `translate(${x(formattedData[i].date)},${y(formattedData[i].value)})`);
        const boundingPath = tooltip.selectAll("path")
            .data([,])
            .join("path")
                .attr("fill", "white")
                .attr("stroke", "black");

        const text = tooltip.selectAll("text")
            .data([,])
            .join("text")
            .call(text => text
                .selectAll("tspan")
                .data([formatDate(formattedData[i].date), formatCurrency(formattedData[i].value)])
                .join("tspan")
                .attr("x", 0)
                .attr("y", (_, i) => `${i * 1.1}em`)
                .attr("font-weight", (_, i) => i ? null : "bold")
                .text(d => d));
        
        function size(text, path) {
            const {x, y, width:w, height:h} = text.node().getBBox();
            text.attr("transform", `translate(${-w / 2},${15 - y})`);
            path.attr("d", `M${-w / 2 - 10},5H-5l5,-5l5,5H${w / 2 + 10}v${h + 20}h-${w + 20}z`);
        }
        size(text, boundingPath);
    }

    function pointerentered() {
        path.style("mix-blend-mode", null).style("stroke", "#ddd");
        // dot.attr("display", null);
        tooltip.style("display", null);
    }

    function pointerleft() {
        path.style("mix-blend-mode", "multiply").style("stroke", null);
        // dot.attr("display", "none");
        // svg.node().value = null;
        // svg.dispatch("input", {bubbles: true});
        tooltip.style("display", "none");
    }

    return svg.node();
}

// --- SETUP & EVENT LISTENERS ---
function initNetworth() {    
    renderNetWorthChart();

    // Handle window resizing
    // if (!window.sankeyResizeObserver) {
    //     window.sankeyResizeObserver = new ResizeObserver(() => {
    //         window.requestAnimationFrame(() => renderNetWorthChart());
    //     });
    //     window.sankeyResizeObserver.observe(container);
    // }
}

async function initialNetWorthDataLoad() {
    // --- Load the entire dataset on load ---
    const initial_start_date = '1999-12-01'; const initial_end_date = '2027-12-31';
    const response = await fetch(`/api/networth-data?start_date=${initial_start_date}&end_date=${initial_end_date}`);
    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }
    const htmlContent = await response.text();
    document.getElementById('data-store').innerHTML = htmlContent;
    console.log('Successfully fetched and injected HTML.')
}


document.body.addEventListener("drawNetworth", function() {
    // initialNetWorthDataLoad();
    initNetworth();
    // renderNetWorthChart();
});

// initialNetWorthDataLoad();


// // Initial Render on direct load (fallback)
// // document.addEventListener("DOMContentLoaded", initGraph);
// // initGraph();
// initGraph(); renderNetWorthChart();

// // --- HTMX INTEGRATION ---
// // This listens for when HTMX swaps out elements. 
// // We attach to 'document' instead of 'document.body' because if the script 
// // is loaded in the <head>, document.body is null and will crash the script!
// document.addEventListener("htmx:afterSwap", function(evt) {
//     // If we just loaded the tab into #main-content, initialize the graph
//     if (evt.target.id === "main-content") {
//         initGraph();
//     }
//     // If we just fetched new data from FastAPI into #networth-chart-data, re-render
//     else if (evt.target.id === "networth-data-store") {
//         // console.log("swap occurred")
//         renderNetWorthChart();
//     }
// });