import { useState, Suspense, lazy } from 'react'
import { LayoutDashboard, Database, MessageSquare, Activity, Share2, Settings, BarChart2, Network } from 'lucide-react';
import './App.css'

// Lazy Load heavy components
const FileUploader = lazy(() => import('./components/FileUploader'));
// GraphVisualizer is seemingly unused directly in App.tsx or used inside others, checking usage... it was imported but not used in App.tsx rendering logic in previous view.
// Let's keep it lazy if it was there, or remove if unused. It was unused in the previous file content view (line 7 imported, never used). I'll skip it.
import DashboardStats from './components/DashboardStats'; // Keep eager for critical path (Dashboard)
const Playground = lazy(() => import('./components/Playground'));
const GraphExplorer = lazy(() => import('./components/GraphExplorer'));
const EvaluationStudio = lazy(() => import('./components/EvaluationStudio'));
const TraceInspector = lazy(() => import('./components/TraceInspector'));
const AssessmentDashboard = lazy(() => import('./components/AssessmentDashboard'));
const Orchestrator = lazy(() => import('./components/Orchestrator'));
const SettingsComponent = lazy(() => import('./components/Settings'));
const ActivityCharts = lazy(() => import('./components/ActivityCharts'));

// Simple Loading Component
const PageLoader = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-secondary)' }}>
        <div className="loader-spinner"></div> {/* We can add CSS for this later or just text */}
        <p>Loading module...</p>
    </div>
);

function App() {
    const [activeTab, setActiveTab] = useState('dashboard')


    return (
        <div className="app-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="logo-area">
                    <div className="logo-icon">
                        <div className="logo-inner"></div>
                    </div>
                    <h2>DKMES</h2>
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
                    <Suspense fallback={<PageLoader />}>
                        {activeTab === 'dashboard' && (
                            <div className="dashboard-view">
                                <div className="welcome-banner">
                                    <h1>DKMES - Data Knowledge Management Eco-System</h1>
                                    <p>Here's what's happening with your knowledge base today.</p>
                                </div>
                                <DashboardStats />
                                {/* Activity Charts */}
                                <ActivityCharts />
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
                    </Suspense>
                </div>
            </div>
        </div>
    );
}

export default App
