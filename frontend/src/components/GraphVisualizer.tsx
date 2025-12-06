import React, { useEffect, useRef, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

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

    // If no data, show message
    if (!data || data.nodes.length === 0) {
        return <div className="no-data">No graph data to visualize</div>;
    }

    return (
        <div ref={containerRef} className="graph-container" style={{ width: '100%', height: '100%', border: 'none', overflow: 'hidden' }}>
            <ForceGraph3D
                width={dimensions.width}
                height={dimensions.height}
                graphData={data}
                nodeLabel="label"
                nodeColor={() => "#3b82f6"}
                nodeRelSize={6}
                linkColor={() => "#64748b"}
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                backgroundColor="#0f172a"
                onNodeClick={onNodeClick}
            />
        </div>
    );
};

export default GraphVisualizer;
