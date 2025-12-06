import React, { useState, useEffect } from 'react';
import '../App.css';

interface DimensionDetail {
    dimension: string;
    score: number;
    details: string;
    recommendations: string[];
}

interface AssessmentResult {
    timestamp: string;
    domain: string | null;
    overall_score: number;
    dimensions: Record<string, number>;
    dimension_details: DimensionDetail[];
    recommendations: string[];
    metadata: Record<string, any>;
}

interface FeedbackStats {
    overall: {
        total_feedback: number;
        avg_rating: number;
        useful_rate: number;
        correction_rate: number;
    };
    by_agent: Record<string, any>;
    low_rated_requests: any[];
}

interface RegisteredAgent {
    agent_id: string;
    name: string;
    domains: string[];
    registered_at: string;
    last_active: string | null;
}

interface KnowledgeExchange {
    request_id: string;
    sender_agent_id: string;
    domain: string;
    query: string;
    confidence: number;
    timestamp: string;
}

const AssessmentDashboard: React.FC = () => {
    const [assessment, setAssessment] = useState<AssessmentResult | null>(null);
    const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [agents, setAgents] = useState<RegisteredAgent[]>([]);
    const [exchanges, setExchanges] = useState<KnowledgeExchange[]>([]);
    const [activeTab, setActiveTab] = useState<'overview' | 'activity'>('overview');

    const runAssessment = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/assessment/run', { method: 'POST' });
            const data = await response.json();
            setAssessment(data);
            fetchHistory();
        } catch (e) {
            setError('Failed to run assessment');
        } finally {
            setLoading(false);
        }
    };

    const fetchFeedbackStats = async () => {
        try {
            const response = await fetch('/api/v1/feedback/stats');
            const data = await response.json();
            setFeedbackStats(data);
        } catch (e) {
            console.error('Failed to fetch feedback stats');
        }
    };

    const fetchHistory = async () => {
        try {
            const response = await fetch('/api/v1/assessment/history?limit=5');
            const data = await response.json();
            setHistory(data.assessments || []);
        } catch (e) {
            console.error('Failed to fetch history');
        }
    };

    const fetchAgents = async () => {
        try {
            const response = await fetch('/api/v1/kep/agents');
            const data = await response.json();
            setAgents(data.agents || []);
        } catch (e) {
            console.error('Failed to fetch agents');
        }
    };

    const fetchExchanges = async () => {
        try {
            const response = await fetch('/api/v1/kep/history?limit=20');
            const data = await response.json();
            setExchanges(data.exchanges || []);
        } catch (e) {
            console.error('Failed to fetch exchanges');
        }
    };

    useEffect(() => {
        fetchFeedbackStats();
        fetchHistory();
        fetchAgents();
        fetchExchanges();
    }, []);

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return '#10b981';
        if (score >= 0.6) return '#f59e0b';
        return '#ef4444';
    };

    const getScoreLabel = (score: number) => {
        if (score >= 0.8) return 'Excellent';
        if (score >= 0.6) return 'Good';
        if (score >= 0.4) return 'Fair';
        return 'Needs Improvement';
    };

    const dimensionIcons: Record<string, string> = {
        usefulness: '⭐',
        coverage: '📚',
        consistency: '✅',
        freshness: '🕐'
    };

    return (
        <div className="assessment-dashboard fade-in" style={{ padding: '1.5rem', height: '100%', overflow: 'auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.5rem' }}>🧠 Self-Assessment Dashboard</h1>
                    <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        Agent Activity & Knowledge Quality
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        onClick={() => setActiveTab('overview')}
                        style={{
                            padding: '0.5rem 1rem',
                            background: activeTab === 'overview' ? 'var(--accent-color)' : 'var(--bg-secondary)',
                            color: activeTab === 'overview' ? 'white' : 'var(--text-primary)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        📊 Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('activity')}
                        style={{
                            padding: '0.5rem 1rem',
                            background: activeTab === 'activity' ? 'var(--accent-color)' : 'var(--bg-secondary)',
                            color: activeTab === 'activity' ? 'white' : 'var(--text-primary)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        📋 Activity Log
                    </button>
                    <button
                        onClick={runAssessment}
                        disabled={loading}
                        style={{
                            padding: '0.5rem 1rem',
                            background: '#10b981',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '0.85rem',
                            fontWeight: '600'
                        }}
                    >
                        {loading ? '⏳...' : '🔍 Run'}
                    </button>
                </div>
            </div>

            {error && (
                <div style={{ padding: '1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', marginBottom: '1rem', color: '#dc2626' }}>
                    {error}
                </div>
            )}

            {activeTab === 'activity' ? (
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
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    {/* Overall Score Card */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ margin: '0 0 1rem 0' }}>📊 Overall Score</h3>
                        {assessment ? (
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: '4rem', fontWeight: 'bold', color: getScoreColor(assessment.overall_score) }}>
                                    {Math.round(assessment.overall_score * 100)}%
                                </div>
                                <div style={{ color: getScoreColor(assessment.overall_score), fontWeight: '600', fontSize: '1.1rem' }}>
                                    {getScoreLabel(assessment.overall_score)}
                                </div>
                                <div style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                    Last assessed: {new Date(assessment.timestamp).toLocaleString()}
                                </div>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                                Click "Run" to start assessment
                            </div>
                        )}
                    </div>

                    {/* Feedback Stats Card */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ margin: '0 0 1rem 0' }}>💬 Federated Feedback</h3>
                        {feedbackStats ? (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--accent-color)' }}>
                                        {feedbackStats.overall.total_feedback}
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Total Feedback</div>
                                </div>
                                <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#f59e0b' }}>
                                        {feedbackStats.overall.avg_rating.toFixed(1)}/5
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Avg Rating</div>
                                </div>
                                <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#10b981' }}>
                                        {feedbackStats.overall.useful_rate.toFixed(0)}%
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Useful Rate</div>
                                </div>
                                <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#8b5cf6' }}>
                                        {feedbackStats.overall.correction_rate.toFixed(0)}%
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Correction Rate</div>
                                </div>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                                No feedback data yet
                            </div>
                        )}
                    </div>

                    {/* Dimension Scores */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ margin: '0 0 1rem 0' }}>📈 Dimension Scores</h3>
                        {assessment ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {assessment.dimension_details.map((dim) => (
                                    <div key={dim.dimension} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <span style={{ fontSize: '1.2rem', width: '30px' }}>{dimensionIcons[dim.dimension] || '📊'}</span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                                <span style={{ textTransform: 'capitalize', fontWeight: '500' }}>{dim.dimension}</span>
                                                <span style={{ fontWeight: 'bold', color: getScoreColor(dim.score) }}>
                                                    {Math.round(dim.score * 100)}%
                                                </span>
                                            </div>
                                            <div style={{ height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                                                <div style={{ width: `${dim.score * 100}%`, height: '100%', background: getScoreColor(dim.score), transition: 'width 0.5s ease' }} />
                                            </div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                                {dim.details}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                                Run an assessment to see scores
                            </div>
                        )}
                    </div>

                    {/* Recommendations */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ margin: '0 0 1rem 0' }}>💡 Recommendations</h3>
                        {assessment && assessment.recommendations.length > 0 ? (
                            <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {assessment.recommendations.map((rec, idx) => (
                                    <li key={idx} style={{ color: 'var(--text-primary)', lineHeight: '1.5' }}>
                                        {rec}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                                {assessment ? '✅ No recommendations - looking good!' : 'Run an assessment to get recommendations'}
                            </div>
                        )}
                    </div>

                    {/* Assessment History - Full Width */}
                    {history.length > 0 && (
                        <div className="card" style={{ padding: '1.5rem', gridColumn: 'span 2' }}>
                            <h3 style={{ margin: '0 0 1rem 0' }}>📜 Recent Assessments</h3>
                            <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto' }}>
                                {history.map((item, idx) => (
                                    <div key={idx} style={{
                                        minWidth: '150px',
                                        padding: '1rem',
                                        background: 'var(--bg-secondary)',
                                        borderRadius: '8px',
                                        textAlign: 'center'
                                    }}>
                                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: getScoreColor(item.overall_score) }}>
                                            {Math.round(item.overall_score * 100)}%
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                            {new Date(item.timestamp).toLocaleDateString()}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default AssessmentDashboard;
