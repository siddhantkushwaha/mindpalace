import { useState } from 'react';
import { postSearch, getSourceInfo, formatDate, SOURCES } from '../api';
import type { SearchResultItem } from '../api';

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const doSearch = async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await postSearch({ query: q, top_k: 10, source_filter: sourceFilter });
      setResults(res.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') doSearch();
  };

  return (
    <div className="search-page">
      <div className="search-header">
        <h1>Search</h1>
        <p>Search your personal data directly</p>
      </div>

      <div className="search-bar-area">
        <div className="search-input-wrapper">
          <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search your data..."
          />
          <button className="search-btn" onClick={doSearch} disabled={!query.trim() || loading}>
            {loading ? '...' : 'Search'}
          </button>
        </div>
        <div className="source-chips">
          <button
            className={`source-chip ${!sourceFilter ? 'active' : ''}`}
            onClick={() => setSourceFilter(null)}
          >
            All
          </button>
          {SOURCES.map((s) => (
            <button
              key={s.key}
              className={`source-chip ${sourceFilter === s.key ? 'active' : ''}`}
              style={sourceFilter === s.key ? { background: s.color + '33', borderColor: s.color } : {}}
              onClick={() => setSourceFilter(s.key)}
            >
              <span className="material-symbols-rounded mi">{s.icon}</span> {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="search-results">
        {loading && <div className="loading-spinner">Searching...</div>}
        {!loading && searched && results.length === 0 && (
          <div className="no-results">No results found</div>
        )}
        {results.map((r) => {
          const src = getSourceInfo(r.metadata.source);
          const isExpanded = expanded === r.id;
          return (
            <div
              key={r.id}
              className={`result-card ${isExpanded ? 'expanded' : ''}`}
              onClick={() => setExpanded(isExpanded ? null : r.id)}
            >
              <div className="result-header">
                <span className="result-source-badge" style={{ background: src.color + '22', color: src.color }}>
                  <span className="material-symbols-rounded mi">{src.icon}</span> {src.label}
                </span>
                <span className="result-date">{formatDate(r.metadata.created_at)}</span>
              </div>
              <h3 className="result-title">{r.metadata.title || 'Untitled'}</h3>
              <p className="result-preview">
                {isExpanded ? r.content : r.content.slice(0, 200) + (r.content.length > 200 ? '...' : '')}
              </p>
              {r.metadata.url && (
                <a
                  className="result-link"
                  href={r.metadata.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                >
                  Open source →
                </a>
              )}
              <div className="result-meta">
                <span className="result-type">{r.metadata.content_type}</span>
                {r.metadata.total_chunks > 1 && (
                  <span className="result-chunk">
                    Chunk {r.metadata.chunk_index + 1}/{r.metadata.total_chunks}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
