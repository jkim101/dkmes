import React, { useState, useEffect } from 'react';
import {
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell,
    LineChart, Line, AreaChart, Area
} from 'recharts';

interface ActivityStats {
    query_timeline: { period: string; count: number }[];
    strategy_distribution: { name: string; value: number }[];
    latency_stats: { avg: number; min: number; max: number; total: number };
    latency_trend: { period: string; latency: number }[];
}

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#6b7280'];
const STRATEGY_COLORS: Record<string, string> = {
    'vector': '#3b82f6',
    'graph': '#8b5cf6',
    'hybrid': '#10b981',
    'unknown': '#6b7280'
};

const ActivityCharts: React.FC = () => {
    const [stats, setStats] = useState<ActivityStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState<1 | 7>(7);

    useEffect(() => {
        fetchStats();
    }, [timeRange]);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/v1/activity-stats?days=${timeRange}`);
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (e) {
            console.error('Failed to fetch activity stats:', e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px', color: 'var(--text-secondary)' }}>
                Loading charts...
            </div>
        );
    }

    if (!stats) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px', color: 'var(--text-secondary)' }}>
                No activity data available
            </div>
        );
    }

    const hasData = stats.query_timeline.length > 0 || stats.strategy_distribution.length > 0;

    return (
        <div style={{ marginTop: '2rem' }}>
            {/* Time Range Toggle */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>📊 System Activity</h3>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        onClick={() => setTimeRange(1)}
                        style={{
                            padding: '0.4rem 0.8rem',
                            background: timeRange === 1 ? 'var(--accent-color)' : 'var(--bg-secondary)',
                            color: timeRange === 1 ? 'white' : 'var(--text-primary)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        24h
                    </button>
                    <button
                        onClick={() => setTimeRange(7)}
                        style={{
                            padding: '0.4rem 0.8rem',
                            background: timeRange === 7 ? 'var(--accent-color)' : 'var(--bg-secondary)',
                            color: timeRange === 7 ? 'white' : 'var(--text-primary)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        7 Days
                    </button>
                </div>
            </div>

            {!hasData ? (
                <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    <p>No queries recorded yet. Start asking questions to see activity!</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    {/* Query Activity Timeline */}
                    <div className="card" style={{ padding: '1rem' }}>
                        <h4 style={{ margin: '0 0 1rem 0', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
                            Query Activity ({timeRange === 1 ? 'Hourly' : 'Daily'})
                        </h4>
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={stats.query_timeline}>
                                <defs>
                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                <XAxis
                                    dataKey="period"
                                    tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
                                    tickFormatter={(v) => timeRange === 1 ? `${v}h` : v.slice(5)}
                                />
                                <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'var(--bg-color)',
                                        border: '1px solid var(--border-color)',
                                        borderRadius: '8px'
                                    }}
                                />
                                <Area type="monotone" dataKey="count" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCount)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* RAG Strategy Distribution */}
                    <div className="card" style={{ padding: '1rem' }}>
                        <h4 style={{ margin: '0 0 1rem 0', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
                            RAG Strategy Distribution
                        </h4>
                        {stats.strategy_distribution.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <PieChart>
                                    <Pie
                                        data={stats.strategy_distribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={50}
                                        outerRadius={70}
                                        paddingAngle={5}
                                        dataKey="value"
                                        label={({ name, percent = 0 }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                        labelLine={false}
                                    >
                                        {stats.strategy_distribution.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={STRATEGY_COLORS[entry.name] || COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                                No strategy data
                            </div>
                        )}
                    </div>

                    {/* Response Latency Trend */}
                    <div className="card" style={{ padding: '1rem', gridColumn: 'span 2' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
                                Response Latency Trend
                            </h4>
                            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>
                                    Avg: <strong style={{ color: '#10b981' }}>{stats.latency_stats.avg}s</strong>
                                </span>
                                <span style={{ color: 'var(--text-secondary)' }}>
                                    Min: <strong style={{ color: '#3b82f6' }}>{stats.latency_stats.min}s</strong>
                                </span>
                                <span style={{ color: 'var(--text-secondary)' }}>
                                    Max: <strong style={{ color: '#ef4444' }}>{stats.latency_stats.max}s</strong>
                                </span>
                            </div>
                        </div>
                        {stats.latency_trend.length > 0 ? (
                            <ResponsiveContainer width="100%" height={180}>
                                <LineChart data={stats.latency_trend}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                    <XAxis
                                        dataKey="period"
                                        tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
                                        tickFormatter={(v) => timeRange === 1 ? `${v}h` : v.slice(5)}
                                    />
                                    <YAxis
                                        tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
                                        tickFormatter={(v) => `${v}s`}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            background: 'var(--bg-color)',
                                            border: '1px solid var(--border-color)',
                                            borderRadius: '8px'
                                        }}
                                        formatter={(value: number) => [`${value}s`, 'Avg Latency']}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="latency"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        dot={{ fill: '#10b981', strokeWidth: 2 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                                No latency data recorded
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ActivityCharts;
