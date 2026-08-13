import React, { useEffect, useState } from 'react';
import { fetchNamasteConcepts, fetchTm2Concepts, getConceptMapping, translateFhir } from '../services/api';

const STAT_CARDS = [
  {
    accent: 'var(--cyan)',
    icon: '🌐',
    iconBg: 'rgba(6,182,212,0.12)',
    valueKey: 'tm2',
    label: 'WHO ICD-11 Concepts',
    sub: 'TM2 Module II · Release 2026-01',
    provenance: 'who',
  },
  {
    accent: 'var(--indigo)',
    icon: '📜',
    iconBg: 'rgba(99,102,241,0.12)',
    valueKey: 'namaste',
    label: 'NAMASTE Ayurveda Concepts',
    sub: 'AYUSH SAT-D Standard',
    provenance: 'local',
  },
  {
    accent: 'var(--emerald)',
    icon: '⬡',
    iconBg: 'rgba(16,185,129,0.12)',
    value: 'FHIR Active',
    label: '$translate API Status',
    sub: 'Parameters Resource Endpoint',
    provenance: null,
  },
  {
    accent: 'var(--amber)',
    icon: '⚙',
    iconBg: 'rgba(245,158,11,0.12)',
    value: 'Engine Active',
    label: 'Mapping Engine',
    sub: 'Hard Rejection & Feature Scoring',
    provenance: 'algo',
  },
];

const PRESETS = [
  { code: 'SAT-D.8', display: 'aMsadAhaH (Ayurveda: burning in shoulder)', short: 'SAT-D.8 (burning in shoulder)' },
  { code: 'SAT-D.51', display: 'akasmAt SithilamalapravRuttiH (loose stools)', short: 'SAT-D.51 (loose stools)' },
  { code: 'SAT-D.12', display: 'netrarogaH (eye diseases)', short: 'SAT-D.12 (eye diseases)' },
  { code: 'SAT-D.14', display: 'netradAhaH (inflammation of eyes)', short: 'SAT-D.14 (eye inflammation)' },
  { code: 'SAT-D.99', display: 'aMsa mathana vat vyathA (shoulder churning)', short: 'SAT-D.99 (no candidate test)' },
  { code: 'SAT-D.60', display: 'tvagrotra (proper functioning of eyes)', short: 'SAT-D.60 (functional query guard)' },
];

const ProvenanceBadge = ({ type }) => {
  if (!type) return null;
  const classes = {
    who: 'provenance-badge provenance-who',
    local: 'provenance-badge provenance-local',
    algo: 'provenance-badge provenance-algo',
  };
  const labels = {
    who: '● OFFICIAL · WHO',
    local: '● LOCAL DEMO',
    algo: '● ALGORITHMIC',
  };
  return <span className={classes[type]}>{labels[type]}</span>;
};

const ConfidenceBadge = ({ conf }) => {
  const map = {
    HIGH: ['badge badge-high', 'HIGH CONFIDENCE'],
    MEDIUM: ['badge badge-medium', 'MEDIUM CONFIDENCE'],
    LOW: ['badge badge-low', 'LOW CONFIDENCE'],
  };
  const [cls, label] = map[conf] || ['badge badge-none', 'NO CANDIDATE'];
  return <span className={cls}>{label}</span>;
};

