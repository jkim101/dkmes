import { useState } from 'react'
import { LayoutDashboard, Database, MessageSquare, Activity, Share2, Settings, BarChart2, Network, ChevronRight, Bell, Search } from 'lucide-react';
import './App.css'


import FileUploader from './components/FileUploader';
import GraphVisualizer from './components/GraphVisualizer';
import DashboardStats from './components/DashboardStats';
import Playground from './components/Playground';
import GraphExplorer from './components/GraphExplorer';
import EvaluationStudio from './components/EvaluationStudio';
import TraceInspector from './components/TraceInspector';
import AssessmentDashboard from './components/AssessmentDashboard';
import Orchestrator from './components/Orchestrator';
import SettingsComponent from './components/Settings'; // Rename import to avoid conflict with Icon

function App() {
    const [activeTab, setActiveTab] = useState('dashboard')
    const [refreshStats, setRefreshStats] = useState(0)

    const handleUploadSuccess = () => {
        setRefreshStats(prev => prev + 1);
    };

    return (
        <div className="app-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="logo-area">
                    <div className="logo-icon">
                        <div className="logo-inner"></div>
                    </div>
                    <h2>DKMES</h2>
                    <span className="badge">Admin</span>

                </div>

                <nav className="nav-menu">
                    <button className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
                        <LayoutDashboard size={20} /> Dashboard
                    </button>
                    <button className={`nav-item ${activeTab === 'data' ? 'active' : ''}`} onClick={() => setActiveTab('data')}>
                        <Database size={20} /> Data Manager
                    </button>
                    <button className={`nav-item ${activeTab === 'playground' ? 'active' : ''}`} onClick={() => setActiveTab('playground')}>
                        <MessageSquare size={20} /> Playground
                    </button>
                    <button className={`nav-item ${activeTab === 'evaluate' ? 'active' : ''}`} onClick={() => setActiveTab('evaluate')}>
                        <BarChart2 size={20} /> Evaluation Studio
                    </button>
                    <button className={`nav-item ${activeTab === 'graph' ? 'active' : ''}`} onClick={() => setActiveTab('graph')}>
                        <Network size={20} /> Graph Explorer
                    </button>
                    <button className={`nav-item ${activeTab === 'inspector' ? 'active' : ''}`} onClick={() => setActiveTab('inspector')}>
                        <Activity size={20} /> Inspector
                    </button>
                    <button className={`nav-item ${activeTab === 'assessment' ? 'active' : ''}`} onClick={() => setActiveTab('assessment')}>
                        <Share2 size={20} /> Assessment
                    </button>
                    <button className={`nav-item ${activeTab === 'orchestrator' ? 'active' : ''}`} onClick={() => setActiveTab('orchestrator')}>
                        <Network size={20} /> Orchestrator
                    </button>
                    <button className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
                        <Settings size={20} /> Settings
                    </button>
                </nav>


            </div>

            <div className="main-content">
                <header className="top-bar">


                </header>

                <div className="content-area">
                    {activeTab === 'dashboard' && (
                        <div className="dashboard-view">
                            <div className="welcome-banner">
                                <h1>DKMES - Data Knowledge Management System</h1>
                                <p>Here's what's happening with your knowledge base today.</p>
                            </div>
                            <DashboardStats />
                            {/* Placeholder for recent activity or charts */}
                            <div className="card" style={{ marginTop: '2rem', height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                                <p>System Activity Chart (Coming Soon)</p>
                            </div>
                        </div>
                    )}
                    {activeTab === 'playground' && <Playground />}
                    {activeTab === 'graph' && <GraphExplorer />}
                    {activeTab === 'data' && <FileUploader />}
                    {activeTab === 'inspector' && <TraceInspector />}
                    {activeTab === 'evaluate' && <EvaluationStudio />}
                    {activeTab === 'assessment' && <AssessmentDashboard />}
                    {activeTab === 'orchestrator' && <Orchestrator />}
                    {activeTab === 'settings' && <SettingsComponent />}
                </div>
            </div>
        </div>
    );
}

export default App
