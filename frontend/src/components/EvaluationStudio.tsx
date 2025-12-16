import React, { useState } from 'react';
import '../App.css';
import GraphVisualizer from './GraphVisualizer';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

interface ComparisonResponse {
    vector: { score: number; feedback: string; context: string[]; metrics?: any };
    graph: { score: number; feedback: string; context: string[]; debug_info?: any; metrics?: any };
    hybrid: { score: number; feedback: string; context: string[]; metrics?: any };
}

interface BatchResult {
    question: string;
    ground_truth: string;
    system_answer: string;
    strategy: string;
    metrics: {
        rouge_l: number;
        faithfulness: number;
        answer_relevance: number;
        overall: number;
    };
}

const MetricsRadar = ({ metrics }: { metrics: any }) => {
    if (!metrics) return null;

    const data = [
        { subject: 'Faithfulness', A: metrics.faithfulness || 0, fullMark: 1 },
        { subject: 'Relevance', A: metrics.answer_relevance || 0, fullMark: 1 },
        { subject: 'ROUGE-L', A: metrics.rouge_l || 0, fullMark: 1 },
    ];

    return (
        <div style={{ width: '100%', height: '200px', fontSize: '0.8rem' }}>
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid stroke="var(--border-color)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} axisLine={false} />
                    <Radar
                        name="Metrics"
                        dataKey="A"
                        stroke="var(--accent-color)"
                        fill="var(--accent-color)"
                        fillOpacity={0.3}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};

const EvaluationStudio: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'interactive' | 'batch'>('interactive');

    // Interactive State
    const [query, setQuery] = useState('');
    const [persona, setPersona] = useState('Novice');
    const [result, setResult] = useState<ComparisonResponse | null>(null);
    const [loading, setLoading] = useState(false);

    // Batch State
    const [batchData, setBatchData] = useState<string>('[{"question": "What is DKMES?", "ground_truth": "Data Knowledge Management Eco-System"}]');
    const [batchResults, setBatchResults] = useState<BatchResult[]>([]);
    const [batchLoading, setBatchLoading] = useState(false);
    const [avgScore, setAvgScore] = useState<number | null>(null);

    const handleEvaluate = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setResult(null);
        try {
            const response = await fetch('/api/v1/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, agent_id: 'test-agent', persona }),
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Error evaluating:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleBatchEvaluate = async () => {
        try {
            const pairs = JSON.parse(batchData);
            setBatchLoading(true);
            setBatchResults([]);
            setAvgScore(null);

            const response = await fetch('/api/v1/batch-evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pairs }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Server error');
            }

            const data = await response.json();
            setBatchResults(data.results);
            setAvgScore(data.average_score);
        } catch (error) {
            console.error('Batch eval failed:', error);
            alert(`Batch evaluation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setBatchLoading(false);
        }
    };

    return (
        <div className="evaluation-studio fade-in">
            <div className="card-header">
                <h2>Evaluation Studio</h2>
                <p>Compare Vector, Graph, and Hybrid RAG strategies side-by-side.</p>
            </div>

            <div className="tabs" style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: '0.5rem' }}>
                <button
                    className={`tab-btn ${activeTab === 'interactive' ? 'active' : ''}`}
                    onClick={() => setActiveTab('interactive')}
                    style={{ padding: '0.8rem 1.5rem', background: 'none', border: 'none', outline: 'none', borderBottom: activeTab === 'interactive' ? '2px solid var(--text-primary)' : '2px solid transparent', color: activeTab === 'interactive' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', fontWeight: activeTab === 'interactive' ? '600' : '400' }}
                >
                    Interactive Mode
                </button>
                <button
                    className={`tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
                    onClick={() => setActiveTab('batch')}
                    style={{ padding: '0.8rem 1.5rem', background: 'none', border: 'none', outline: 'none', borderBottom: activeTab === 'batch' ? '2px solid var(--text-primary)' : '2px solid transparent', color: activeTab === 'batch' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', fontWeight: activeTab === 'batch' ? '600' : '400' }}
                >
                    Batch Evaluation
                </button>
            </div>

            {activeTab === 'interactive' ? (
                <div className="interactive-mode">
                    <div className="controls-row">
                        <select
                            value={persona}
                            onChange={(e) => setPersona(e.target.value)}
                            className="styled-select"
                            disabled={loading}
                        >
                            <option value="Novice">Novice (Beginner)</option>
                            <option value="Intermediate">Intermediate</option>
                            <option value="Expert">Expert (Technical)</option>
                        </select>
                        <div className="search-box">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter evaluation query..."
                                className="styled-input"
                                onKeyDown={(e) => e.key === 'Enter' && !loading && handleEvaluate()}
                                disabled={loading}
                            />
                            <button
                                onClick={handleEvaluate}
                                className="primary-btn"
                                disabled={loading}
                            >
                                {loading ? 'Evaluating...' : 'Run Evaluation'}
                            </button>
                        </div>
                    </div>

                    {loading && (
                        <div className="loading-container fade-in">
                            <div className="spinner"></div>
                            <p>Analyzing Vector, Graph, and Hybrid contexts...</p>
                        </div>
                    )}

                    {result && (
                        <div className="comparison-grid fade-in">
                            {/* Vector Column */}
                            <div className="result-column" style={{ height: '600px', minHeight: '600px', maxHeight: '600px', display: 'flex', flexDirection: 'column' }}>
                                <div className="column-header vector" style={{ flexShrink: 0 }}>
                                    <h3>Vector RAG</h3>
                                    <span className="score-badge">{result.vector.score.toFixed(1)}</span>
                                </div>
                                <div className="metrics-box" style={{ padding: '0.5rem', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
                                    <MetricsRadar metrics={result.vector.metrics} />
                                </div>
                                <div className="feedback-box" style={{ flexShrink: 0, maxHeight: '150px', overflowY: 'auto' }}>
                                    <p>{result.vector.feedback}</p>
                                </div>
                                <div className="context-preview" style={{ flex: '1 1 auto', overflowY: 'auto', minHeight: 0 }}>
                                    <h4>Retrieved Docs</h4>
                                    {result.vector.context.map((item: string, idx: number) => (
                                        <div key={idx} className="mini-card">{item.slice(0, 100)}...</div>
                                    ))}
                                </div>
                            </div>

                            {/* Graph Column */}
                            <div className="result-column" style={{ height: '600px', minHeight: '600px', maxHeight: '600px', display: 'flex', flexDirection: 'column' }}>
                                <div className="column-header graph" style={{ flexShrink: 0 }}>
                                    <h3>Graph RAG</h3>
                                    <span className="score-badge">{result.graph.score.toFixed(1)}</span>
                                </div>
                                <div className="metrics-box" style={{ padding: '0.5rem', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
                                    <MetricsRadar metrics={result.graph.metrics} />
                                </div>
                                <div className="feedback-box" style={{ flexShrink: 0, maxHeight: '150px', overflowY: 'auto' }}>
                                    <p>{result.graph.feedback}</p>
                                </div>
                                <div className="context-preview" style={{ flex: '1 1 auto', overflowY: 'auto', minHeight: 0 }}>
                                    <h4>Graph Visualization</h4>
                                    <GraphVisualizer data={result.graph.debug_info?.graph_data} />
                                    <div style={{ marginTop: '1rem' }}>
                                        {result.graph.context.map((item: string, idx: number) => (
                                            <div key={idx} className="mini-tag">{item}</div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Hybrid Column */}
                            <div className="result-column" style={{ height: '600px', minHeight: '600px', maxHeight: '600px', display: 'flex', flexDirection: 'column' }}>
                                <div className="column-header hybrid" style={{ flexShrink: 0 }}>
                                    <h3>Hybrid RAG</h3>
                                    <span className="score-badge">{result.hybrid.score.toFixed(1)}</span>
                                </div>
                                <div className="metrics-box" style={{ padding: '0.5rem', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
                                    <MetricsRadar metrics={result.hybrid.metrics} />
                                </div>
                                <div className="feedback-box" style={{ flexShrink: 0, maxHeight: '150px', overflowY: 'auto' }}>
                                    <p>{result.hybrid.feedback}</p>
                                </div>
                                <div className="context-preview" style={{ flex: '1 1 auto', overflowY: 'auto', minHeight: 0 }}>
                                    <h4>Combined Context</h4>
                                    <p className="summary-text">{result.hybrid.context.length} items retrieved</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <div className="batch-mode">
                    <div className="input-group" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <label style={{ fontWeight: '600' }}>Test Dataset (JSON List of Q&A Pairs)</label>
                            <div className="file-upload-wrapper" style={{ position: 'relative' }}>
                                <input
                                    type="file"
                                    accept=".json"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) {
                                            const reader = new FileReader();
                                            reader.onload = (event) => {
                                                try {
                                                    const json = JSON.parse(event.target?.result as string);
                                                    setBatchData(JSON.stringify(json, null, 2));
                                                } catch (err) {
                                                    alert('Invalid JSON file');
                                                }
                                            };
                                            reader.readAsText(file);
                                        }
                                    }}
                                    style={{ fontSize: '0.8rem' }}
                                />
                            </div>
                        </div>
                        <textarea
                            value={batchData}
                            onChange={(e) => setBatchData(e.target.value)}
                            rows={10}
                            style={{ width: '100%', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)', fontFamily: 'monospace' }}
                        />
                        <button onClick={handleBatchEvaluate} disabled={batchLoading} className="primary-btn" style={{ marginTop: '1rem' }}>
                            {batchLoading ? 'Running Batch Eval...' : 'Run Batch Evaluation'}
                        </button>
                    </div>

                    {avgScore !== null && (
                        <div className="batch-results" style={{ marginTop: '2rem' }}>
                            <div className="summary-card" style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem', border: '1px solid var(--success-color)' }}>
                                <h3 style={{ margin: 0, color: 'var(--success-color)' }}>Average Overall Score: {(avgScore * 100).toFixed(1)}%</h3>
                            </div>

                            {/* Group results by question */}
                            {(() => {
                                // Group by question
                                const grouped: { [key: string]: typeof batchResults } = {};
                                batchResults.forEach(res => {
                                    if (!grouped[res.question]) grouped[res.question] = [];
                                    grouped[res.question].push(res);
                                });

                                return Object.entries(grouped).map(([question, strategies], qIdx) => {
                                    // Sort strategies in order: Vector, Graph, Hybrid
                                    const sortedStrategies = strategies.sort((a, b) => {
                                        const order = { 'Vector': 1, 'Graph': 2, 'Hybrid': 3 };
                                        return order[a.strategy as keyof typeof order] - order[b.strategy as keyof typeof order];
                                    });

                                    return (
                                        <div key={qIdx} style={{ marginBottom: '3rem' }}>
                                            <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                                <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>Question {qIdx + 1}</h4>
                                                <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.95rem' }}>{question}</p>
                                            </div>

                                            <div className="comparison-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
                                                {sortedStrategies.map((res, sIdx) => {
                                                    const strategyColors = {
                                                        'Vector': { bg: 'rgba(59, 130, 246, 0.05)', color: '#3b82f6' },
                                                        'Graph': { bg: 'rgba(168, 85, 247, 0.05)', color: '#a855f7' },
                                                        'Hybrid': { bg: 'rgba(16, 185, 129, 0.05)', color: '#10b981' }
                                                    };
                                                    const colors = strategyColors[res.strategy as keyof typeof strategyColors];

                                                    return (
                                                        <div key={sIdx} className="result-column" style={{ background: 'var(--card-bg)', borderRadius: '12px', border: '1px solid var(--border-color)', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '400px', minHeight: '400px', maxHeight: '400px' }}>
                                                            <div className="column-header" style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', background: colors.bg, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                                                                <h3 style={{ margin: 0, fontSize: '1rem', color: colors.color }}>{res.strategy}</h3>
                                                                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.color }}>
                                                                    {(res.metrics.overall * 100).toFixed(0)}%
                                                                </span>
                                                            </div>

                                                            <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
                                                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.75rem' }}>
                                                                    <div style={{ textAlign: 'center' }}>
                                                                        <div style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>ROUGE-L</div>
                                                                        <div style={{ fontWeight: 'bold', color: res.metrics.rouge_l > 0.7 ? 'var(--success-color)' : res.metrics.rouge_l > 0.4 ? 'var(--warning-color)' : 'var(--error-color)' }}>
                                                                            {res.metrics.rouge_l.toFixed(2)}
                                                                        </div>
                                                                    </div>
                                                                    <div style={{ textAlign: 'center' }}>
                                                                        <div style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Faith.</div>
                                                                        <div style={{ fontWeight: 'bold', color: res.metrics.faithfulness > 0.7 ? 'var(--success-color)' : res.metrics.faithfulness > 0.4 ? 'var(--warning-color)' : 'var(--error-color)' }}>
                                                                            {res.metrics.faithfulness.toFixed(2)}
                                                                        </div>
                                                                    </div>
                                                                    <div style={{ textAlign: 'center' }}>
                                                                        <div style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Relev.</div>
                                                                        <div style={{ fontWeight: 'bold', color: res.metrics.answer_relevance > 0.7 ? 'var(--success-color)' : res.metrics.answer_relevance > 0.4 ? 'var(--warning-color)' : 'var(--error-color)' }}>
                                                                            {res.metrics.answer_relevance.toFixed(2)}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            <div style={{ padding: '1rem', fontSize: '0.85rem', lineHeight: '1.6', color: 'var(--text-primary)', overflowY: 'auto', flex: '1 1 auto', minHeight: 0 }}>
                                                                <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>System Answer:</div>
                                                                {res.system_answer}
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    );
                                });
                            })()}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default EvaluationStudio;
