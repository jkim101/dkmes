import React, { useState, useEffect } from 'react';
import { Save, Cpu, Database, Layers, FileText } from 'lucide-react';
import PromptEditor from './PromptEditor';
import './Settings.css'; // We'll create a basic CSS file or inline styles

interface SystemSettings {
    llm_model: string;
    temperature: number;
    max_output_tokens: number;
    rag_strategy: string;
    top_k: number;
    chunk_size: number;
    chunk_overlap: number;
    graph_depth: number;
    system_prompt_override: string | null;
}

const Settings: React.FC = () => {
    const [settings, setSettings] = useState<SystemSettings>({
        llm_model: "gemini-2.0-flash-exp",
        temperature: 0.2,
        max_output_tokens: 8192,
        rag_strategy: "hybrid",
        top_k: 5,
        chunk_size: 1000,
        chunk_overlap: 200,
        graph_depth: 2,
        system_prompt_override: null
    });
    const [loading, setLoading] = useState(false);
    const [statusData, setStatusData] = useState<{ message: string, type: 'success' | 'error' | '' }>({ message: '', type: '' });

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/v1/settings');
            if (res.ok) {
                const data = await res.json();
                setSettings(data);
            }
        } catch (error) {
            console.error("Failed to fetch settings", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        setStatusData({ message: '', type: '' });
        try {
            const res = await fetch('/api/v1/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            if (res.ok) {
                const data = await res.json();
                setSettings(data);
                setStatusData({ message: 'Settings saved successfully!', type: 'success' });
            } else {
                setStatusData({ message: 'Failed to save settings.', type: 'error' });
            }
        } catch (error) {
            setStatusData({ message: `Error: ${error}`, type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field: keyof SystemSettings, value: any) => {
        setSettings(prev => ({ ...prev, [field]: value }));
    };

    const [activeTab, setActiveTab] = useState<'config' | 'prompts'>('config');

    // ... (keep fetchSettings, handleSave, handleChange logic)

    return (
        <div className="settings-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
                <button
                    onClick={() => setActiveTab('config')}
                    style={{
                        padding: '0.75rem 1rem',
                        background: 'none',
                        border: 'none',
                        borderBottom: activeTab === 'config' ? '2px solid var(--accent-color)' : '2px solid transparent',
                        color: activeTab === 'config' ? 'var(--accent-color)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'config' ? '600' : 'normal',
                        cursor: 'pointer',
                        display: 'flex', alignItems: 'center', gap: '0.5rem'
                    }}
                >
                    <Layers size={18} /> System Config
                </button>
                <button
                    onClick={() => setActiveTab('prompts')}
                    style={{
                        padding: '0.75rem 1rem',
                        background: 'none',
                        border: 'none',
                        borderBottom: activeTab === 'prompts' ? '2px solid var(--accent-color)' : '2px solid transparent',
                        color: activeTab === 'prompts' ? 'var(--accent-color)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'prompts' ? '600' : 'normal',
                        cursor: 'pointer',
                        display: 'flex', alignItems: 'center', gap: '0.5rem'
                    }}
                >
                    <FileText size={18} /> Prompt Studio
                </button>
            </div>

            {activeTab === 'prompts' ? (
                <PromptEditor />
            ) : (
                <>
                    <div className="settings-header">
                        <h2><Layers className="icon" /> System Configuration</h2>
                        <p>Manage LLM parameters, Retrieval Augmented Generation (RAG) strategies, and system behaviors.</p>
                    </div>

                    {statusData.message && (
                        <div className={`status-message ${statusData.type}`}>
                            {statusData.message}
                        </div>
                    )}

                    <div className="settings-grid">
                        {/* LLM Configuration */}
                        <div className="settings-card">
                            <div className="card-header">
                                <Cpu size={20} />
                                <h3>LLM Parameters</h3>
                            </div>
                            <div className="form-group">
                                <label>Model Name</label>
                                <select
                                    value={settings.llm_model}
                                    onChange={(e) => handleChange('llm_model', e.target.value)}
                                >
                                    <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Experimental)</option>
                                    <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Temperature ({settings.temperature})</label>
                                <input
                                    type="range" min="0" max="1" step="0.1"
                                    value={settings.temperature}
                                    onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                                />
                            </div>
                            <div className="form-group">
                                <label>Max Output Tokens</label>
                                <input
                                    type="number"
                                    value={settings.max_output_tokens}
                                    onChange={(e) => handleChange('max_output_tokens', parseInt(e.target.value))}
                                />
                            </div>
                        </div>

                        {/* RAG Configuration */}
                        <div className="settings-card">
                            <div className="card-header">
                                <Database size={20} />
                                <h3>RAG & Retrieval</h3>
                            </div>
                            <div className="form-group">
                                <label>Default Strategy</label>
                                <select
                                    value={settings.rag_strategy}
                                    onChange={(e) => handleChange('rag_strategy', e.target.value)}
                                >
                                    <option value="vector">Vector Only</option>
                                    <option value="graph">Graph Only</option>
                                    <option value="hybrid">Hybrid (Vector + Graph)</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Top K Results</label>
                                <input
                                    type="number" min="1" max="20"
                                    value={settings.top_k}
                                    onChange={(e) => handleChange('top_k', parseInt(e.target.value))}
                                />
                            </div>
                            <div className="form-group">
                                <label>Graph Traversal Depth</label>
                                <input
                                    type="number" min="1" max="3"
                                    value={settings.graph_depth}
                                    onChange={(e) => handleChange('graph_depth', parseInt(e.target.value))}
                                />
                            </div>
                        </div>

                        {/* Ingestion Settings (Visual only for now if not dynamic) */}
                        <div className="settings-card">
                            <div className="card-header">
                                <Layers size={20} />
                                <h3>Ingestion Config</h3>
                            </div>
                            <div className="form-group">
                                <label>Chunk Size (Tokens)</label>
                                <input
                                    type="number"
                                    value={settings.chunk_size}
                                    onChange={(e) => handleChange('chunk_size', parseInt(e.target.value))}
                                />
                            </div>
                            <div className="form-group">
                                <label>Chunk Overlap</label>
                                <input
                                    type="number"
                                    value={settings.chunk_overlap}
                                    onChange={(e) => handleChange('chunk_overlap', parseInt(e.target.value))}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="settings-actions">
                        <button className="btn-save" onClick={handleSave} disabled={loading}>
                            <Save size={18} /> {loading ? 'Saving...' : 'Save Configuration'}
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default Settings;
