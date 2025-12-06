import React from 'react';
import { RegisteredAgent, KnowledgeExchange } from './types';

interface ActivityLogProps {
    agents: RegisteredAgent[];
    exchanges: KnowledgeExchange[];
}

const ActivityLog: React.FC<ActivityLogProps> = ({ agents, exchanges }) => {

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return '#10b981';
        if (score >= 0.6) return '#f59e0b';
        return '#ef4444';
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
            {/* Connected Agents */}
            <div className="card" style={{ padding: '1.5rem' }}>
                <h3 style={{ margin: '0 0 1rem 0' }}>🤖 Connected Agents</h3>
                {agents.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {agents.map((agent) => (
                            <div key={agent.agent_id} style={{
                                padding: '0.75rem',
                                background: 'var(--bg-secondary)',
                                borderRadius: '8px',
                                borderLeft: `4px solid ${agent.last_active ? '#10b981' : '#6b7280'}`
                            }}>
                                <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{agent.name}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                    ID: {agent.agent_id}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                    Domains: {agent.domains.join(', ') || 'None'}
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                    {agent.last_active ? `Last active: ${new Date(agent.last_active).toLocaleString()}` : 'Never active'}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                        No agents registered yet
                    </div>
                )}
            </div>

            {/* Knowledge Exchange History */}
            <div className="card" style={{ padding: '1.5rem' }}>
                <h3 style={{ margin: '0 0 1rem 0' }}>📨 Knowledge Exchange History</h3>
                {exchanges.length > 0 ? (
                    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                            <thead>
                                <tr style={{ background: 'var(--bg-secondary)' }}>
                                    <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>Time</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>Agent</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>Query</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'center', borderBottom: '1px solid var(--border-color)' }}>Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                                {exchanges.map((ex) => (
                                    <tr key={ex.request_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                        <td style={{ padding: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                            {new Date(ex.timestamp).toLocaleString()}
                                        </td>
                                        <td style={{ padding: '0.75rem' }}>
                                            <span style={{
                                                background: 'var(--accent-color)',
                                                color: 'white',
                                                padding: '2px 8px',
                                                borderRadius: '4px',
                                                fontSize: '0.75rem'
                                            }}>
                                                {ex.sender_agent_id}
                                            </span>
                                        </td>
                                        <td style={{ padding: '0.75rem', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {ex.query}
                                        </td>
                                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                            <span style={{ color: getScoreColor(ex.confidence), fontWeight: '600' }}>
                                                {(ex.confidence * 100).toFixed(0)}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                        No knowledge exchanges yet
                    </div>
                )}
            </div>
        </div>
    );
};

export default ActivityLog;
