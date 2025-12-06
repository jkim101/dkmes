import React from 'react';
import { AssessmentResult, FeedbackStats } from './types';

interface AssessmentOverviewProps {
    assessment: AssessmentResult | null;
    feedbackStats: FeedbackStats | null;
    history: any[];
}

const AssessmentOverview: React.FC<AssessmentOverviewProps> = ({ assessment, feedbackStats, history }) => {

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
    );
};

export default AssessmentOverview;
