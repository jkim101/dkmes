import React, { useState, useEffect } from 'react';
import { Activity, Server, RefreshCw, MessageSquare, ArrowLeftRight, List, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import '../App.css';

interface AgentStatus {
    agent_id: string;
    name: string;
    domain: string;
    status: 'online' | 'offline';
    timestamp: string;
}

interface ExchangeLog {
    request_id: string;
    sender_agent_id: string;
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

const Orchestrator: React.FC = () => {
    const [alphaStatus, setAlphaStatus] = useState<AgentStatus | null>(null);
    const [betaStatus, setBetaStatus] = useState<AgentStatus | null>(null);
    const [alphaExchanges, setAlphaExchanges] = useState<ExchangeLog[]>([]);
    const [betaExchanges, setBetaExchanges] = useState<ExchangeLog[]>([]);
    const [activeTasks, setActiveTasks] = useState<A2ATask[]>([]);
    const [loading, setLoading] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchAgentStatus = async (port: number): Promise<AgentStatus | null> => {
        try {
            const response = await fetch(`http://localhost:${port}/health`);
            if (response.ok) {
                const data = await response.json();
                return {
                    agent_id: data.agent_id,
                    name: data.agent_name || (port === 8000 ? 'DKMES Alpha' : 'Agent Beta'),
                    domain: data.domain,
                    status: 'online',
                    timestamp: data.timestamp
                };
            }
        } catch (e) {
            // console.log(`Agent on port ${port} offline`);
        }
        return null;
    };

    const fetchExchanges = async (port: number): Promise<ExchangeLog[]> => {
        try {
            const response = await fetch(`http://localhost:${port}/api/v1/kep/history?limit=10`);
            if (response.ok) {
                const data = await response.json();
                return data.exchanges || [];
            }
        } catch (e) {
            // console.log(`Failed to fetch exchanges from port ${port}`);
        }
        return [];
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

        const [alpha, beta, alphaEx, betaEx, tasks] = await Promise.all([
            fetchAgentStatus(8000),
            fetchAgentStatus(8001),
            fetchExchanges(8000),
            fetchExchanges(8001),
            fetchTasks()
        ]);

        setAlphaStatus(alpha || { agent_id: 'dkmes-alpha', name: 'DKMES Alpha', domain: 'knowledge-management', status: 'offline', timestamp: '' });
        setBetaStatus(beta || { agent_id: 'agent-beta-aiml', name: 'AI/ML Research Agent', domain: 'artificial-intelligence', status: 'offline', timestamp: '' });
        setAlphaExchanges(alphaEx);
        setBetaExchanges(betaEx);
        setActiveTasks(tasks);

        setLoading(false);
    };

    useEffect(() => {
        refreshAll();

        if (autoRefresh) {
            const interval = setInterval(refreshAll, 3000); // Faster refresh for task monitoring
            return () => clearInterval(interval);
        }
    }, [autoRefresh]);

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

    const AgentCard = ({ agent, exchanges, port }: { agent: AgentStatus | null, exchanges: ExchangeLog[], port: number }) => (
        <div className="card" style={{ padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Agent Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Server size={20} />
                    <div>
                        <div style={{ fontWeight: '600', fontSize: '1rem' }}>{agent?.name || 'Unknown'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Port {port}</div>
                    </div>
                </div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '20px',
                    background: agent?.status === 'online' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: getStatusColor(agent?.status || 'offline'),
                    fontSize: '0.75rem',
                    fontWeight: '600'
                }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: getStatusColor(agent?.status || 'offline') }} />
                    {agent?.status === 'online' ? 'Online' : 'Offline'}
                </div>
            </div>

            {/* Agent Info */}
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: '8px', marginBottom: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
                    <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Domain: </span>
                        <span style={{ fontWeight: '500' }}>{agent?.domain}</span>
                    </div>
                    <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Exchanges: </span>
                        <span style={{ fontWeight: '500' }}>{exchanges.length}</span>
                    </div>
                </div>
            </div>

            {/* Recent Exchanges */}
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <MessageSquare size={14} /> Recent Exchanges
                </div>
                <div style={{ flex: 1, overflowY: 'auto' }}>
                    {exchanges.length > 0 ? (
                        exchanges.slice(0, 5).map((ex) => (
                            <div key={ex.request_id} style={{
                                padding: '0.5rem',
                                borderLeft: '3px solid var(--accent-color)',
                                background: 'var(--bg-secondary)',
                                borderRadius: '0 6px 6px 0',
                                marginBottom: '0.5rem',
                                fontSize: '0.75rem'
                            }}>
                                <div style={{ fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {ex.query}
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                                    <span>From: {ex.sender_agent_id}</span>
                                    <span style={{ color: ex.confidence > 0.7 ? '#10b981' : '#f59e0b' }}>
                                        {(ex.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1rem', fontSize: '0.8rem' }}>
                            No exchanges yet
                        </div>
                    )}
                </div>
            </div>
        </div>
    );

    return (
        <div className="orchestrator-dashboard fade-in" style={{ padding: '1.5rem', height: '100%', overflow: 'auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Activity size={24} /> Multi-Agent Orchestrator
                    </h1>
                    <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        Monitor and manage knowledge exchange between agents
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

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.5fr) minmax(0, 1fr)', gap: '1.5rem', marginBottom: '1.5rem' }}>
                {/* Connection Diagram */}
                <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem' }}>
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            width: '60px', height: '60px', borderRadius: '50%',
                            background: alphaStatus?.status === 'online' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            border: `2px solid ${getStatusColor(alphaStatus?.status || 'offline')}`,
                            margin: '0 auto'
                        }}>
                            <Server size={24} color={getStatusColor(alphaStatus?.status || 'offline')} />
                        </div>
                        <div style={{ marginTop: '0.5rem', fontWeight: '600', fontSize: '0.85rem' }}>Alpha</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>:8000</div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: '40px', height: '2px', background: 'var(--border-color)' }} />
                        <ArrowLeftRight size={20} color="var(--accent-color)" />
                        <div style={{ width: '40px', height: '2px', background: 'var(--border-color)' }} />
                    </div>

                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            width: '60px', height: '60px', borderRadius: '50%',
                            background: betaStatus?.status === 'online' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            border: `2px solid ${getStatusColor(betaStatus?.status || 'offline')}`,
                            margin: '0 auto'
                        }}>
                            <Server size={24} color={getStatusColor(betaStatus?.status || 'offline')} />
                        </div>
                        <div style={{ marginTop: '0.5rem', fontWeight: '600', fontSize: '0.85rem' }}>Beta</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>:8001</div>
                    </div>
                </div>

                {/* A2A Task Monitor */}
                <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '200px' }}>
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

            {/* Agent Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <AgentCard agent={alphaStatus} exchanges={alphaExchanges} port={8000} />
                <AgentCard agent={betaStatus} exchanges={betaExchanges} port={8001} />
            </div>
        </div>
    );
};

export default Orchestrator;
