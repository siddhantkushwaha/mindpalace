import { useState, useEffect } from 'react';
import { listApiKeys, createApiKey, deleteApiKey } from '../api';
import type { ApiKeyInfo } from '../api';

export default function Settings() {
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [newLabel, setNewLabel] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadKeys();
  }, []);

  const loadKeys = async () => {
    try {
      const keys = await listApiKeys();
      setApiKeys(keys);
    } catch {
      setError('Failed to load API keys');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setNewKey(null);
    try {
      const key = await createApiKey(newLabel || 'default');
      setNewKey(key.key ?? null);
      setNewLabel('');
      await loadKeys();
    } catch {
      setError('Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteApiKey(id);
      setApiKeys((prev) => prev.filter((k) => k.id !== id));
    } catch {
      setError('Failed to delete API key');
    }
  };

  const handleCopyKey = () => {
    if (newKey) navigator.clipboard.writeText(newKey);
  };

  return (
    <div className="settings-page">
      <div className="settings-container">
        <h1 className="settings-title">Settings</h1>

        <section className="settings-section">
          <h2>API Keys</h2>
          <p className="settings-desc">
            Create API keys to push data from external connectors. Each key is scoped to your account.
          </p>

          <form className="api-key-form" onSubmit={handleCreate}>
            <input
              type="text"
              placeholder="Key label (e.g. gmail-sync)"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Key'}
            </button>
          </form>

          {newKey && (
            <div className="api-key-created">
              <strong>New API key created — copy it now, it won't be shown again:</strong>
              <div className="api-key-value">
                <code>{newKey}</code>
                <button onClick={handleCopyKey} title="Copy key">📋</button>
              </div>
            </div>
          )}

          {error && <div className="settings-error">{error}</div>}

          <div className="api-key-list">
            {apiKeys.length === 0 ? (
              <p className="text-muted">No API keys yet. Create one above.</p>
            ) : (
              apiKeys.map((k) => (
                <div key={k.id} className="api-key-item">
                  <div className="api-key-info">
                    <span className="api-key-label">{k.label}</span>
                    <span className="api-key-preview">{k.key_preview}</span>
                    <span className="api-key-date">{new Date(k.created_at).toLocaleDateString()}</span>
                  </div>
                  <button className="api-key-delete" onClick={() => handleDelete(k.id)} title="Revoke key">
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
