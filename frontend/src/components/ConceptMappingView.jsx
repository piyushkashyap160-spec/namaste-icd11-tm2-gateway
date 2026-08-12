import React, { useState, useEffect } from 'react';
import { getConceptMapping, translateFhir } from '../services/api';
import { Search, GitMerge, AlertTriangle, ShieldCheck, ArrowDown, Check, XCircle } from 'lucide-react';

export default function ConceptMappingView({ selectedCode, onCodeChange }) {
  const [inputCode, setInputCode] = useState(selectedCode || 'SAT-D.8');
  const [result, setResult] = useState(null);
  const [fhirResponse, setFhirResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const runMapping = async (codeToRun) => {
    setLoading(true);
    setFhirResponse(null);
    try {
      const data = await getConceptMapping(codeToRun);
      setResult(data);
      
      // Auto fetch FHIR translate preview for top match if available
      if (data.namaste) {
        const fhirData = await translateFhir({
          resourceType: "Parameters",
          parameter: [
            {
              name: "code",
              valueCoding: {
                system: "http://namaste.gov.in/sat-d",
                code: data.namaste.code,
                display: data.namaste.display
              }
            }
          ]
        });
        setFhirResponse(fhirData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCode) {
      setInputCode(selectedCode);
      runMapping(selectedCode);
    } else {
      runMapping('SAT-D.8');
    }
  }, [selectedCode]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputCode) {
      runMapping(inputCode);
      if (onCodeChange) onCodeChange(inputCode);
    }
  };

  const getConfidenceBadge = (conf) => {
    switch (conf) {
      case 'HIGH': return <span className="badge badge-high">HIGH CONFIDENCE</span>;
      case 'MEDIUM': return <span className="badge badge-medium">MEDIUM CONFIDENCE</span>;
      case 'LOW': return <span className="badge badge-low">LOW CONFIDENCE</span>;
      default: return <span className="badge badge-none">NO CONFIDENCE</span>;
    }
  };

  return (
    <div>
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <form onSubmit={handleSubmit} className="input-group">
          <input
            type="text"
            className="form-input"
            placeholder="Enter NAMASTE code (e.g. SAT-D.8, SAT-D.51) or clinical text..."
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value)}
          />
          <button type="submit" className="btn" disabled={loading}>
            <GitMerge size={16} />
            {loading ? 'Evaluating...' : 'Run Mapping Engine'}
          </button>
        </form>
      </div>

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Source NAMASTE Concept Box */}
          <div className="glass-panel" style={{ padding: '24px', borderLeft: '4px solid var(--primary-cyan)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
              Source Concept (AYUSH NAMASTE)
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '8px 0' }}>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>{result.namaste.display}</h2>
              <span className="badge badge-high">{result.namaste.code}</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              "{result.namaste.definition}"
            </p>
          </div>

          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', padding: '8px 16px', borderRadius: '20px', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--primary-cyan)', gap: '8px', fontSize: '0.85rem', fontWeight: 600 }}>
              <ArrowDown size={16} />
              <span>Deterministic Clinical Feature Extraction & hard rejection evaluation</span>
            </div>
          </div>

          {/* Mapping Status Disclaimer */}
          <div className="disclaimer-banner">
            <AlertTriangle size={18} />
            <div>
              <strong>Mapping Status: {result.mapping_status}</strong> — {result.note}
            </div>
          </div>

          {/* Candidate Mappings List */}
          {result.count === 0 ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', borderColor: 'rgba(244, 63, 94, 0.3)' }}>
              <XCircle size={48} color="var(--accent-rose)" style={{ marginBottom: '12px' }} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-rose)' }}>NO_CANDIDATE</h3>
              <p style={{ color: 'var(--text-muted)', marginTop: '6px', maxWidth: '500px', margin: '6px auto 0 auto' }}>
                No candidate concept passed clinical safety thresholds or explicit hard rejection rules. System avoided producing a false forced mapping.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                Candidate Matches ({result.count})
              </h3>

              {result.matches.map((match, idx) => (
                <div key={match.tm2_id} className="glass-panel" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                        TM2 CONCEPT ID: {match.tm2_id} | EQUIVALENCE: {match.equivalence}
                      </div>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '4px' }}>
                        {match.tm2_title}
                      </h3>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      {getConfidenceBadge(match.confidence)}
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--primary-cyan)', marginTop: '4px' }}>
                        Score: {match.score}
                      </div>
                    </div>
                  </div>

                  {/* Evidence Section */}
                  <div style={{ background: 'rgba(10, 14, 23, 0.6)', padding: '16px', borderRadius: '12px', marginTop: '16px' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Clinical Evidence & Feature Matches
                    </div>
                    <div className="tag-container">
                      {match.evidence.anatomy.map(a => (
                        <span key={a} className="tag tag-anatomy">Anatomy: {a}</span>
                      ))}
                      {match.evidence.symptoms.map(s => (
                        <span key={s} className="tag tag-symptom">Symptom: {s}</span>
                      ))}
                      {match.evidence.quality.map(q => (
                        <span key={q} className="tag">Quality: {q}</span>
                      ))}
                      {match.evidence.words.map(w => (
                        <span key={w} className="tag">Word: {w}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* FHIR $translate Payload Drawer */}
          {fhirResponse && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>FHIR R4 $translate Output (JSON)</h3>
                <span className="tag" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8' }}>
                  Parameters Resource
                </span>
              </div>
              <pre>{JSON.stringify(fhirResponse, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
