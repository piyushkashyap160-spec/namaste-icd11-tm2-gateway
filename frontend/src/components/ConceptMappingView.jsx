import React, { useState, useEffect } from 'react';
import { getConceptMapping, translateFhir } from '../services/api';

const ConfidenceBadge = ({ conf }) => {
  const map = {
    HIGH: ['badge badge-high', 'HIGH'],
    MEDIUM: ['badge badge-medium', 'MEDIUM'],
    LOW: ['badge badge-low', 'LOW'],
  };
  const [cls, label] = map[conf] || ['badge badge-none', 'NONE'];
  return <span className={cls}>{label} CONFIDENCE</span>;
};

const ScoreBar = ({ score, max = 100 }) => {
  const pct = Math.min(100, (score / max) * 100);
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-label">
        <span>Clinical Match Score</span>
        <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{score}</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

export default function ConceptMappingView({ selectedCode, onCodeChange }) {
  const [inputCode, setInputCode] = useState(selectedCode || 'SAT-D.8');
  const [result, setResult] = useState(null);
  const [fhirResponse, setFhirResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runMapping = async (code) => {
    setLoading(true);
    setFhirResponse(null);
    setError(null);
    try {
      const data = await getConceptMapping(code);
      setResult(data);

      if (data.namaste) {
        const fhirData = await translateFhir({
          resourceType: 'Parameters',
          parameter: [
            {
              name: 'code',
              valueCoding: {
                system: 'http://namaste.gov.in/sat-d',
                code: data.namaste.code,
                display: data.namaste.display,
              },
            },
          ],
        });
        setFhirResponse(fhirData);
      }
    } catch (err) {
      setError(err.message || 'Mapping failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const code = selectedCode || 'SAT-D.8';
    setInputCode(code);
    runMapping(code);
  }, [selectedCode]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputCode.trim()) {
      runMapping(inputCode.trim());
      if (onCodeChange) onCodeChange(inputCode.trim());
    }
  };

  return (
    <div>
      {/* Search Bar */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '22px' }}>
        <form onSubmit={handleSubmit} className="input-group">
          <input
            id="mapping-code-input"
            type="text"
            className="form-input"
            placeholder="Enter NAMASTE SAT-D code (e.g. SAT-D.8) or clinical text…"
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value)}
            autoComplete="off"
          />
          <button id="run-mapping-btn" type="submit" className="btn" disabled={loading}>
            <span style={{ fontSize: 15 }}>⇄</span>
            {loading ? 'Evaluating…' : 'Run Mapping Engine'}
          </button>
        </form>
      </div>

      {error && (
        <div style={{ padding: '14px 18px', background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.25)', borderRadius: 12, marginBottom: 20, color: 'var(--rose)', fontSize: '0.875rem' }}>
          ⚠ {error}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
          <div className="spinner" style={{ width: 28, height: 28, margin: '0 auto 12px auto', borderWidth: 3 }} />
          <div>Running clinical feature extraction and mapping…</div>
        </div>
      )}

      {result && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

          {/* Source NAMASTE Concept */}
          <div className="glass-panel" style={{ padding: '22px 24px', borderLeft: '3px solid var(--cyan)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)' }}>
                Source · AYUSH NAMASTE
              </span>
              <span className="provenance-badge provenance-local">● LOCAL DEMO</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
              <div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--cyan)', marginBottom: 4 }}>{result.namaste.code}</div>
                <h2 style={{ fontSize: '1.3rem', fontWeight: 800, letterSpacing: '-0.015em' }}>{result.namaste.display}</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: 5 }}>
                  {result.namaste.definition}
                </p>
              </div>
            </div>
          </div>

          {/* Pipeline connector */}
          <div className="pipeline-connector">
            <div className="pipeline-pill">
              <span>↓</span>
              Deterministic Clinical Feature Extraction + Hard Rejection Evaluation
            </div>
          </div>

          {/* Mapping status note */}
          <div className="disclaimer-banner" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 16, flexShrink: 0 }}>⚠</span>
            <div>
              <strong>Mapping Status: {result.mapping_status}</strong> — {result.note}
            </div>
          </div>

          {/* Results */}
          {result.count === 0 ? (
            <div className="glass-panel no-candidate-panel">
              <div className="no-candidate-icon">
                <span style={{ fontSize: 22, color: 'var(--rose)' }}>✗</span>
              </div>
              <div className="no-candidate-title">NO_CANDIDATE</div>
              <p className="no-candidate-desc">
                No candidate concept passed clinical safety thresholds or hard rejection rules.
                The engine avoided producing a false forced mapping — clinical safety preserved.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <div className="section-title">Candidate Matches</div>
                <span className="badge badge-high" style={{ fontSize: '0.7rem' }}>{result.count} found</span>
                <span className="provenance-badge provenance-who">● OFFICIAL · WHO ICD-11 TM2</span>
              </div>

              {result.matches.map((match) => (
                <div key={match.tm2_id} className="glass-panel match-card">
                  <div className="match-card-header">
                    <div>
                      <div className="match-tm2-id">
                        TM2 · {match.tm2_code || match.tm2_id} &nbsp;|&nbsp; equiv: {match.equivalence}
                      </div>
                      <div className="match-title">{match.tm2_title}</div>
                    </div>
                    <div className="match-right">
                      <ConfidenceBadge conf={match.confidence} />
                      <div className="match-score">{match.score}</div>
                      <div className="match-score-label">score</div>
                    </div>
                  </div>

                  <ScoreBar score={match.score} />

                  <div className="evidence-panel">
                    <div className="evidence-panel-label">Clinical Evidence — Matched Features</div>
                    <div className="tag-container">
                      {(match.evidence?.anatomy || []).map(a => (
                        <span key={a} className="tag tag-anatomy">Anatomy: {a}</span>
                      ))}
                      {(match.evidence?.symptoms || []).map(s => (
                        <span key={s} className="tag tag-symptom">Symptom: {s}</span>
                      ))}
                      {(match.evidence?.quality || []).map(q => (
                        <span key={q} className="tag tag-quality">Quality: {q}</span>
                      ))}
                      {(match.evidence?.words || []).map(w => (
                        <span key={w} className="tag">Word: {w}</span>
                      ))}
                      {[...(match.evidence?.anatomy || []), ...(match.evidence?.symptoms || []), ...(match.evidence?.quality || []), ...(match.evidence?.words || [])].length === 0 && (
                        <span className="tag" style={{ color: 'var(--text-tertiary)' }}>No shared feature tokens</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* FHIR $translate Output */}
          {fhirResponse && (
            <div className="glass-panel" style={{ padding: '22px 24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <div className="section-title">FHIR R4 $translate Response</div>
                  <div className="section-subtitle">Parameters resource · WHO system URI · Real-time output</div>
                </div>
                <span className="provenance-badge provenance-algo">● FHIR R4</span>
              </div>
              <pre>{JSON.stringify(fhirResponse, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
