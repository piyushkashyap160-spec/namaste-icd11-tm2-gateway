import React, { useState, useEffect } from 'react';
import { fetchNamasteConcepts } from '../services/api';

export default function NamasteSearchView({ onSelectConcept }) {
  const [concepts, setConcepts] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNamasteConcepts()
      .then(data => setConcepts(data))
      .catch(() => setConcepts([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = concepts.filter(c =>
    !query ||
    c.code.toLowerCase().includes(query.toLowerCase()) ||
    (c.display || '').toLowerCase().includes(query.toLowerCase()) ||
    (c.definition || '').toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      {/* Search bar */}
      <div className="glass-panel" style={{ padding: '18px 22px', marginBottom: '22px' }}>
        <div className="input-group">
          <input
            id="namaste-search-input"
            type="text"
            className="form-input"
            placeholder="Filter by code, display, or definition…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            autoComplete="off"
          />
        </div>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="section-title">SAT-D Concept Catalog</div>
          <span className="provenance-badge provenance-local">● LOCAL DEMO</span>
          <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
            {loading ? '…' : `${filtered.length} / ${concepts.length} concepts`}
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="spinner" style={{ width: 24, height: 24, margin: '0 auto 10px auto' }} />
            Loading NAMASTE concepts…
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            No concepts match "{query}"
          </div>
        ) : (
          <table className="concept-table">
            <thead>
              <tr>
                <th>SAT-D Code</th>
                <th>Sanskrit Display</th>
                <th>Clinical Definition (English)</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.code} onClick={() => onSelectConcept(c.code)}>
                  <td><span className="concept-code">{c.code}</span></td>
                  <td style={{ fontWeight: 600, fontSize: '0.9rem' }}>{c.display}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '380px' }}>
                    {c.definition || '—'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                      onClick={e => { e.stopPropagation(); onSelectConcept(c.code); }}
                    >
                      Map →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
