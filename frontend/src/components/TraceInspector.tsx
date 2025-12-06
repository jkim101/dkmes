import React, { useState, useEffect } from 'react';
import '../App.css';
import { Activity, Clock, Server, Database, MessageSquare, ChevronRight, CheckCircle, XCircle, Search } from 'lucide-react';

interface Trace {
    id: string;
    timestamp: string;
    query: string;
    status: string;
    latency: number;
    metadata: any;
}

interface TraceStep {
    step_name: string;
    timestamp: string;
    input: string;
    output: string;
    metadata: any;
}

interface TraceDetail extends Trace {
    steps: TraceStep[];
}

interface TraceInspectorProps {
    activeTraceId?: string | null;
    compact?: boolean;
}

const TraceInspector: React.FC<TraceInspectorProps> = ({ activeTraceId, compact = false }) => {
    const [traces, setTraces] = useState<Trace[]>([]);
    const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
    const [selectedTraceDetail, setSelectedTraceDetail] = useState<TraceDetail | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!compact) {
            fetchTraces();
            const interval = setInterval(fetchTraces, 5000); // Auto-refresh
            return () => clearInterval(interval);
        }
    }, [compact]);

    useEffect(() => {
        if (activeTraceId) {
            setSelectedTraceId(activeTraceId);
        }
    }, [activeTraceId]);

    useEffect(() => {
        if (selectedTraceId) {
            fetchTraceDetail(selectedTraceId);
        }
    }, [selectedTraceId]);

    const fetchTraces = async () => {
        try {
            const response = await fetch('/api/v1/traces');
            if (response.ok) {
                const data = await response.json();
                setTraces(data);
            }
        } catch (error) {
            console.error('Error fetching traces:', error);
        }
    };

    const fetchTraceDetail = async (id: string) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/traces/${id}`);
            if (response.ok) {
                const data = await response.json();
                setSelectedTraceDetail(data);
            }
        } catch (error) {
            console.error('Error fetching trace detail:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (isoString: string) => {
        return new Date(isoString).toLocaleTimeString();
    };

    return (
        <div className="trace-inspector-container" style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : '350px 1fr', gap: '1rem', height: '100%' }}>

            {/* Left Sidebar: Trace List (Hidden in compact mode) */}
            {!compact && (
                <div className="trace-list card" style={{ display: 'flex', flexDirection: 'column', padding: '0' }}>
                    <div className="card-header" style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                        <h3><Activity size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} /> Recent Traces</h3>
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        {traces.map((trace) => (
                            <div
                                key={trace.id}
                                onClick={() => setSelectedTraceId(trace.id)}
                                style={{
                                    padding: '1rem',
                                    borderBottom: '1px solid var(--border-color)',
                                    cursor: 'pointer',
                                    background: selectedTraceId === trace.id ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                                    borderLeft: selectedTraceId === trace.id ? '4px solid var(--accent-color)' : '4px solid transparent'
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{formatTime(trace.timestamp)}</span>
                                    <span style={{
                                        fontSize: '0.7rem',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        background: trace.status === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                                        color: trace.status === 'success' ? '#10b981' : '#ef4444'
                                    }}>
                                        {trace.status.toUpperCase()}
                                    </span>
                                </div>
                                <div style={{ fontWeight: '500', marginBottom: '0.5rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {trace.query}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}>
                                    <Clock size={12} style={{ marginRight: '4px' }} /> {trace.latency.toFixed(2)}s
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Right Content: Trace Detail */}
            <div className="trace-detail card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {selectedTraceDetail ? (
                    <>
                        <div className="card-header" style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                <div>
                                    <h2 style={{ margin: '0 0 0.5rem 0' }}>Trace Details</h2>
                                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>ID: {selectedTraceDetail.id}</p>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{selectedTraceDetail.latency.toFixed(2)}s</div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Total Latency</div>
                                </div>
                            </div>
                            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>USER QUERY</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>{selectedTraceDetail.query}</div>
                            </div>
                        </div>

                        <div className="timeline" style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
                            {selectedTraceDetail.steps.map((step, idx) => (
                                <div key={idx} className="timeline-item" style={{ display: 'flex', marginBottom: '2rem' }}>
                                    <div className="timeline-marker" style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        marginRight: '1.5rem',
                                        minWidth: '40px'
                                    }}>
                                        <div style={{
                                            width: '12px',
                                            height: '12px',
                                            borderRadius: '50%',
                                            background: 'var(--accent-color)',
                                            marginBottom: '0.5rem'
                                        }}></div>
                                        {idx < selectedTraceDetail.steps.length - 1 && (
                                            <div style={{ width: '2px', flex: 1, background: 'var(--border-color)' }}></div>
                                        )}
                                    </div>

                                    <div className="timeline-content" style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                            <span style={{ fontWeight: '600', color: 'var(--accent-color)' }}>{step.step_name}</span>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{formatTime(step.timestamp)}</span>
                                        </div>

                                        <div style={{ background: 'var(--bg-color)', borderRadius: '8px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                                            {step.input && step.input !== "{}" && (
                                                <div style={{ padding: '0.8rem', borderBottom: '1px solid var(--border-color)' }}>
                                                    <div style={{ fontSize: '0.7rem', fontWeight: 'bold', color: 'var(--text-secondary)', marginBottom: '0.3rem', textTransform: 'uppercase' }}>Input / Context</div>
                                                    <pre style={{ margin: 0, fontSize: '0.85rem', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
                                                        {step.input.length > 300 ? step.input.substring(0, 300) + '...' : step.input}
                                                    </pre>
                                                </div>
                                            )}

                                            <div style={{ padding: '0.8rem' }}>
                                                <div style={{ fontSize: '0.7rem', fontWeight: 'bold', color: 'var(--text-secondary)', marginBottom: '0.3rem', textTransform: 'uppercase' }}>Output / Result</div>
                                                <pre style={{ margin: 0, fontSize: '0.85rem', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
                                                    {step.output}
                                                </pre>
                                            </div>

                                            {step.metadata && Object.keys(step.metadata).length > 0 && (
                                                <div style={{ padding: '0.5rem 0.8rem', background: 'rgba(0,0,0,0.02)', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {JSON.stringify(step.metadata)}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                        <Search size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                        <p>Select a trace to view details</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TraceInspector;
