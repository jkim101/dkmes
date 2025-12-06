import React, { useState, useEffect } from 'react';
import '../App.css';
import AssessmentOverview from './assessment/AssessmentOverview';
import ActivityLog from './assessment/ActivityLog';
import { AssessmentResult, FeedbackStats, RegisteredAgent, KnowledgeExchange } from './assessment/types';

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
                <ActivityLog agents={agents} exchanges={exchanges} />
            ) : (
                <AssessmentOverview
                    assessment={assessment}
                    feedbackStats={feedbackStats}
                    history={history}
                />
            )}
        </div>
    );
};

export default AssessmentDashboard;
