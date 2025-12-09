import { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  source?: string;
  timestamp: Date;
}

type TargetAgent = 'alpha' | 'local';

const GAMMA_URL = '';  // Use relative URLs (proxied by Vite in dev)
const ALPHA_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hi! I'm the Data Analytics Agent. Ask me anything and I'll forward your question to DKMES Alpha's knowledge base for answers.",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [target, setTarget] = useState<TargetAgent>('alpha');
  const [alphaStatus, setAlphaStatus] = useState<'online' | 'offline'>('offline');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkAlphaStatus();
    const interval = setInterval(checkAlphaStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkAlphaStatus = async () => {
    try {
      const res = await fetch(`${ALPHA_URL}/health`);
      setAlphaStatus(res.ok ? 'online' : 'offline');
    } catch {
      setAlphaStatus('offline');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      let response, data, source;

      if (target === 'alpha') {
        response = await fetch(`${GAMMA_URL}/api/v1/ask-alpha`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: input })
        });
        data = await response.json();
        source = 'DKMES Alpha';
      } else {
        response = await fetch(`${GAMMA_URL}/api/v1/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: input })
        });
        data = await response.json();
        source = 'Agent Gamma';
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.answer || data.error || 'No response received',
        isUser: false,
        source,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Data Analytics Agent</h1>
        <p>Knowledge-powered chatbot connected to DKMES Alpha</p>
      </header>

      <div className="status-bar">
        <div className="status-item">
          <div className="status-dot online"></div>
          <span>Gamma :8002</span>
        </div>
        <div className="status-item">
          <div className={`status-dot ${alphaStatus}`}></div>
          <span>Alpha :8000</span>
        </div>
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.isUser ? 'user' : 'assistant'}`}>
              <div className="message-content">{msg.content}</div>
              {msg.source && (
                <div className="message-source">
                  <span className="source-tag">{msg.source}</span>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-content loading">Thinking...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div className="target-selector">
            <button
              className={`target-btn ${target === 'alpha' ? 'active' : ''}`}
              onClick={() => setTarget('alpha')}
            >
              🎯 Ask DKMES Alpha
            </button>
            <button
              className={`target-btn ${target === 'local' ? 'active' : ''}`}
              onClick={() => setTarget('local')}
            >
              💬 Agent Gamma Local
            </button>
          </div>
          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              disabled={isLoading}
            />
            <button onClick={sendMessage} disabled={isLoading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
