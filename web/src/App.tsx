import { useState, useEffect, useCallback } from 'react';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Search from './pages/Search';
import Settings from './pages/Settings';
import { checkAuth, clearToken, registerPasskey, getPasskeyStatus } from './auth';
import { listChatSessions, deleteChatSession } from './api';
import type { ChatSessionSummary } from './api';

type Page = 'chat' | 'search' | 'settings';

function App() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [page, setPage] = useState<Page>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [passkeyRegistered, setPasskeyRegistered] = useState(false);
  const [registeringPasskey, setRegisteringPasskey] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [chatKey, setChatKey] = useState(0);

  useEffect(() => {
    checkAuth().then(setAuthed);
  }, []);

  useEffect(() => {
    if (authed) {
      getPasskeyStatus()
        .then((s) => setPasskeyRegistered(s.registered))
        .catch(() => {});
      refreshSessions();
    }
  }, [authed]);

  const refreshSessions = useCallback(() => {
    listChatSessions()
      .then(setChatSessions)
      .catch(() => {});
  }, []);

  const handleNewChat = () => {
    setActiveSessionId(null);
    setChatKey((k) => k + 1);
    setPage('chat');
    setSidebarOpen(false);
  };

  const handleSessionCreated = useCallback((id: string, _title: string) => {
    setActiveSessionId(id);
    // Refresh the session list after a short delay so the DB has the record
    setTimeout(refreshSessions, 500);
  }, [refreshSessions]);

  const handleLoadSession = (id: string) => {
    setActiveSessionId(id);
    setChatKey((k) => k + 1);
    setPage('chat');
    setSidebarOpen(false);
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteChatSession(id);
    if (activeSessionId === id) setActiveSessionId(null);
    setChatSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const handleLogout = () => {
    clearToken();
    setAuthed(false);
  };

  const handleRegisterPasskey = async () => {
    setRegisteringPasskey(true);
    try {
      await registerPasskey();
      setPasskeyRegistered(true);
    } catch {
      // Silently handle — user may have cancelled
    } finally {
      setRegisteringPasskey(false);
    }
  };

  // Loading state
  if (authed === null) {
    return (
      <div className="app" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: 16 }}>Loading...</span>
      </div>
    );
  }

  // Not authenticated
  if (!authed) {
    return <Login onLogin={() => setAuthed(true)} />;
  }

  return (
    <div className="app">
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-logo">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </span>
          <span className="sidebar-title">MindPalace</span>
        </div>

        <button className="new-chat-btn sidebar-new-chat" onClick={handleNewChat}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New Chat
        </button>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${page === 'search' ? 'active' : ''}`}
            onClick={() => { setPage('search'); setSidebarOpen(false); }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            Search
          </button>
          <button
            className={`nav-item ${page === 'settings' ? 'active' : ''}`}
            onClick={() => { setPage('settings'); setSidebarOpen(false); }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            Settings
          </button>
        </nav>

        {chatSessions.length > 0 && (
          <div className="chat-history-section">
            <div className="chat-history-label">Recent Chats</div>
            <div className="chat-history-list">
              {chatSessions.map((s) => (
                <div
                  key={s.id}
                  className={`chat-history-item ${activeSessionId === s.id ? 'active' : ''}`}
                  onClick={() => handleLoadSession(s.id)}
                  title={s.title}
                >
                  <span className="chat-history-title">{s.title}</span>
                  <button
                    className="chat-history-delete"
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    title="Delete chat"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          {!passkeyRegistered && (
            <button className="nav-item passkey-register" onClick={handleRegisterPasskey} disabled={registeringPasskey}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <circle cx="12" cy="16" r="1" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              {registeringPasskey ? 'Setting up...' : 'Set up Biometrics'}
            </button>
          )}
          <button className="nav-item logout-btn" onClick={handleLogout}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
        {page === 'chat' && (
          <Chat
            key={chatKey}
            sessionId={activeSessionId}
            onSessionCreated={handleSessionCreated}
          />
        )}
        {page === 'search' && <Search />}
        {page === 'settings' && <Settings />}
      </main>
    </div>
  );
}

export default App;
