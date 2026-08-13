import React, { useEffect, useState } from 'react';
import { fetchAuditLogs } from '../services/api';

function formatTs(ts) {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString('en-IN', { hour12: false });
  } catch {
    return ts;
  }
}

export default function AuditLogsView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAuditLogs()
      .then(data => setLogs(data))
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="disclaimer-banner">
        <span style={{ fontSize: 16, flexShrink: 0 }}>🛡</span>
        <div>
          <strong>Non-PHI Access Logs.</strong> All mapping requests are logged for EHR compliance and traceability.
          No patient data is stored. Logs record API method, endpoint, NAMASTE code accessed, and timestamp.
        </div>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="section-title">Access Audit Trail</div>
          <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
            {loading ? '…' : `${logs.length} records`}
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="spinner" style={{ width: 22, height: 22, margin: '0 auto 10px auto' }} />
            Loading audit logs…
          </div>
        ) : logs.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
            No audit log entries yet. Interact with the API to generate records.
          </div>
        ) : (
          <table className="concept-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Code</th>
                <th>Subject</th>
              </tr>
            </thead>
            <tbody>
              {[...logs].reverse().map((log, i) => (
                <tr key={log.id || i} className="audit-row">
                  <td style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--mono)', fontSize: '0.75rem' }}>{logs.length - i}</td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {formatTs(log.timestamp || log.ts)}
                  </td>
                  <td>
                    <span className={`method-badge ${log.method === 'POST' ? 'method-post' : 'method-get'}`}>
                      {log.method || 'GET'}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {log.endpoint || log.path || '—'}
                  </td>
                  <td>
                    <span className="concept-code">{log.namaste_code || log.code || '—'}</span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {log.subject || log.user || '—'}
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
