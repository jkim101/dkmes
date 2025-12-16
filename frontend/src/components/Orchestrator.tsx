import React, { useState, useEffect } from 'react';
import { Activity, Server, RefreshCw, MessageSquare, List, CheckCircle, Clock, AlertCircle, Plus } from 'lucide-react';
import AgentNetworkGraph from './AgentNetworkGraph';
import '../App.css';

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

interface A2ATask {
    id: string;
    status: {
        state: string;
        timestamp: number;
    };
    history: any[];
}

interface AgentConfig {
    port: number;
    fallbackId: string;
    fallbackName: string;
    fallbackDomain: string;
}

// Default agent configurations - easily extendable
const DEFAULT_AGENT_CONFIGS: AgentConfig[] = [
    { port: 8000, fallbackId: 'dkmes-alpha', fallbackName: 'DKMES Alpha', fallbackDomain: 'knowledge-management' },
    { port: 8001, fallbackId: 'agent-beta-aiml', fallbackName: 'AI/ML Research Agent', fallbackDomain: 'artificial-intelligence' },
    { port: 8002, fallbackId: 'agent-gamma-analytics', fallbackName: 'CVDT Chatbot Agent', fallbackDomain: 'data-analytics' },
];

const Orchestrator: React.FC = () => {
    const [agentConfigs, setAgentConfigs] = useState<AgentConfig[]>(DEFAULT_AGENT_CONFIGS);
    const [agents, setAgents] = useState<AgentStatus[]>([]);
    const [exchangesByPort, setExchangesByPort] = useState<Record<number, ExchangeLog[]>>({});
    const [activeTasks, setActiveTasks] = useState<A2ATask[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<AgentStatus | null>(null);
    const [loading, setLoading] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [showAddAgent, setShowAddAgent] = useState(false);
    const [newAgentPort, setNewAgentPort] = useState('');

    const fetchAgentStatus = async (config: AgentConfig): Promise<AgentStatus> => {
        try {
            const response = await fetch(`http://localhost:${config.port}/health`);
            if (response.ok) {
                const data = await response.json();
                return {
                    agent_id: data.agent_id || config.fallbackId,
                    name: data.agent_name || config.fallbackName,
                    domain: data.domain || config.fallbackDomain,
                    port: config.port,
                    status: 'online',
                    timestamp: data.timestamp
                };
            }
        } catch (e) {
            // Agent offline
        }
        return {
            agent_id: config.fallbackId,
            name: config.fallbackName,
            domain: config.fallbackDomain,
            port: config.port,
            status: 'offline',
            timestamp: ''
        };
    };

    const fetchExchanges = async (port: number): Promise<{ port: number, exchanges: ExchangeLog[] }> => {
        try {
            const response = await fetch(`http://localhost:${port}/api/v1/kep/history?limit=10`);
            if (response.ok) {
                const data = await response.json();
                return { port, exchanges: data.exchanges || [] };
            }
        } catch (e) {
            // console.log(`Failed to fetch exchanges from port ${port}`);
        }
        return { port, exchanges: [] };
    };

    const fetchTasks = async (): Promise<A2ATask[]> => {
        try {
            const response = await fetch('http://localhost:8000/a2a', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "tasks/list",
                    params: { limit: 10 },
                    id: Date.now()
                })
            });

            if (response.ok) {
                const data = await response.json();
                return data.result?.tasks || [];
            }
        } catch (e) {
            console.error("Failed to fetch tasks", e);
        }
        return [];
    };

    const refreshAll = async () => {
        setLoading(true);

        // Fetch all agents dynamically
        const agentPromises = agentConfigs.map(config => fetchAgentStatus(config));
        const exchangePromises = agentConfigs.map(config => fetchExchanges(config.port));

        const [agentResults, exchangeResults, tasks] = await Promise.all([
            Promise.all(agentPromises),
            Promise.all(exchangePromises),
            fetchTasks()
        ]);

        setAgents(agentResults);

        setAgents(agentResults);

        // Store exchanges by port
        const newExchangesByPort: Record<number, ExchangeLog[]> = {};
        exchangeResults.forEach(res => {
            newExchangesByPort[res.port] = res.exchanges;
        });
        setExchangesByPort(newExchangesByPort);

        setActiveTasks(tasks);

        setLoading(false);
    };

    const addAgent = () => {
        const port = parseInt(newAgentPort);
        if (port && !agentConfigs.some(c => c.port === port)) {
            setAgentConfigs([...agentConfigs, {
                port,
                fallbackId: `agent-${port}`,
                fallbackName: `Agent :${port}`,
                fallbackDomain: 'unknown'
            }]);
            setNewAgentPort('');
            setShowAddAgent(false);
        }
    };

    const removeAgent = (port: number) => {
        setAgentConfigs(agentConfigs.filter(c => c.port !== port));
    };

    useEffect(() => {
        refreshAll();

        if (autoRefresh) {
            const interval = setInterval(refreshAll, 3000);
            return () => clearInterval(interval);
        }
    }, [autoRefresh, agentConfigs]);

    const getStatusColor = (status: string) => status === 'online' ? '#10b981' : '#ef4444';

    const getTaskStateColor = (state: string) => {
        switch (state) {
            case 'TASK_STATE_COMPLETED': return '#10b981';
            case 'TASK_STATE_FAILED': return '#ef4444';
            case 'TASK_STATE_WORKING': return '#3b82f6';
            case 'TASK_STATE_SUBMITTED': return '#f59e0b';
            default: return '#6b7280';
        }
    };

    const getTaskStateIcon = (state: string) => {
        switch (state) {
            case 'TASK_STATE_COMPLETED': return <CheckCircle size={14} />;
            case 'TASK_STATE_FAILED': return <AlertCircle size={14} />;
            case 'TASK_STATE_WORKING': return <RefreshCw size={14} className="spin" />;
            default: return <Clock size={14} />;
        }
    };

    // Get exchanges for a specific agent based on its port
    const getAgentExchanges = (agent: AgentStatus): ExchangeLog[] => {
        // Return exchanges fetched from this agent's port directly
        // This represents requests RECEIVED by this agent (processed by it)
        return exchangesByPort[agent.port] || [];
    };

    const AgentCard = ({ agent }: { agent: AgentStatus }) => {
        const exchanges = getAgentExchanges(agent);
        return (
            <div className="card" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', minWidth: '280px' }}>
                {/* Agent Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Server size={18} />
                        <div>
                            <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{agent.name}</div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>:{agent.port}</div>
                        </div>
                    </div>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '12px',
                        background: agent.status === 'online' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: getStatusColor(agent.status),
                        fontSize: '0.7rem',
                        fontWeight: '600'
                    }}>
                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: getStatusColor(agent.status) }} />
                        {agent.status === 'online' ? 'Online' : 'Offline'}
                    </div>
                </div>

                {/* Agent Info */}
                <div style={{ padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: '6px', marginBottom: '0.75rem', fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Domain</span>
                        <span style={{ color: 'var(--accent-color)' }}>{agent.domain}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Exchanges</span>
                        <span style={{ color: '#10b981' }}>{exchanges.length}</span>
                    </div>
                </div>

                {/* Recent Exchanges */}
                <div style={{ fontSize: '0.8rem', fontWeight: '600', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <MessageSquare size={12} /> Recent
                </div>
                <div style={{ flex: 1, overflowY: 'auto', maxHeight: '120px' }}>
                    {exchanges.length > 0 ? (
                        exchanges.slice(0, 3).map((ex) => (
                            <div key={ex.request_id} style={{
                                padding: '0.35rem',
                                borderLeft: '2px solid var(--accent-color)',
                                background: 'var(--bg-secondary)',
                                borderRadius: '0 4px 4px 0',
                                marginBottom: '0.35rem',
                                fontSize: '0.7rem'
                            }}>
                                <div style={{ fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {ex.query}
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.15rem', color: 'var(--text-secondary)' }}>
                                    <span>{ex.sender_agent_id}</span>
                                    <span style={{ color: ex.confidence > 0.7 ? '#10b981' : '#f59e0b' }}>
                                        {(ex.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '0.5rem', fontSize: '0.7rem' }}>
                            No exchanges
                        </div>
                    )}
                </div>

                {/* Remove button for non-default agents */}
                {!DEFAULT_AGENT_CONFIGS.some(c => c.port === agent.port) && (
                    <button
                        onClick={() => removeAgent(agent.port)}
                        style={{
                            marginTop: '0.5rem',
                            padding: '0.25rem',
                            background: 'rgba(239, 68, 68, 0.1)',
                            color: '#ef4444',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.7rem'
                        }}
                    >
                        Remove
                    </button>
                )}
            </div>
        );
    };

    return (
        <div className="orchestrator-dashboard fade-in" style={{ padding: '1.5rem', height: '100%', overflow: 'auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Activity size={24} /> Multi-Agent Orchestrator
                    </h1>
                    <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {agents.length} agents • {agents.filter(a => a.status === 'online').length} online
                    </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        Auto-refresh
                    </label>
                    <button
                        onClick={() => setShowAddAgent(!showAddAgent)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 1rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        <Plus size={14} /> Add Agent
                    </button>
                    <button
                        onClick={refreshAll}
                        disabled={loading}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 1rem',
                            background: 'var(--accent-color)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        <RefreshCw size={14} className={loading ? 'spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Add Agent Modal */}
            {showAddAgent && (
                <div className="card" style={{ padding: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <input
                        type="number"
                        placeholder="Port number (e.g., 8002)"
                        value={newAgentPort}
                        onChange={(e) => setNewAgentPort(e.target.value)}
                        style={{
                            padding: '0.5rem',
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            color: 'var(--text-primary)',
                            fontSize: '0.85rem',
                            width: '200px'
                        }}
                    />
                    <button
                        onClick={addAgent}
                        style={{
                            padding: '0.5rem 1rem',
                            background: '#10b981',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        Add
                    </button>
                    <button
                        onClick={() => setShowAddAgent(false)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-secondary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        Cancel
                    </button>
                </div>
            )}

            {/* Network Graph and Task Monitor */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                {/* Interactive Agent Network Graph */}
                <div className="card" style={{ padding: '1rem' }}>
                    <div style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Activity size={18} /> Agent Network
                    </div>
                    <AgentNetworkGraph
                        agents={agents}
                        exchanges={Object.values(exchangesByPort).flat()}
                        onAgentSelect={(agent) => setSelectedAgent(agent)}
                    />
                </div>

                {/* A2A Task Monitor */}
                <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '460px' }}>
                    <div style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <List size={18} /> Active A2A Tasks
                        <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                            {activeTasks.length} tasks
                        </span>
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        {activeTasks.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {activeTasks.map(task => {
                                    const input = task.history && task.history[0] && task.history[0].parts && task.history[0].parts[0] ? task.history[0].parts[0].text : 'No Input';
                                    return (
                                        <div key={task.id} style={{
                                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                            padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: '6px', fontSize: '0.8rem'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden' }}>
                                                <span style={{ color: getTaskStateColor(task.status.state) }}>
                                                    {getTaskStateIcon(task.status.state)}
                                                </span>
                                                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '150px' }} title={input}>
                                                    {input}
                                                </span>
                                            </div>
                                            <span style={{
                                                fontSize: '0.7rem', fontWeight: '600',
                                                padding: '0.1rem 0.4rem', borderRadius: '4px',
                                                background: `${getTaskStateColor(task.status.state)}20`,
                                                color: getTaskStateColor(task.status.state)
                                            }}>
                                                {task.status.state.replace('TASK_STATE_', '')}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                No active tasks
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Agent Cards - Dynamic Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: `repeat(auto-fill, minmax(280px, 1fr))`,
                gap: '1rem'
            }}>
                {agents.map(agent => (
                    <AgentCard key={agent.agent_id} agent={agent} />
                ))}
            </div>

            {/* Selected Agent Detail Panel */}
            {selectedAgent && (
                <div
                    className="card"
                    style={{
                        position: 'fixed',
                        bottom: '2rem',
                        right: '2rem',
                        padding: '1rem',
                        width: '300px',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                        zIndex: 1000
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <div style={{ fontWeight: '600' }}>{selectedAgent.name}</div>
                        <button
                            onClick={() => setSelectedAgent(null)}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer',
                                fontSize: '1.2rem'
                            }}
                        >
                            ×
                        </button>
                    </div>
                    <div style={{ fontSize: '0.8rem' }}>
                        <div><strong>Agent ID:</strong> {selectedAgent.agent_id}</div>
                        <div><strong>Port:</strong> {selectedAgent.port}</div>
                        <div><strong>Domain:</strong> {selectedAgent.domain}</div>
                        <div><strong>Status:</strong> <span style={{ color: getStatusColor(selectedAgent.status) }}>{selectedAgent.status}</span></div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Orchestrator;

