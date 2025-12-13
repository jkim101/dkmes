import React, { useState } from 'react';
import { MessageSquare, Search } from 'lucide-react';
import '../App.css';
import TraceInspector from './TraceInspector';

interface Message {
    role: 'user' | 'agent';
    content: string;
    context?: string[];
    strategy?: string;
    timestamp?: number;
    traceId?: string;
    reasoningTrace?: string;
    toolCalls?: Array<{
        name: string;
        arguments: Record<string, any>;
        result: any;
        execution_time_ms: number;
    }>;
}

const Playground: React.FC = () => {
    const [strategy, setStrategy] = useState<string>('Hybrid');
    const [agentMode, setAgentMode] = useState<boolean>(false);
    const [fusionMode, setFusionMode] = useState<boolean>(false);

    // Interactive State
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const [expandedContext, setExpandedContext] = useState<number | null>(null);
    const [expandedTools, setExpandedTools] = useState<number | null>(null);
    const [activeTraceId, setActiveTraceId] = useState<string | null>(null);

    const handleSend = async () => {
        if (!query.trim()) return;

        const userMsg = query;
        setMessages(prev => [...prev, { role: 'user', content: userMsg, timestamp: Date.now() }]);
        setQuery('');
        setLoading(true);

        try {
            if (fusionMode) {
                // Use Fusion endpoint - combines local + peer knowledge
                const response = await fetch('/api/v1/chat/fused', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: userMsg,
                        use_local: true,
                        use_peers: true,
                        peer_domains: ['artificial-intelligence', 'machine-learning']
                    }),
                });
                const data = await response.json();

                setMessages(prev => [...prev, {
                    role: 'agent',
                    content: data.answer,
                    context: data.sources?.map((s: any) =>
                        `[${s.type === 'local' ? 'Local' : 'Peer'}] ${s.excerpt}`
                    ),
                    strategy: `Fusion (${data.peers_used?.length || 0} peers)`,
                    timestamp: Date.now(),
                    traceId: data.trace_id
                }]);

                if (data.trace_id) {
                    setActiveTraceId(data.trace_id);
                }
            } else if (agentMode) {
                // Use Agent endpoint with tool calling
                const response = await fetch('/api/v1/agent/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: userMsg,
                        use_tools: true,
                        history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
                    }),
                });
                const data = await response.json();

                setMessages(prev => [...prev, {
                    role: 'agent',
                    content: data.answer,
                    toolCalls: data.tool_calls,
                    reasoningTrace: data.reasoning_trace,
                    timestamp: Date.now(),
                    traceId: data.trace_id
                }]);

                if (data.trace_id) {
                    setActiveTraceId(data.trace_id);
                }
            } else {
                // Use regular RAG endpoint
                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: userMsg, strategy }),
                });
                const data = await response.json();

                setMessages(prev => [...prev, {
                    role: 'agent',
                    content: data.answer,
                    context: data.context,
                    strategy: data.strategy,
                    timestamp: Date.now(),
                    traceId: data.trace_id
                }]);

                if (data.trace_id) {
                    setActiveTraceId(data.trace_id);
                }
            }
        } catch (error) {
            setMessages(prev => [...prev, { role: 'agent', content: "Error: Failed to get response." }]);
        } finally {
            setLoading(false);
        }
    };

    const toggleContext = (idx: number) => {
        setExpandedContext(expandedContext === idx ? null : idx);
    };

    const toggleTools = (idx: number) => {
        setExpandedTools(expandedTools === idx ? null : idx);
    };

    return (
        <div className="playground-container fade-in" style={{ height: '100%', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>

            {/* Left Column: Interactive Session */}
            <div className="interactive-session card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '0' }}>
                <div className="card-header" style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <MessageSquare size={16} />
                        <span style={{ fontSize: '0.95rem', fontWeight: '600' }}>Interactive Session</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        {/* Fusion Mode Toggle */}
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <span style={{ color: fusionMode ? '#10b981' : 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: fusionMode ? '600' : '400' }}>Fusion</span>
                            <input
                                type="checkbox"
                                checked={fusionMode}
                                onChange={(e) => { setFusionMode(e.target.checked); if (e.target.checked) setAgentMode(false); }}
                                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                            />
                        </label>
                        {/* Agent Mode Toggle */}
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <span style={{ color: agentMode ? '#10b981' : 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: agentMode ? '600' : '400' }}>Agent</span>
                            <input
                                type="checkbox"
                                checked={agentMode}
                                onChange={(e) => { setAgentMode(e.target.checked); if (e.target.checked) setFusionMode(false); }}
                                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                            />
                        </label>

                        {/* RAG Strategy (only shown when not in Agent mode) */}
                        {!agentMode && !fusionMode && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>RAG:</span>
                                <select
                                    value={strategy}
                                    onChange={(e) => setStrategy(e.target.value)}
                                    className="styled-select"
                                    style={{ padding: '0.3rem', borderRadius: '6px', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                                >
                                    <option value="Vector">Vector</option>
                                    <option value="Graph">Graph</option>
                                    <option value="Hybrid">Hybrid</option>
                                </select>
                            </div>
                        )}
                    </div>
                </div>

                <div className="chat-window" style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', background: 'var(--bg-secondary)' }}>
                    {messages.length === 0 && (
                        <div className="no-data" style={{ textAlign: 'center', marginTop: '20%' }}>
                            <div className="message-bubble agent" style={{ display: 'inline-block', textAlign: 'left', maxWidth: '80%' }}>
                                {strategy === 'Vector' && "Hello! I am your Vector RAG assistant. I use semantic similarity to find relevant documents. Fast and efficient!"}
                                {strategy === 'Graph' && "Hello! I am your Graph RAG assistant. I traverse the knowledge graph to find connected entities and relationships. Great for complex queries!"}
                                {strategy === 'Hybrid' && "Hello! I am your Hybrid RAG assistant. I combine vector similarity and knowledge graph traversal for comprehensive retrieval. Configure my behavior in Settings, or just ask away!"}
                            </div>
                        </div>
                    )}
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message-wrapper ${msg.role}`} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                            {msg.role === 'agent' && (
                                <div style={{ marginBottom: '0.3rem', marginLeft: '0.5rem' }}>🤖</div>
                            )}
                            <div
                                className={`message-bubble`}
                                onClick={() => msg.traceId && setActiveTraceId(msg.traceId)}
                                style={{
                                    background: msg.role === 'user' ? 'var(--accent-color)' : 'var(--card-bg)',
                                    padding: '1rem 1.5rem',
                                    borderRadius: '12px',
                                    maxWidth: '90%',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                                    position: 'relative',
                                    border: msg.role === 'agent' ? '1px solid var(--border-color)' : 'none',
                                    cursor: msg.traceId ? 'pointer' : 'default',
                                    borderLeft: msg.traceId === activeTraceId ? '4px solid var(--accent-color)' : (msg.role === 'agent' ? '1px solid var(--border-color)' : 'none')
                                }}
                            >
                                <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{msg.content}</div>

                                {msg.strategy && (
                                    <div style={{ marginTop: '0.8rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                        Strategy: {msg.strategy}
                                    </div>
                                )}

                                {/* Reasoning Trace for Agent Mode */}
                                {msg.reasoningTrace && (
                                    <div style={{
                                        marginTop: '0.8rem',
                                        fontSize: '0.75rem',
                                        color: '#6366f1',
                                        background: 'rgba(99, 102, 241, 0.1)',
                                        padding: '0.5rem',
                                        borderRadius: '4px',
                                        fontFamily: 'monospace'
                                    }}>
                                        🧠 {msg.reasoningTrace}
                                    </div>
                                )}

                                {/* Tool Calls Display for Agent Mode */}
                                {msg.toolCalls && msg.toolCalls.length > 0 && (
                                    <div style={{ marginTop: '1rem' }}>
                                        <div
                                            onClick={() => toggleTools(idx)}
                                            style={{ fontSize: '0.8rem', color: 'var(--accent-color)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                                        >
                                            {expandedTools === idx ? '▼' : '▶'} Tool Calls ({msg.toolCalls.length})
                                        </div>
                                        {expandedTools === idx && (
                                            <div style={{ marginTop: '0.5rem', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8rem' }}>
                                                {msg.toolCalls.map((tool, toolIdx) => (
                                                    <div key={toolIdx} style={{ marginBottom: '0.5rem', paddingBottom: '0.5rem', borderBottom: toolIdx < msg.toolCalls!.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                                                        <div style={{ fontWeight: '600', color: '#f59e0b' }}>🔧 {tool.name}</div>
                                                        <div style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                                            Args: {JSON.stringify(tool.arguments)}
                                                        </div>
                                                        <div style={{ color: '#10b981', marginTop: '0.25rem' }}>
                                                            Result: {typeof tool.result === 'string' ? tool.result : JSON.stringify(tool.result)}
                                                        </div>
                                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>
                                                            ⏱️ {tool.execution_time_ms.toFixed(0)}ms
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Context Chunks */}
                                {msg.context && msg.context.length > 0 && (
                                    <div style={{ marginTop: '1rem' }}>
                                        <div
                                            onClick={() => toggleContext(idx)}
                                            style={{ fontSize: '0.8rem', color: 'var(--accent-color)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                                        >
                                            {expandedContext === idx ? '▼ Hide Context' : '▶ Show Context'} ({msg.context.length} chunks)
                                        </div>
                                        {expandedContext === idx && (
                                            <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                                {msg.context.map((chunk, chunkIdx) => (
                                                    <div key={chunkIdx} style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8rem', borderLeft: '3px solid var(--accent-color)' }}>
                                                        {chunk}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="loading-indicator" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                            <div className="dot-pulse"></div>
                            <span>Thinking...</span>
                        </div>
                    )}
                </div>

                <div className="chat-input-area" style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', background: 'var(--card-bg)' }}>
                    <div style={{ position: 'relative' }}>
                        <input
                            type="text"
                            className="styled-input"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && !loading && handleSend()}
                            placeholder="Ask a question..."
                            disabled={loading}
                            style={{ width: '100%', paddingRight: '3rem' }}
                        />
                        <button
                            className="icon-btn"
                            onClick={handleSend}
                            disabled={loading}
                            style={{ position: 'absolute', right: '0.5rem', top: '50%', transform: 'translateY(-50%)', background: 'var(--accent-color)', color: 'white', borderRadius: '6px', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: 'none', cursor: 'pointer' }}
                        >
                            ➤
                        </button>
                    </div>
                </div>
            </div>

            {/* Right Column: Inspector Session */}
            <div className="inspector-session card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '0' }}>
                <div className="card-header" style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Search size={16} />
                    <span style={{ fontSize: '0.95rem', fontWeight: '600' }}>Inspector</span>
                </div>
                <div style={{ flex: 1, overflow: 'hidden' }}>
                    <TraceInspector activeTraceId={activeTraceId} compact={true} />
                </div>
            </div>
        </div>
    );
};

export default Playground;
