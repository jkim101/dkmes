import React, { useEffect, useState, useRef } from 'react';
import { FileText, Network, Link, Zap } from 'lucide-react';
import '../App.css';

interface SystemStats {
    vector_chunks: number;
    graph_nodes: number;
    graph_edges: number;
    status: string;
}

// Custom Hook for Counting Animation
const useCountUp = (end: number, duration: number = 2000) => {
    const [count, setCount] = useState(0);
    const countRef = useRef(0);

    useEffect(() => {
        let startTime: number | null = null;
        const start = countRef.current; // Start from previous value

        const step = (timestamp: number) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);

            // Ease-out expo function
            const easeOut = (x: number) => x === 1 ? 1 : 1 - Math.pow(2, -10 * x);

            const currentCount = Math.floor(start + (end - start) * easeOut(progress));
            setCount(currentCount);
            countRef.current = currentCount;

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
    }, [end, duration]);

    return count;
};

const StatCard: React.FC<{ icon: React.ReactNode, label: string, value: number, type: string }> = ({ icon, label, value, type }) => {
    const displayValue = useCountUp(value);

    return (
        <div className={`stat-card ${type}`}>
            <div className={`stat-icon ${type}`}>{icon}</div>
            <div className="stat-info">
                <span className="stat-value">{displayValue.toLocaleString()}</span>
                <span className="stat-label">{label}</span>
            </div>
        </div>
    );
};

const DashboardStats: React.FC<{ refreshTrigger?: number }> = ({ refreshTrigger }) => {
    const [stats, setStats] = useState<SystemStats>({
        vector_chunks: 0,
        graph_nodes: 0,
        graph_edges: 0,
        status: 'offline'
    });

    useEffect(() => {
        fetchStats();
    }, [refreshTrigger]);

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/v1/stats');
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    return (
        <div className="stats-grid fade-in">
            <StatCard icon={<FileText size={28} />} label="Vector Chunks" value={stats.vector_chunks} type="vector" />
            <StatCard icon={<Network size={28} />} label="Graph Nodes" value={stats.graph_nodes} type="graph" />
            <StatCard icon={<Link size={28} />} label="Relationships" value={stats.graph_edges} type="edge" />

            <div className="stat-card status">
                <div className="stat-icon status"><Zap size={28} /></div>
                <div className="stat-info">
                    <span className="stat-value" style={{ fontSize: '1.2rem', textTransform: 'uppercase' }}>{stats.status}</span>
                    <span className="stat-label">System Status</span>
                </div>
            </div>
        </div>
    );
};

export default DashboardStats;
