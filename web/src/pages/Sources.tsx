import { useEffect, useState } from 'react';
import { getStats, getHealth, SOURCES } from '../api';

export default function Sources() {
  const [stats, setStats] = useState<{ collection: string; total_chunks: number } | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => setStats(null));
    getHealth().then(() => setHealthy(true)).catch(() => setHealthy(false));
  }, []);

  return (
    <div className="sources-page">
      <div className="sources-header">
        <h1>Sources</h1>
        <p>Your indexed data at a glance</p>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-value">{stats?.total_chunks ?? '—'}</div>
          <div className="stat-label">Total Chunks Indexed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.collection ?? '—'}</div>
          <div className="stat-label">Collection</div>
        </div>
        <div className="stat-card">
          <div className={`stat-value ${healthy === true ? 'healthy' : healthy === false ? 'unhealthy' : ''}`}>
            {healthy === null ? '...' : healthy ? '● Online' : '● Offline'}
          </div>
          <div className="stat-label">Backend Status</div>
        </div>
      </div>

      <h2 className="sources-subtitle">Connected Sources</h2>
      <div className="sources-grid">
        {SOURCES.map((s) => (
          <div key={s.key} className="source-card" style={{ borderColor: s.color + '44' }}>
            <div className="source-icon" style={{ background: s.color + '22' }}>
              <span className="material-symbols-rounded">{s.icon}</span>
            </div>
            <div className="source-info">
              <h3>{s.label}</h3>
              <span className="source-key">{s.key}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
