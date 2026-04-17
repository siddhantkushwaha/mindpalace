import { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { createChatWebSocket, SOURCES, getChatSession } from '../api';
import type { ChatMessage } from '../api';

interface ChatProps {
  sessionId: string | null;
  onSessionCreated: (id: string, title: string) => void;
}

export default function Chat({ sessionId, onSessionCreated }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [thinkingText, setThinkingText] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const assistantBuffer = useRef('');
  const thinkingBuffer = useRef('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const currentSessionId = useRef<string | null>(sessionId);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load session messages when sessionId changes
  useEffect(() => {
    currentSessionId.current = sessionId;
    if (sessionId) {
      // Don't reload from DB if we're actively streaming — we already have the messages in state
      if (streaming) return;
      getChatSession(sessionId)
        .then((session) => {
          setMessages(session.messages.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content })));
          setSourceFilter(session.source_filter);
        })
        .catch(() => {
          setMessages([]);
        });
    } else {
      setMessages([]);
      setSourceFilter(null);
    }
    inputRef.current?.focus();
  }, [sessionId]);

  const connectWs = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) return wsRef.current;
    const ws = createChatWebSocket();
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'session_id') {
        currentSessionId.current = data.session_id;
        // Notify parent about new session
        onSessionCreated(data.session_id, '');
      } else if (data.type === 'thinking') {
        setThinking(true);
        thinkingBuffer.current += data.content;
        setThinkingText(thinkingBuffer.current);
      } else if (data.type === 'token') {
        setThinking(false);
        assistantBuffer.current += data.content;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: assistantBuffer.current };
          }
          return updated;
        });
      } else if (data.type === 'error') {
        setThinking(false);
        setStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: '', error: true };
          }
          return updated;
        });
      } else if (data.type === 'done') {
        setThinking(false);
        setStreaming(false);
      }
    };

    ws.onerror = () => {
      setStreaming(false);
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return ws;
  }, [onSessionCreated]);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || streaming) return;

    const userMsg: ChatMessage = { role: 'user', content: text };
    const history = [...messages];
    setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: '' }]);
    setInput('');
    setStreaming(true);
    setThinking(false);
    setThinkingText('');
    assistantBuffer.current = '';
    thinkingBuffer.current = '';

    const send = (ws: WebSocket) => {
      ws.send(
        JSON.stringify({
          message: text,
          chat_history: history,
          source_filter: sourceFilter,
          session_id: currentSessionId.current,
        })
      );
    };

    const ws = connectWs();
    if (ws.readyState === WebSocket.OPEN) {
      send(ws);
    } else {
      ws.onopen = () => send(ws);
    }
  }, [input, streaming, messages, sourceFilter, connectWs]);

  const retryLastMessage = useCallback(() => {
    // Find the last user message
    const lastUserIdx = messages.findLastIndex((m) => m.role === 'user');
    if (lastUserIdx === -1 || streaming) return;
    const text = messages[lastUserIdx].content;
    const history = messages.slice(0, lastUserIdx);

    // Replace the error assistant message with a fresh empty one
    setMessages((prev) => {
      const updated = prev.slice(0, lastUserIdx + 1);
      updated.push({ role: 'assistant', content: '' });
      return updated;
    });
    setStreaming(true);
    setThinking(false);
    setThinkingText('');
    assistantBuffer.current = '';
    thinkingBuffer.current = '';

    const send = (ws: WebSocket) => {
      ws.send(
        JSON.stringify({
          message: text,
          chat_history: history,
          source_filter: sourceFilter,
          session_id: currentSessionId.current,
        })
      );
    };

    const ws = connectWs();
    if (ws.readyState === WebSocket.OPEN) {
      send(ws);
    } else {
      ws.onopen = () => send(ws);
    }
  }, [messages, streaming, sourceFilter, connectWs]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const activeSource = SOURCES.find((s) => s.key === sourceFilter);

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="chat-header-spacer" />
        <div className="filter-area">
          <button
            className={`filter-toggle ${sourceFilter ? 'active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
          >
            {activeSource ? <><span className="material-symbols-rounded mi">{activeSource.icon}</span> {activeSource.label}</> : <><span className="material-symbols-rounded mi">search</span> All Sources</>}
          </button>
          {showFilters && (
            <div className="filter-dropdown">
              <button
                className={`filter-option ${!sourceFilter ? 'selected' : ''}`}
                onClick={() => { setSourceFilter(null); setShowFilters(false); }}
              >
                <span className="material-symbols-rounded mi">search</span> All Sources
              </button>
              {SOURCES.map((s) => (
                <button
                  key={s.key}
                  className={`filter-option ${sourceFilter === s.key ? 'selected' : ''}`}
                  onClick={() => { setSourceFilter(s.key); setShowFilters(false); }}
                >
                  <span className="material-symbols-rounded mi">{s.icon}</span> {s.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h2>MindPalace</h2>
            <p>Ask anything about your personal data</p>
            <div className="suggestion-chips">
              {['What\'s in my latest email?', 'Summarize my notes', 'Find my bookmarks about React'].map((s) => (
                <button key={s} className="suggestion-chip" onClick={() => { setInput(s); inputRef.current?.focus(); }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              )}
            </div>
            <div className="message-content">
              {msg.role === 'assistant' ? (
                <>
                  {/* Show thinking block: open while thinking, collapsed once content arrives */}
                  {i === messages.length - 1 && thinkingText && (
                    <details className={`thinking-block${thinking ? ' active' : ''}`} open={thinking}>
                      <summary>{thinking ? 'Thinking…' : 'Show Thinking'}</summary>
                      <div className="thinking-content">{thinkingText}</div>
                    </details>
                  )}
                  {msg.content ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  ) : msg.error ? (
                    <div className="message-error">
                      <p>Failed to generate a response.</p>
                      <button className="retry-btn" onClick={retryLastMessage}>Retry</button>
                    </div>
                  ) : (
                    !thinking && streaming && i === messages.length - 1 ? (
                      <span className="typing-indicator">
                        <span /><span /><span />
                      </span>
                    ) : null
                  )}
                </>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message MindPalace..."
            rows={1}
            disabled={streaming}
          />
          <button
            className="send-btn"
            onClick={sendMessage}
            disabled={!input.trim() || streaming}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
