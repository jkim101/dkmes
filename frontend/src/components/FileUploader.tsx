import React, { useState, useEffect } from 'react';
import '../App.css';
import { Upload, FileText, RefreshCw, Database, AlertCircle, CheckCircle2, Circle } from 'lucide-react';

interface UploadedFile {
    filename: string;
    size: number;
    status: string;
}

interface SystemStats {
    vector_chunks: number;
    graph_nodes: number;
    graph_edges: number;
}

type ProcessingStep = 'idle' | 'uploading' | 'chunking' | 'graph' | 'complete';

const FileUploader: React.FC = () => {
    // State for Upload
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [uploadMode, setUploadMode] = useState<'append' | 'replace'>('append');
    const [processingStep, setProcessingStep] = useState<ProcessingStep>('idle');
    const [showReplaceModal, setShowReplaceModal] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');

    // State for Indexed Knowledge
    const [indexedFiles, setIndexedFiles] = useState<UploadedFile[]>([]);
    const [stats, setStats] = useState<SystemStats>({ vector_chunks: 0, graph_nodes: 0, graph_edges: 0 });
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setRefreshing(true);
        await Promise.all([fetchDocuments(), fetchStats()]);
        setRefreshing(false);
    };

    const fetchDocuments = async () => {
        try {
            const response = await fetch('/api/v1/documents');
            if (response.ok) {
                const data = await response.json();
                setIndexedFiles(data);
            }
        } catch (error) {
            console.error('Error fetching documents:', error);
        }
    };

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

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setSelectedFiles(Array.from(event.target.files));
            setProcessingStep('idle');
        }
    };

    const initiateUpload = () => {
        if (selectedFiles.length === 0) return;

        if (uploadMode === 'replace') {
            setShowReplaceModal(true);
        } else {
            startUploadProcess();
        }
    };

    const startUploadProcess = async () => {
        setShowReplaceModal(false);
        setProcessingStep('uploading');

        // Simulate steps for better UX since backend is monolithic per file
        // In a real streaming setup, we'd listen for events.

        let successCount = 0;

        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            const currentMode = (uploadMode === 'replace' && i === 0) ? 'replace' : 'append';

            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('mode', currentMode);

                // Fake progress transition
                setTimeout(() => setProcessingStep('chunking'), 1000);
                setTimeout(() => setProcessingStep('graph'), 3000);

                const response = await fetch('/api/v1/documents/upload', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.details?.graph === 'failed' && data.details?.vector === 'failed') {
                        console.error(`Ingestion failed for ${file.name}:`, data);
                        setUploadStatus(`Failed to ingest ${file.name}`);
                    } else {
                        successCount++;
                    }
                } else {
                    console.error(`Upload failed for ${file.name}`);
                    setUploadStatus(`Upload failed for ${file.name}`);
                }
            } catch (error) {
                console.error(`Error uploading ${file.name}:`, error);
                setUploadStatus(`Error uploading ${file.name}`);
            }
        }

        setProcessingStep('complete');
        setTimeout(() => {
            setSelectedFiles([]);
            setProcessingStep('idle');
            fetchData();
        }, 2000);
    };

    const clearSelection = () => {
        setSelectedFiles([]);
        setProcessingStep('idle');
    };

    // Helper to clean filename (remove UUID prefix if present)
    const cleanFilename = (filename: string) => {
        // UUID pattern: 8-4-4-4-12 chars, followed by underscore
        const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_/i;
        return filename.replace(uuidPattern, '');
    };

    // Helper to render step icon
    const StepIcon = ({ step, currentStep }: { step: ProcessingStep, currentStep: ProcessingStep }) => {
        const stepsOrder = ['uploading', 'chunking', 'graph', 'complete'];
        const stepIdx = stepsOrder.indexOf(step);
        const currentIdx = stepsOrder.indexOf(currentStep);

        if (currentStep === 'complete' || currentIdx > stepIdx) {
            return <div style={{ color: 'var(--success-color)' }}><CheckCircle2 size={20} /></div>;
        }
        if (currentStep === step) {
            return <div className="spinner-sm"></div>;
        }
        return <div style={{ color: 'var(--border-color)' }}><Circle size={20} /></div>;
    };

    return (
        <div className="data-manager-container" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem', height: '100%' }}>

            {/* Modal */}
            {showReplaceModal && (
                <div className="modal-overlay">
                    <div className="modal-card">
                        <div className="modal-icon">
                            <AlertCircle size={32} />
                        </div>
                        <h3 className="modal-title">Confirm Clear & Replace</h3>
                        <p className="modal-body">
                            This will <strong>permanently delete all {indexedFiles.length} existing documents</strong> and re-initialize the RAG system with only the new uploads.
                        </p>
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowReplaceModal(false)}>Cancel</button>
                            <button className="btn-danger" onClick={startUploadProcess}>Confirm & Replace</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Left Column: Upload Section */}
            <div className="upload-section card" style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="card-header">
                    <h3><Upload size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} /> Upload New Documents</h3>
                </div>

                <div className="upload-dropzone" style={{
                    flex: 1,
                    border: '2px dashed var(--border-color)',
                    borderRadius: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '3rem',
                    marginBottom: '1.5rem',
                    background: 'rgba(255,255,255,0.02)',
                    position: 'relative'
                }}>
                    <input
                        type="file"
                        multiple
                        accept=".txt,.md,.json,.pdf,.docx,.html"
                        onChange={handleFileSelect}
                        style={{ position: 'absolute', width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
                        disabled={processingStep !== 'idle'}
                    />
                    <div style={{ background: 'var(--accent-color)', borderRadius: '50%', padding: '1rem', marginBottom: '1rem', opacity: 0.2 }}>
                        <Upload size={32} color="white" />
                    </div>
                    <h4 style={{ margin: '0 0 0.5rem 0' }}>Drag & drop files here, or <span style={{ color: 'var(--accent-color)' }}>browse</span></h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>PDF, DOCX, TXT, MD, HTML (Max 10MB)</p>
                </div>

                {selectedFiles.length > 0 && processingStep === 'idle' && (
                    <div className="selected-files-preview" style={{ marginBottom: '1.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <span style={{ fontWeight: '600' }}>Selected Files ({selectedFiles.length})</span>
                            <button onClick={clearSelection} style={{ background: 'none', border: 'none', color: 'var(--error-color)', cursor: 'pointer', fontSize: '0.9rem' }}>Clear All</button>
                        </div>
                        <div style={{ maxHeight: '150px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                            {selectedFiles.map((f, idx) => (
                                <div key={idx} style={{ padding: '0.5rem 1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', fontSize: '0.9rem' }}>
                                    <FileText size={14} style={{ marginRight: '0.5rem', opacity: 0.7 }} />
                                    {f.name} <span style={{ marginLeft: 'auto', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{(f.size / 1024).toFixed(1)} KB</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {processingStep !== 'idle' && (
                    <div className="processing-status-card">
                        <div className="status-header">Processing Status</div>

                        <div className="status-step">
                            <div className="step-icon"><StepIcon step="uploading" currentStep={processingStep} /></div>
                            <div className="step-info">
                                <span className="step-title">Uploading Files</span>
                                <span className="step-desc">Transferring documents to server...</span>
                            </div>
                        </div>

                        <div className="status-step">
                            <div className="step-icon"><StepIcon step="chunking" currentStep={processingStep} /></div>
                            <div className="step-info">
                                <span className="step-title">Chunking & Embedding</span>
                                <span className="step-desc">Splitting text and generating vector embeddings</span>
                            </div>
                        </div>

                        <div className="status-step">
                            <div className="step-icon"><StepIcon step="graph" currentStep={processingStep} /></div>
                            <div className="step-info">
                                <span className="step-title">Building Knowledge Graph</span>
                                <span className="step-desc">Extracting entities and relationships</span>
                            </div>
                        </div>
                        {uploadStatus && (
                            <div className="status-step" style={{ color: 'var(--error-color)', marginTop: '1rem' }}>
                                <AlertCircle size={20} style={{ marginRight: '0.5rem' }} /> {uploadStatus}
                            </div>
                        )}
                    </div>
                )}

                <div className="upload-controls" style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div className="mode-selector" style={{ display: 'flex', gap: '1.5rem' }}>
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                            <input
                                type="radio"
                                name="uploadMode"
                                value="append"
                                checked={uploadMode === 'append'}
                                onChange={() => setUploadMode('append')}
                                disabled={processingStep !== 'idle'}
                                style={{ marginRight: '0.5rem' }}
                            />
                            Append
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                            <input
                                type="radio"
                                name="uploadMode"
                                value="replace"
                                checked={uploadMode === 'replace'}
                                onChange={() => setUploadMode('replace')}
                                disabled={processingStep !== 'idle'}
                                style={{ marginRight: '0.5rem' }}
                            />
                            Replace All
                        </label>
                    </div>

                    <button
                        className="primary-btn"
                        onClick={initiateUpload}
                        disabled={processingStep !== 'idle' || selectedFiles.length === 0}
                        style={{ background: uploadMode === 'replace' ? 'var(--error-color)' : 'var(--accent-color)' }}
                    >
                        {processingStep !== 'idle' ? 'Processing...' : (uploadMode === 'replace' ? 'Replace All' : 'Upload Files')}
                    </button>
                </div>
            </div>

            {/* Right Column: Indexed Knowledge */}
            <div className="indexed-section card" style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3><Database size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} /> Indexed Knowledge</h3>
                    <button onClick={fetchData} style={{ background: 'none', border: 'none', cursor: 'pointer', opacity: 0.7 }} title="Refresh">
                        <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
                    </button>
                </div>

                {/* Stats Cards */}
                <div className="stats-mini-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#3b82f6' }}>{stats.vector_chunks}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Chunks</div>
                    </div>
                    <div style={{ background: 'rgba(168, 85, 247, 0.1)', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#a855f7' }}>{stats.graph_nodes}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Graph Nodes</div>
                    </div>
                </div>

                {/* File List */}
                <div className="indexed-file-list" style={{ flex: 1, overflowY: 'auto' }}>
                    {indexedFiles.length > 0 ? (
                        indexedFiles.map((file, idx) => (
                            <div key={idx} style={{
                                padding: '1rem',
                                background: 'var(--bg-color)',
                                marginBottom: '0.8rem',
                                borderRadius: '8px',
                                border: '1px solid var(--border-color)'
                            }}>
                                <div style={{ fontWeight: '600', marginBottom: '0.3rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{cleanFilename(file.filename)}</div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                    {(file.size / 1024).toFixed(1)} KB • {file.status}
                                </div>
                            </div>
                        ))
                    ) : (
                        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem' }}>No documents indexed.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FileUploader;
