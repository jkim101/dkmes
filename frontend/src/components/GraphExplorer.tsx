import React, { useEffect, useState } from 'react';
import GraphVisualizer from './GraphVisualizer';
import '../App.css';

const GraphExplorer: React.FC = () => {
    // In a real app, this would fetch the entire graph or a large subgraph.
    // For this demo, we'll simulate a "full graph" by searching for common terms or just showing the last result.
    // Since we don't have a "get all nodes" API yet, we will use a placeholder or a broad search.

    const [data, setData] = useState<any>({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);

    const [selectedNode, setSelectedNode] = useState<any>(null);
    const [editForm, setEditForm] = useState({ label: '', group: '' });

    useEffect(() => {
        fetchGraph();
    }, []);

    const fetchGraph = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/v1/graph/visualize');
            if (response.ok) {
                const result = await response.json();
                setData(result);
            }
        } catch (error) {
            console.error("Failed to fetch graph", error);
        } finally {
            setLoading(false);
        }
    };

    const handleNodeClick = (node: any) => {
        setSelectedNode(node);
        setEditForm({ label: node.label || '', group: node.group || '' });
    };

    const handleUpdate = async () => {
        if (!selectedNode) return;
        try {
            const response = await fetch(`/api/v1/graph/nodes/${selectedNode.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ properties: { name: editForm.label } }) // Assuming 'name' is the property key
            });
            if (response.ok) {
                alert('Node updated successfully');
                setSelectedNode(null);
                fetchGraph();
            } else {
                alert('Failed to update node');
            }
        } catch (error) {
            console.error("Error updating node", error);
        }
    };

    const handleDelete = async () => {
        if (!selectedNode) return;
        if (!confirm('Are you sure you want to delete this node?')) return;
        try {
            const response = await fetch(`/api/v1/graph/nodes/${selectedNode.id}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                alert('Node deleted successfully');
                setSelectedNode(null);
                fetchGraph();
            } else {
                alert('Failed to delete node');
            }
        } catch (error) {
            console.error("Error deleting node", error);
        }
    };

    return (
        <div className="graph-explorer-container fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
            <div className="toolbar" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3>Graph Explorer</h3>
                <button className="primary-btn" onClick={fetchGraph} disabled={loading}>
                    {loading ? 'Loading...' : 'Refresh Graph'}
                </button>
            </div>
            <div style={{ flex: 1, border: '1px solid var(--border-color)', borderRadius: '12px', overflow: 'hidden', position: 'relative' }}>
                {data.nodes.length > 0 ? (
                    <GraphVisualizer data={data} onNodeClick={handleNodeClick} />
                ) : (
                    <div className="no-data" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                        {loading ? 'Loading Graph Data...' : 'No Graph Data Available'}
                    </div>
                )}
            </div>

            {/* Edit Panel */}
            {selectedNode && (
                <div className="edit-panel" style={{
                    position: 'absolute',
                    top: '60px',
                    right: '20px',
                    width: '300px',
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '1rem',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                    zIndex: 10
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <h4>Edit Node</h4>
                        <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>✕</button>
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Label (Name)</label>
                        <input
                            type="text"
                            value={editForm.label}
                            onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                        />
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Group (Type)</label>
                        <input
                            type="text"
                            value={editForm.group}
                            disabled
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-secondary)', cursor: 'not-allowed' }}
                        />
                    </div>

                    <div className="actions" style={{ display: 'flex', gap: '0.5rem' }}>
                        <button onClick={handleUpdate} className="primary-btn" style={{ flex: 1 }}>Save</button>
                        <button onClick={handleDelete} className="secondary-btn" style={{ flex: 1, borderColor: '#ef4444', color: '#ef4444' }}>Delete</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GraphExplorer;
