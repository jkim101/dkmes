import React, { useCallback, useEffect, useMemo } from 'react';
import ReactFlow, {
    Node,
    Edge,
    useNodesState,
    useEdgesState,
    Background,
    Controls,
    MiniMap,
    MarkerType,
    Handle,
    Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Server } from 'lucide-react';

interface AgentStatus {
    agent_id: string;
    name: string;
    domain: string;
    status: 'online' | 'offline';
    port: number;
    timestamp: string;
}

interface ExchangeLog {
    request_id: string;
    sender_agent_id: string;
    receiver_agent_id?: string;
    domain: string;
    query: string;
    confidence: number;
    timestamp: string;
}

interface AgentNetworkGraphProps {
    agents: AgentStatus[];
    exchanges: ExchangeLog[];
    onAgentSelect?: (agent: AgentStatus) => void;
}

// Custom Agent Node Component
const AgentNode = ({ data }: { data: AgentStatus & { exchangeCount: number } }) => {
    const isOnline = data.status === 'online';
    const statusColor = isOnline ? '#10b981' : '#ef4444';

    return (
        <div
            style={{
                padding: '16px 24px',
                borderRadius: '12px',
                background: 'var(--bg-primary, #1a1a2e)',
                border: `2px solid ${statusColor}`,
                boxShadow: isOnline
                    ? `0 0 20px ${statusColor}40, 0 4px 12px rgba(0,0,0,0.3)`
                    : '0 4px 12px rgba(0,0,0,0.3)',
                minWidth: '180px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
            }}
        >
            <Handle type="target" position={Position.Top} style={{ background: statusColor }} />
            <Handle type="source" position={Position.Bottom} style={{ background: statusColor }} />
            <Handle type="target" position={Position.Left} style={{ background: statusColor }} />
            <Handle type="source" position={Position.Right} style={{ background: statusColor }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                    style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        background: `${statusColor}20`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Server size={20} color={statusColor} />
                </div>
                <div>
                    <div style={{ fontWeight: '600', fontSize: '0.9rem', color: 'var(--text-primary, #fff)' }}>
                        {data.name}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #888)' }}>
                        :{data.port}
                    </div>
                </div>
            </div>

            <div
                style={{
                    marginTop: '12px',
                    padding: '8px',
                    background: 'var(--bg-secondary, #252542)',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary, #888)' }}>Domain</span>
                    <span style={{ color: 'var(--accent-color, #6366f1)' }}>{data.domain}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary, #888)' }}>Exchanges</span>
                    <span style={{ color: '#10b981' }}>{data.exchangeCount}</span>
                </div>
            </div>

            <div
                style={{
                    position: 'absolute',
                    top: '-8px',
                    right: '-8px',
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    background: statusColor,
                    border: '2px solid var(--bg-primary, #1a1a2e)',
                }}
            />
        </div>
    );
};

const nodeTypes = { agentNode: AgentNode };

const AgentNetworkGraph: React.FC<AgentNetworkGraphProps> = ({ agents, exchanges, onAgentSelect }) => {
    // Calculate positions in a circle
    const calculateNodePositions = useCallback((agentCount: number) => {
        const positions: { x: number; y: number }[] = [];
        const centerX = 300;
        const centerY = 200;
        const radius = Math.max(150, agentCount * 40);

        for (let i = 0; i < agentCount; i++) {
            const angle = (2 * Math.PI * i) / agentCount - Math.PI / 2;
            positions.push({
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle),
            });
        }
        return positions;
    }, []);

    // Count exchanges per agent
    const exchangeCounts = useMemo(() => {
        const counts: Record<string, number> = {};
        exchanges.forEach((ex) => {
            counts[ex.sender_agent_id] = (counts[ex.sender_agent_id] || 0) + 1;
            if (ex.receiver_agent_id) {
                counts[ex.receiver_agent_id] = (counts[ex.receiver_agent_id] || 0) + 1;
            }
        });
        return counts;
    }, [exchanges]);

    // Generate nodes from agents
    const initialNodes: Node[] = useMemo(() => {
        const positions = calculateNodePositions(agents.length);
        return agents.map((agent, index) => ({
            id: agent.agent_id,
            type: 'agentNode',
            position: positions[index] || { x: 100, y: 100 },
            data: {
                ...agent,
                exchangeCount: exchangeCounts[agent.agent_id] || 0,
            },
        }));
    }, [agents, calculateNodePositions, exchangeCounts]);

    // Generate edges (connections between all online agents)
    const initialEdges: Edge[] = useMemo(() => {
        const edges: Edge[] = [];
        const onlineAgents = agents.filter((a) => a.status === 'online');

        // Create mesh connections between all online agents
        for (let i = 0; i < onlineAgents.length; i++) {
            for (let j = i + 1; j < onlineAgents.length; j++) {
                const sourceId = onlineAgents[i].agent_id;
                const targetId = onlineAgents[j].agent_id;

                // Check if there are exchanges between these agents
                const hasExchange = exchanges.some(
                    (ex) =>
                        (ex.sender_agent_id === sourceId && ex.receiver_agent_id === targetId) ||
                        (ex.sender_agent_id === targetId && ex.receiver_agent_id === sourceId)
                );

                edges.push({
                    id: `${sourceId}-${targetId}`,
                    source: sourceId,
                    target: targetId,
                    type: 'smoothstep',
                    animated: hasExchange,
                    style: {
                        stroke: hasExchange ? '#10b981' : 'var(--border-color, #333)',
                        strokeWidth: hasExchange ? 2 : 1,
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: hasExchange ? '#10b981' : 'var(--border-color, #333)',
                    },
                });
            }
        }
        return edges;
    }, [agents, exchanges]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    // Update nodes when agents change
    useEffect(() => {
        const positions = calculateNodePositions(agents.length);
        const newNodes = agents.map((agent, index) => ({
            id: agent.agent_id,
            type: 'agentNode',
            position: nodes.find((n) => n.id === agent.agent_id)?.position || positions[index] || { x: 100, y: 100 },
            data: {
                ...agent,
                exchangeCount: exchangeCounts[agent.agent_id] || 0,
            },
        }));
        setNodes(newNodes);
    }, [agents, exchangeCounts]);

    // Update edges when exchanges change
    useEffect(() => {
        const onlineAgents = agents.filter((a) => a.status === 'online');
        const newEdges: Edge[] = [];

        for (let i = 0; i < onlineAgents.length; i++) {
            for (let j = i + 1; j < onlineAgents.length; j++) {
                const sourceId = onlineAgents[i].agent_id;
                const targetId = onlineAgents[j].agent_id;

                const hasExchange = exchanges.some(
                    (ex) =>
                        (ex.sender_agent_id === sourceId && ex.receiver_agent_id === targetId) ||
                        (ex.sender_agent_id === targetId && ex.receiver_agent_id === sourceId)
                );

                newEdges.push({
                    id: `${sourceId}-${targetId}`,
                    source: sourceId,
                    target: targetId,
                    type: 'smoothstep',
                    animated: hasExchange,
                    style: {
                        stroke: hasExchange ? '#10b981' : 'var(--border-color, #333)',
                        strokeWidth: hasExchange ? 2 : 1,
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: hasExchange ? '#10b981' : 'var(--border-color, #333)',
                    },
                });
            }
        }
        setEdges(newEdges);
    }, [agents, exchanges]);

    const handleNodeClick = useCallback(
        (_: React.MouseEvent, node: Node) => {
            const agent = agents.find((a) => a.agent_id === node.id);
            if (agent && onAgentSelect) {
                onAgentSelect(agent);
            }
        },
        [agents, onAgentSelect]
    );

    return (
        <div style={{ width: '100%', height: '400px', background: 'var(--bg-secondary, #1a1a2e)', borderRadius: '12px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={handleNodeClick}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.3 }}
                proOptions={{ hideAttribution: true }}
            >
                <Background color="var(--border-color, #333)" gap={20} />
                <Controls
                    style={{
                        background: 'var(--bg-primary, #1a1a2e)',
                        border: '1px solid var(--border-color, #333)',
                        borderRadius: '8px',
                    }}
                />
                <MiniMap
                    style={{
                        background: 'var(--bg-primary, #1a1a2e)',
                        border: '1px solid var(--border-color, #333)',
                    }}
                    nodeColor={(node) => {
                        const agent = agents.find((a) => a.agent_id === node.id);
                        return agent?.status === 'online' ? '#10b981' : '#ef4444';
                    }}
                />
            </ReactFlow>
        </div>
    );
};

export default AgentNetworkGraph;