export default function DashboardView({ onSelectConcept }) {
  const [counts, setCounts] = useState({ namaste: null, tm2: null });
  const [inputCode, setInputCode] = useState('SAT-D.8');
  const [mappingResult, setMappingResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchNamasteConcepts().then(d => setCounts(p => ({ ...p, namaste: d.length }))).catch(() => {});
    fetchTm2Concepts().then(d => setCounts(p => ({ ...p, tm2: d.length }))).catch(() => {});
  }, []);

  const runMapping = async (codeToRun) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConceptMapping(codeToRun);
      setMappingResult(data);
    } catch (err) {
      setError(err.message || 'Mapping failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runMapping('SAT-D.8');
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputCode.trim()) {
      runMapping(inputCode.trim());
    }
  };

  const handleSelectPreset = (code) => {
    setInputCode(code);
    runMapping(code);
  };

  const getDisplayValue = (card) => {
    if (card.value) return card.value;
    const v = counts[card.valueKey];
    return v !== null ? v : '–';
  };

  const topMatch = mappingResult?.matches?.[0];

  return (
    <div>
      {/* Disclaimer Banner */}
      <div className="disclaimer-banner">
        <span style={{ fontSize: 16, flexShrink: 0 }}>⚠</span>
        <div>
          <strong>Interoperability Candidate Mapping Gateway:</strong> This system generates candidate mappings for EHR integration demonstration. It does <strong>not</strong> establish official WHO or NAMASTE clinical equivalence. Data sources are clearly distinguished: <strong>OFFICIAL</strong> (WHO ICD-11 TM2), <strong>LOCAL</strong> (AYUSH SAT-D), and <strong>ALGORITHMIC</strong> (Candidate Engine).
        </div>
      </div>

      {/* Top 4 Stat Cards */}
      <div className="stats-grid">
        {STAT_CARDS.map((card, i) => (
          <div
            key={i}
            className="glass-panel stat-card"
            style={{ '--stat-accent': card.accent }}
          >
            <div className="stat-icon" style={{ background: card.iconBg, color: card.accent, fontSize: 18 }}>
              {card.icon}
            </div>
            <div className="stat-value">{getDisplayValue(card)}</div>
            <div className="stat-label">{card.label}</div>
            <div className="stat-sub">{card.sub}</div>
            {card.provenance && (
              <div style={{ marginTop: 8 }}>
                <ProvenanceBadge type={card.provenance} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Embedded Clinical Mapping Engine (Side-by-Side Reference Layout) */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '28px' }}>
        <div className="section-header" style={{ marginBottom: 20 }}>
          <div>
            <div className="section-title" style={{ fontSize: '1.2rem', fontWeight: 800 }}>
              Clinical Mapping Engine
            </div>
            <div className="section-subtitle">
              Deterministic clinical feature scoring, hard rejection evaluation, and ICD-11 TM2 candidate matching
            </div>
          </div>
          <span className="provenance-badge provenance-algo" style={{ fontSize: '0.72rem' }}>
            ● LIVE ENGINE
          </span>
        </div>

        <div className="mapping-engine-grid">
          {/* LEFT SIDE: Sanskrit/NAMASTE Concept Input & MAP NOW */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="glass-panel" style={{ padding: '20px', background: 'rgba(8, 13, 26, 0.65)' }}>
              <label
                htmlFor="dashboard-concept-input"
                style={{
                  display: 'block',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: 'var(--text-secondary)',
                  marginBottom: 10,
                }}
              >
                Enter Sanskrit Concept Code or Query
              </label>

              <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10 }}>
                <input
                  id="dashboard-concept-input"
                  type="text"
                  className="form-input"
                  placeholder="e.g. SAT-D.8, aMsadAhaH, or burning in shoulder..."
                  value={inputCode}
                  onChange={(e) => setInputCode(e.target.value)}
                  autoComplete="off"
                />
                <button
                  id="dashboard-map-now-btn"
                  type="submit"
                  className="btn"
                  disabled={loading}
                  style={{ background: 'linear-gradient(135deg, var(--cyan), var(--teal))', color: '#060b14', fontWeight: 800 }}
                >
                  {loading ? 'MAPPING...' : 'MAP NOW'}
                </button>
              </form>

              {/* Quick Select Presets */}
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: '0.73rem', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                  Quick Validation Presets
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {PRESETS.map((p) => (
                    <button
                      key={p.code}
                      type="button"
                      className="btn btn-secondary"
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.74rem',
                        borderRadius: 6,
                        borderColor: inputCode === p.code ? 'var(--cyan)' : 'var(--border-subtle)',
                        background: inputCode === p.code ? 'rgba(6, 182, 212, 0.12)' : 'rgba(255,255,255,0.04)',
                        color: inputCode === p.code ? 'var(--cyan)' : 'var(--text-secondary)',
                      }}
                      onClick={() => handleSelectPreset(p.code)}
                    >
                      {p.short}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Source Details Box */}
            {mappingResult?.namaste && (
              <div className="glass-panel" style={{ padding: '16px 18px', borderLeft: '3px solid var(--cyan)', background: 'rgba(5, 9, 18, 0.4)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Source Concept (AYUSH SAT-D)
                </div>
                <div style={{ fontWeight: 800, fontSize: '0.98rem', color: 'var(--text-primary)', marginTop: 4 }}>
                  [{mappingResult.namaste.code}] {mappingResult.namaste.display}
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginTop: 3 }}>
                  "{mappingResult.namaste.definition}"
                </div>
              </div>
            )}
          </div>

          {/* RIGHT SIDE: Mapping Result Panel */}
          <div className="glass-panel" style={{ padding: '20px', background: 'rgba(8, 13, 26, 0.65)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                  Mapping Result
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-tertiary)' }}>
                  ICD-11 TM2 Candidate Concept Code
                </div>
              </div>
              {topMatch && <ConfidenceBadge conf={topMatch.confidence} />}
              {mappingResult && !topMatch && <span className="badge badge-none">NO CANDIDATE</span>}
            </div>

            {error && (
              <div style={{ padding: '12px 14px', background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.25)', borderRadius: 8, color: 'var(--rose)', fontSize: '0.82rem' }}>
                ⚠ {error}
              </div>
            )}

            {loading && (
              <div style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-secondary)' }}>
                <div className="spinner" style={{ width: 24, height: 24, margin: '0 auto 10px auto', borderWidth: 3 }} />
                <div style={{ fontSize: '0.85rem' }}>Evaluating candidate mapping engine...</div>
              </div>
            )}

            {!loading && topMatch && (
              <div>
                {/* Result Title & Code */}
                <div style={{ padding: '14px 16px', background: 'rgba(6, 182, 212, 0.06)', border: '1px solid rgba(6, 182, 212, 0.20)', borderRadius: 10, marginBottom: 16 }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--cyan)', fontWeight: 700 }}>
                    ({topMatch.tm2_code || topMatch.tm2_id}) &nbsp;•&nbsp; {topMatch.equivalence}
                  </div>
                  <div style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--text-primary)', marginTop: 4 }}>
                    {topMatch.tm2_title}
                  </div>
                </div>

                {/* Score Meter */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    <span>Score Meter</span>
                    <span style={{ color: 'var(--cyan)' }}>Match Score: {topMatch.score} / 100</span>
                  </div>
                  <div className="score-bar-track" style={{ height: 10, borderRadius: 6 }}>
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${Math.min(100, Math.max(10, (topMatch.score / 50) * 100))}%`,
                        borderRadius: 6,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        paddingRight: 6,
                        fontSize: '0.65rem',
                        fontWeight: 800,
                        color: '#060b14',
                      }}
                    >
                      {Math.round(Math.min(100, (topMatch.score / 50) * 100))}%
                    </div>
                  </div>
                </div>

                {/* Evidence Tags */}
                <div className="evidence-panel" style={{ marginTop: 0 }}>
                  <div className="evidence-panel-label" style={{ fontSize: '0.72rem', marginBottom: 6 }}>
                    Evidence Tags
                  </div>
                  <div className="tag-container" style={{ marginTop: 4 }}>
                    {topMatch.evidence?.anatomy?.map((a) => (
                      <span key={a} className="tag tag-anatomy">Anatomy: {a}</span>
                    ))}
                    {topMatch.evidence?.symptoms?.map((s) => (
                      <span key={s} className="tag tag-symptom">Symptom: {s}</span>
                    ))}
                    {topMatch.evidence?.quality?.map((q) => (
                      <span key={q} className="tag tag-quality">Quality: {q}</span>
                    ))}
                    {topMatch.evidence?.words?.map((w) => (
                      <span key={w} className="tag">Word: {w}</span>
                    ))}
                    {[
                      ...(topMatch.evidence?.anatomy || []),
                      ...(topMatch.evidence?.symptoms || []),
                      ...(topMatch.evidence?.quality || []),
                      ...(topMatch.evidence?.words || []),
                    ].length === 0 && (
                      <span className="tag" style={{ color: 'var(--text-tertiary)' }}>
                        No direct symptom token match (Anatomy-only candidate)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {!loading && mappingResult && !topMatch && (
              <div className="no-candidate-panel" style={{ padding: '24px 16px' }}>
                <div className="no-candidate-icon" style={{ width: 42, height: 42, marginBottom: 10 }}>
                  <span style={{ fontSize: 18, color: 'var(--rose)' }}>✗</span>
                </div>
                <div className="no-candidate-title" style={{ fontSize: '1rem' }}>NO_CANDIDATE</div>
                <p className="no-candidate-desc" style={{ fontSize: '0.8rem' }}>
                  Hard rejection rule or confidence threshold triggered.
                  System avoided producing a false forced mapping.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Architecture Summary / Steps */}
      <div className="glass-panel" style={{ padding: '22px 24px' }}>
        <div className="section-title" style={{ marginBottom: 12 }}>
          Gateway Interoperability Pipeline
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          {[
            { step: '01', label: 'NAMASTE Lookup', desc: 'SAT-D code → Sanskrit clinical concept' },
            { step: '02', label: 'Feature Extraction', desc: 'Anatomy · Symptoms · Quality · Temporal' },
            { step: '03', label: 'Hard Rejection', desc: '5 safety rules enforce anatomical & functional boundaries' },
            { step: '04', label: 'Candidate Scoring', desc: 'Deterministic weighted clinical feature overlap' },
            { step: '05', label: 'FHIR R4 $translate', desc: 'WHO Parameters resource output with match evidence' },
          ].map((s) => (
            <div
              key={s.step}
              style={{
                padding: '14px 16px',
                background: 'rgba(255,255,255,0.025)',
                borderRadius: 10,
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontFamily: 'var(--mono)', fontSize: '0.68rem', color: 'var(--cyan)', fontWeight: 700, marginBottom: 4 }}>
                STEP {s.step}
              </div>
              <div style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
