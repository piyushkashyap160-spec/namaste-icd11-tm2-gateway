import React, { useState } from 'react';
import { translateFhir } from '../services/api';
import { FileCode2, Play, CheckCircle2, AlertCircle } from 'lucide-react';

const SAMPLES = {
  sat8: {
    resourceType: "Parameters",
    parameter: [
      {
        name: "code",
        valueCoding: {
          system: "http://namaste.gov.in/sat-d",
          code: "SAT-D.8",
          display: "aMsadAhaH"
        }
      }
    ]
  },
  sat51: {
    resourceType: "Parameters",
    parameter: [
      {
        name: "code",
        valueCoding: {
          system: "http://namaste.gov.in/sat-d",
          code: "SAT-D.51",
          display: "akasmAt SithilamalapravRuttiH"
        }
      }
    ]
  },
  sat12: {
    resourceType: "Parameters",
    parameter: [
      {
        name: "code",
        valueCoding: {
          system: "http://namaste.gov.in/sat-d",
          code: "SAT-D.12",
          display: "netrarogaH"
        }
      }
    ]
  }
};

export default function FhirTesterView() {
  const [jsonInput, setJsonInput] = useState(JSON.stringify(SAMPLES.sat8, null, 2));
  const [jsonOutput, setJsonOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTest = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsed = JSON.parse(jsonInput);
      const res = await translateFhir(parsed);
      setJsonOutput(res);
    } catch (err) {
      setError(err.message);
      setJsonOutput(null);
    } finally {
      setLoading(false);
    }
  };

  const loadSample = (sampleKey) => {
    setJsonInput(JSON.stringify(SAMPLES[sampleKey], null, 2));
  };

  return (
    <div>
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 600 }}>Load Sample Request:</span>
        <button className="btn btn-secondary" onClick={() => loadSample('sat8')}>SAT-D.8 (Shoulder Burning)</button>
        <button className="btn btn-secondary" onClick={() => loadSample('sat51')}>SAT-D.51 (Loose Stools)</button>
        <button className="btn btn-secondary" onClick={() => loadSample('sat12')}>SAT-D.12 (Eye Diseases)</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Request Panel */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>FHIR Request Payload (POST /fhir/$translate)</h3>
            <button className="btn" onClick={handleTest} disabled={loading}>
              <Play size={14} />
              {loading ? 'Executing...' : 'Execute'}
            </button>
          </div>
          <textarea
            style={{
              width: '100%',
              height: '380px',
              background: 'rgba(10, 14, 23, 0.9)',
              border: '1px solid var(--border-glow)',
              borderRadius: '12px',
              padding: '16px',
              color: '#a5f3fc',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              resize: 'none'
            }}
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
          />
        </div>

        {/* Response Panel */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>FHIR Response Parameters</h3>
          {error && (
            <div style={{ color: 'var(--accent-rose)', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
          {jsonOutput ? (
            <pre style={{ height: '380px' }}>{JSON.stringify(jsonOutput, null, 2)}</pre>
          ) : !error && (
            <div style={{ color: 'var(--text-dim)', textAlign: 'center', marginTop: '140px' }}>
              Click 'Execute' to submit FHIR $translate operation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
