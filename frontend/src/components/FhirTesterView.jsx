import React, { useState } from 'react';
import { translateFhir } from '../services/api';

const SAMPLE_PAYLOAD = {
  resourceType: 'Parameters',
  parameter: [
    {
      name: 'code',
      valueCoding: {
        system: 'http://namaste.gov.in/sat-d',
        code: 'SAT-D.8',
        display: 'aMsadAhaH',
      },
    },
  ],
};

export default function FhirTesterView() {
  const [payload, setPayload] = useState(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [parseError, setParseError] = useState(null);

  const handleSubmit = async () => {
    setError(null);
    setParseError(null);
    let parsed;
    try {
      parsed = JSON.parse(payload);
    } catch {
      setParseError('Invalid JSON payload');
      return;
    }

    setLoading(true);
    try {
      const data = await translateFhir(parsed);
      setResponse(data);
    } catch (err) {
      setError(err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (code, display) => {
    const preset = {
      resourceType: 'Parameters',
      parameter: [
        {
          name: 'code',
          valueCoding: {
            system: 'http://namaste.gov.in/sat-d',
            code,
            display,
          },
        },
      ],
    };
    setPayload(JSON.stringify(preset, null, 2));
    setResponse(null);
    setError(null);
  };

  const PRESETS = [
    { code: 'SAT-D.8', display: 'aMsadAhaH', label: 'Shoulder burn' },
    { code: 'SAT-D.51', display: 'akasmAt SithilamalapravRuttiH', label: 'Loose stools' },
    { code: 'SAT-D.12', display: 'netrarogaH', label: 'Eye disease' },
    { code: 'SAT-D.99', display: 'aMsa mathana vat vyathA', label: 'No candidate' },
  ];

  const matched = response?.parameter?.[0]?.valueBoolean;

  return (
    <div>
      <div className="disclaimer-banner">
        <span style={{ fontSize: 16, flexShrink: 0 }}>ℹ</span>
        <div>
          Send a <strong>FHIR R4 Parameters</strong> resource with a NAMASTE SAT-D coding.
          The gateway returns a <strong>$translate</strong> response with match result and candidate TM2 coding.
        </div>
      </div>

      {/* Presets */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 18, flexWrap: 'wrap' }}>
        {PRESETS.map(p => (
          <button
            key={p.code}
            className="btn btn-secondary"
            style={{ padding: '7px 14px', fontSize: '0.8rem' }}
            onClick={() => loadPreset(p.code, p.display)}
          >
            {p.code} — {p.label}
          </button>
        ))}
      </div>

      <div className="fhir-layout">
        {/* Request Panel */}
        <div>
          <div className="glass-panel" style={{ padding: '20px 22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div>
                <div className="section-title">POST /fhir/$translate</div>
                <div className="section-subtitle">FHIR R4 Parameters resource</div>
              </div>
              <span className="method-badge method-post">POST</span>
            </div>

            {parseError && (
              <div style={{ padding: '10px 14px', background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.25)', borderRadius: 8, marginBottom: 12, color: 'var(--rose)', fontSize: '0.8rem' }}>
                ⚠ {parseError}
              </div>
            )}

            <textarea
              id="fhir-payload-input"
              value={payload}
              onChange={e => setPayload(e.target.value)}
              style={{
                width: '100%',
                minHeight: '280px',
                background: 'var(--bg-code)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 10,
                padding: '14px 16px',
                color: '#a5f3fc',
                fontFamily: 'var(--mono)',
                fontSize: '0.82rem',
                lineHeight: 1.6,
                resize: 'vertical',
                outline: 'none',
              }}
              onFocus={e => { e.target.style.borderColor = 'var(--cyan)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border-subtle)'; }}
            />

            <button
              id="fhir-send-btn"
              className="btn"
              style={{ marginTop: 14, width: '100%', justifyContent: 'center' }}
              onClick={handleSubmit}
              disabled={loading}
            >
              <span>⬡</span>
              {loading ? 'Translating…' : 'Send $translate Request'}
            </button>
          </div>
        </div>

        {/* Response Panel */}
        <div>
          <div className="glass-panel" style={{ padding: '20px 22px', minHeight: '200px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <div className="section-title">Response</div>
                <div className="section-subtitle">FHIR Parameters · JSON</div>
              </div>
              {response && (
                <span className={matched ? 'badge badge-high' : 'badge badge-none'}>
                  {matched ? '✓ MATCH' : '✗ NO MATCH'}
                </span>
              )}
            </div>

            {error && (
              <div style={{ padding: '14px', background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.25)', borderRadius: 10, color: 'var(--rose)', fontSize: '0.875rem' }}>
                ⚠ {error}
              </div>
            )}

            {loading && (
              <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
                <div className="spinner" style={{ width: 24, height: 24, margin: '0 auto 10px auto' }} />
                Processing FHIR translation…
              </div>
            )}

            {response && !loading && (
              <pre>{JSON.stringify(response, null, 2)}</pre>
            )}

            {!response && !loading && !error && (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
                Send a request to see the FHIR response
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
