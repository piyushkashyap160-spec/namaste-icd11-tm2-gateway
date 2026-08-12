import React, { useEffect, useState } from 'react';
import { fetchAuditLogs } from '../services/api';
import { ShieldCheck, RefreshCw, Clock } from 'lucide-react';

export default function AuditLogsView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div>
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={20} color="var(--accent-emerald)" />
          <span style={{ fontWeight: 700 }}>EHR Interoperability Non-PHI Audit Trail</span>
        </div>
        <button className="btn btn-secondary" onClick={loadLogs} disabled={loading}>
          <RefreshCw size={14} />
          Refresh Logs
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '24px' }}>
        {loading ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Loading audit entries...</div>
        ) : logs.length === 0 ? (
          <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '40px' }}>No audit records logged yet. Trigger mapping requests to generate audit logs.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glow)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px' }}>Timestamp</th>
                  <th style={{ padding: '12px' }}>Subject</th>
                  <th style={{ padding: '12px' }}>Facility</th>
                  <th style={{ padding: '12px' }}>Endpoint</th>
                  <th style={{ padding: '12px' }}>NAMASTE</th>
                  <th style={{ padding: '12px' }}>TM2 Candidate</th>
                  <th style={{ padding: '12px' }}>Score</th>
                  <th style={{ padding: '12px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '12px', fontWeight: 600 }}>{log.subject || 'N/A'}</td>
                    <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{log.facility_id || 'N/A'}</td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', color: 'var(--primary-cyan)' }}>{log.endpoint}</td>
                    <td style={{ padding: '12px' }}><span className="tag tag-anatomy">{log.namaste_code || '-'}</span></td>
                    <td style={{ padding: '12px' }}><span className="tag tag-symptom">{log.selected_tm2_candidate || '-'}</span></td>
                    <td style={{ padding: '12px', fontWeight: 700 }}>{log.score !== null ? log.score : '-'}</td>
                    <td style={{ padding: '12px' }}>
                      <span className={`badge ${log.result === 'CANDIDATE_MAPPING' || log.result === 'SUCCESS' ? 'badge-high' : 'badge-none'}`}>
                        {log.result}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
