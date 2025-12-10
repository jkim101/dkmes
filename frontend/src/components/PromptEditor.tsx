import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import './Settings.css'; // Reuse Settings CSS for now



const PromptEditor: React.FC = () => {
    const [prompts, setPrompts] = useState<Record<string, string>>({});
    const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
    const [editContent, setEditContent] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<{ msg: string; type: 'success' | 'error' | '' }>({ msg: '', type: '' });

    useEffect(() => {
        fetchPrompts();
    }, []);

    useEffect(() => {
        if (selectedPrompt && prompts[selectedPrompt]) {
            setEditContent(prompts[selectedPrompt]);
            setStatus({ msg: '', type: '' });
        }
    }, [selectedPrompt, prompts]);

    const fetchPrompts = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/v1/prompts');
            if (res.ok) {
                const data = await res.json();
                setPrompts(data);
                if (!selectedPrompt && Object.keys(data).length > 0) {
                    setSelectedPrompt(Object.keys(data)[0]);
                }
            }
        } catch (error) {
            console.error("Failed to fetch prompts", error);
            setStatus({ msg: 'Failed to load prompts list.', type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!selectedPrompt) return;

        setLoading(true);
        setStatus({ msg: '', type: '' });

        try {
            const res = await fetch(`/api/v1/prompts/${selectedPrompt}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: editContent })
            });

            if (res.ok) {
                setPrompts(prev => ({ ...prev, [selectedPrompt]: editContent }));
                setStatus({ msg: `Saved '${selectedPrompt}' successfully!`, type: 'success' });
            } else {
                setStatus({ msg: 'Failed to save prompt.', type: 'error' });
            }
        } catch (error) {
            setStatus({ msg: `Error: ${error}`, type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        if (selectedPrompt && prompts[selectedPrompt]) {
            setEditContent(prompts[selectedPrompt]);
            setStatus({ msg: 'Reset to last saved version.', type: '' });
        }
    };

    return (
        <div className="prompt-editor-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>
            <div className="settings-header">
                <h2><FileText className="icon" /> Prompt Studio</h2>
                <p>Fine-tune system prompts and personas dynamically.</p>
            </div>

            {status.msg && (
                <div className={`status-message ${status.type}`} style={{
                    padding: '0.75rem',
                    borderRadius: '6px',
                    background: status.type === 'success' ? '#10b98120' : '#ef444420',
                    color: status.type === 'success' ? '#10b981' : '#ef4444',
                    display: 'flex', alignItems: 'center', gap: '0.5rem'
                }}>
                    {status.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                    {status.msg}
                </div>
            )}

            <div style={{ display: 'flex', flex: 1, gap: '1.5rem', minHeight: '0' }}>
                {/* Sidebar List */}
                <div className="card" style={{ width: '250px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', fontWeight: '600', background: 'var(--bg-secondary)' }}>
                        Prompts List
                    </div>
                    <div style={{ overflowY: 'auto', flex: 1 }}>
                        {Object.keys(prompts).map(name => (
                            <div
                                key={name}
                                onClick={() => setSelectedPrompt(name)}
                                style={{
                                    padding: '0.75rem 1rem',
                                    cursor: 'pointer',
                                    background: selectedPrompt === name ? 'var(--accent-color)' : 'transparent',
                                    color: selectedPrompt === name ? 'white' : 'var(--text-primary)',
                                    borderBottom: '1px solid var(--border-color)',
                                    fontSize: '0.9rem',
                                    transition: 'background 0.2s'
                                }}
                            >
                                {name}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Editor Area */}
                <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{
                        padding: '1rem',
                        borderBottom: '1px solid var(--border-color)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        background: 'var(--bg-secondary)'
                    }}>
                        <span style={{ fontWeight: '600' }}>
                            {selectedPrompt ? `Editing: ${selectedPrompt}` : 'Select a prompt'}
                        </span>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                                onClick={handleReset}
                                disabled={loading || !selectedPrompt}
                                style={{
                                    padding: '0.4rem 0.8rem',
                                    background: 'transparent',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '6px',
                                    color: 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem'
                                }}
                            >
                                <RefreshCw size={14} /> Reset
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={loading || !selectedPrompt}
                                style={{
                                    padding: '0.4rem 1rem',
                                    background: 'var(--accent-color)',
                                    border: 'none',
                                    borderRadius: '6px',
                                    color: 'white',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem'
                                }}
                            >
                                <Save size={14} /> {loading ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>

                    <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        disabled={!selectedPrompt}
                        style={{
                            flex: 1,
                            padding: '1rem',
                            border: 'none',
                            resize: 'none',
                            outline: 'none',
                            background: 'var(--bg-primary)',
                            color: 'var(--text-primary)',
                            fontFamily: 'monospace',
                            fontSize: '0.9rem',
                            lineHeight: '1.5'
                        }}
                        spellCheck={false}
                    />

                    <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Tip: Maintain the placeholders (e.g., {'{context}'}) to ensure the system functions correctly.
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PromptEditor;
