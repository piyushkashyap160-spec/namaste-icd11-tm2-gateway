import React from 'react';

const ENDPOINTS = [
  { method: 'GET', path: '/health', desc: 'System health check — returns status, TM2 source, and concept counts', auth: false },
  { method: 'POST', path: '/api/auth/dev-token', desc: 'Mint a short-lived JWT dev token with requested scopes', auth: false },
  { method: 'GET', path: '/api/namaste/concepts', desc: 'List all supported AYUSH NAMASTE SAT-D concepts', auth: 'terminology:read' },
  { method: 'GET', path: '/api/namaste/concept/{code}/mapping', desc: 'Run full clinical feature extraction and ICD-11 TM2 candidate mapping for a NAMASTE code', auth: 'mapping:read' },
  { method: 'GET', path: '/api/tm2/concepts', desc: 'List all WHO ICD-11 TM2 concepts (from persistent cache or live WHO API)', auth: 'terminology:read' },
  { method: 'POST', path: '/fhir/$translate', desc: 'FHIR R4 ConceptMap $translate — accepts Parameters resource, returns matched TM2 coding with evidence', auth: 'fhir:translate' },
  { method: 'GET', path: '/api/audit/logs', desc: 'Retrieve non-PHI access audit log entries for compliance review', auth: 'audit:read' },
];

const SCOPES = [
  { scope: 'terminology:read', desc: 'Access NAMASTE and TM2 concept catalogs' },
  { scope: 'mapping:read', desc: 'Run clinical feature mapping engine' },
  { scope: 'fhir:translate', desc: 'Use FHIR $translate endpoint' },
  { scope: 'audit:read', desc: 'Access audit log trail' },
];

export default function ApiDocsView() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Auth info */}
      <div className="glass-panel" style={{ padding: '22px 24px' }}>
        <div className="section-title" style={{ marginBottom: 6 }}>Authentication</div>
        <div className="section-subtitle" style={{ marginBottom: 14 }}>
          All endpoints (except /health and /api/auth/dev-token) require a Bearer JWT token.
          Obtain a token via POST /api/auth/dev-token with the required scopes.
        </div>
        <pre style={{ fontSize: '0.78rem' }}>{`POST /api/auth/dev-token
Content-Type: application/json

{
  "subject": "dashboard-emr-user",
  "facility_id": "FAC-IN-DELHI-01",
  "scopes": ["terminology:read", "mapping:read", "fhir:translate", "audit:read"]
}

→ { "access_token": "<JWT>", "token_type": "bearer", "expires_in": 3600 }`}</pre>

        <div style={{ marginTop: 18 }}>
          <div style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: 10 }}>Available Scopes</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {SCOPES.map(s => (
              <div key={s.scope} style={{ padding: '10px 14px', background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.18)', borderRadius: 10, flex: '1 1 220px' }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--cyan)', fontWeight: 600, marginBottom: 3 }}>{s.scope}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Endpoints */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="section-title">API Endpoints</div>
          <div className="section-subtitle">OpenAPI 3.0 — FHIR R4 Compliant</div>
        </div>
        {ENDPOINTS.map((ep, i) => (
          <div key={i} className="endpoint-row">
            <span className={`method-badge ${ep.method === 'POST' ? 'method-post' : 'method-get'}`}>{ep.method}</span>
            <span className="endpoint-path">{ep.path}</span>
            <span className="endpoint-desc">{ep.desc}</span>
            {ep.auth && (
              <span style={{ marginLeft: 'auto', flexShrink: 0, fontFamily: 'var(--mono)', fontSize: '0.68rem', color: 'var(--amber)', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 5, padding: '2px 8px' }}>
                {ep.auth}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Standards reference */}
      <div className="glass-panel" style={{ padding: '22px 24px' }}>
        <div className="section-title" style={{ marginBottom: 14 }}>Standards Reference</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          {[
            { label: 'WHO ICD-11 TM2', href: 'https://icd.who.int/browse/2026-01/mms/en', desc: 'Official WHO International Classification · Module II Traditional Medicine' },
            { label: 'FHIR R4 ConceptMap', href: 'https://www.hl7.org/fhir/conceptmap.html', desc: 'HL7 FHIR R4 $translate operation specification' },
            { label: 'ABDM / NRCeS Standards', href: 'https://abdm.gov.in', desc: 'India ABDM Health Data Management Policy — EHR interoperability baseline' },
            { label: 'AYUSH NAMASTE', href: 'https://www.ayush.gov.in', desc: 'SAT-D Ayurvedic terminology standard — Ministry of AYUSH, Govt. of India' },
          ].map(ref => (
            <a
              key={ref.label}
              href={ref.href}
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.025)', border: '1px solid var(--border-subtle)', borderRadius: 10, textDecoration: 'none', display: 'block', transition: 'background 0.15s, border-color 0.15s' }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(6,182,212,0.3)'; e.currentTarget.style.background = 'rgba(6,182,212,0.05)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.background = 'rgba(255,255,255,0.025)'; }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--cyan)', marginBottom: 4 }}>{ref.label} ↗</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{ref.desc}</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
