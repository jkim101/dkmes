import React, { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

interface GraphData {
    nodes: any[];
    links: any[];
}

interface GraphVisualizerProps {
    data: GraphData;
    onNodeClick?: (node: any) => void;
}

const GraphVisualizer: React.FC<GraphVisualizerProps> = ({ data, onNodeClick }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const graphRef = useRef<any>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

    useEffect(() => {
        if (!containerRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                setDimensions({ width, height });
            }
        });

        resizeObserver.observe(containerRef.current);

        return () => {
            resizeObserver.disconnect();
        };
    }, []);

    // Custom node drawing with labels
    const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
        const label = node.label || node.id;
        const fontSize = 12 / globalScale;
        ctx.font = `${fontSize}px Sans-Serif`;

        // Node circle
        const nodeColor = node.group === 'Table' ? '#3b82f6' :
            node.group === 'Column' ? '#10b981' :
                node.group === 'Query' ? '#f59e0b' : '#8b5cf6';

        ctx.beginPath();
        ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
        ctx.fillStyle = nodeColor;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5 / globalScale;
        ctx.stroke();

        // Label
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#e2e8f0';
        ctx.fillText(label, node.x, node.y + 12);
    }, []);

    // If no data, show message
    if (!data || data.nodes.length === 0) {
        return <div className="no-data">No graph data to visualize</div>;
    }

    return (
        <div ref={containerRef} className="graph-container" style={{ width: '100%', height: '100%', border: 'none', overflow: 'hidden' }}>
            <ForceGraph2D
                ref={graphRef}
                width={dimensions.width}
                height={dimensions.height}
                graphData={data}
                nodeCanvasObject={nodeCanvasObject}
                nodePointerAreaPaint={(node, color, ctx) => {
                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
                    ctx.fill();
                }}
                linkColor={() => "#64748b"}
                linkWidth={1.5}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                backgroundColor="#0f172a"
                onNodeClick={onNodeClick}
                cooldownTicks={100}
                onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
            />
        </div>
    );
};

export default GraphVisualizer;

