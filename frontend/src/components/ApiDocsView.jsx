import React from 'react';
import { BookOpen, ExternalLink, ShieldAlert, Code2 } from 'lucide-react';

export default function ApiDocsView() {
  return (
    <div>
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '12px' }}>FastAPI Swagger & ReDoc Specs</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '20px' }}>
          Interactive OpenAPI 3.0 specification documents for EMR integration developers:
        </p>

        <div style={{ display: 'flex', gap: '16px' }}>
          <a 
            href="http://127.0.0.1:8000/docs" 
            target="_blank" 
            rel="noreferrer"
            className="btn"
            style={{ textDecoration: 'none' }}
          >
            <ExternalLink size={16} />
            Open Swagger UI (/docs)
          </a>
          <a 
            href="http://127.0.0.1:8000/redoc" 
            target="_blank" 
            rel="noreferrer"
            className="btn btn-secondary"
            style={{ textDecoration: 'none' }}
          >
            <ExternalLink size={16} />
            Open ReDoc (/redoc)
          </a>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>REST Endpoints Summary</h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-glow)', color: 'var(--text-muted)', textAlign: 'left' }}>
              <th style={{ padding: '12px' }}>Method</th>
              <th style={{ padding: '12px' }}>Path</th>
              <th style={{ padding: '12px' }}>Required Scope</th>
              <th style={{ padding: '12px' }}>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <td style={{ padding: '12px' }}><span className="badge badge-high">POST</span></td>
              <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>/api/auth/dev-token</td>
              <td style={{ padding: '12px' }}><span className="tag">Public</span></td>
              <td style={{ padding: '12px' }}>Mint JWT access token for testing</td>
            </tr>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <td style={{ padding: '12px' }}><span className="badge badge-low">GET</span></td>
              <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>/api/namaste/concepts</td>
              <td style={{ padding: '12px' }}><span className="tag tag-anatomy">terminology:read</span></td>
              <td style={{ padding: '12px' }}>List NAMASTE concept catalog</td>
            </tr>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <td style={{ padding: '12px' }}><span className="badge badge-low">GET</span></td>
              <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>/api/namaste/concept/{'{code}'}/mapping</td>
              <td style={{ padding: '12px' }}><span className="tag tag-symptom">mapping:read</span></td>
              <td style={{ padding: '12px' }}>Execute safe candidate mapping engine</td>
            </tr>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <td style={{ padding: '12px' }}><span className="badge badge-high">POST</span></td>
              <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>/fhir/$translate</td>
              <td style={{ padding: '12px' }}><span className="tag">fhir:translate</span></td>
              <td style={{ padding: '12px' }}>Standard FHIR ConceptMap $translate operation</td>
            </tr>
            <tr>
              <td style={{ padding: '12px' }}><span className="badge badge-low">GET</span></td>
              <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>/api/audit/logs</td>
              <td style={{ padding: '12px' }}><span className="tag">audit:read</span></td>
              <td style={{ padding: '12px' }}>Retrieve audit trail logs</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
