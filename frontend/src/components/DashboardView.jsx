import React, { useEffect, useState } from 'react';
import { fetchNamasteConcepts, fetchTm2Concepts } from '../services/api';

const TEST_CASES = [
  {
    code: 'SAT-D.8',
    display: 'aMsadAhaH',
    desc: 'Burning in shoulder',
    expectedLabel: 'CANDIDATE_MAPPING',
    expectedColor: 'var(--emerald)',
  },
  {
    code: 'SAT-D.51',
    display: 'akasmAt SithilamalapravRuttiH',
    desc: 'Sudden loose stools',
    expectedLabel: 'CANDIDATE_MAPPING',
    expectedColor: 'var(--emerald)',
  },
  {
    code: 'SAT-D.12',
    display: 'netrarogaH',
    desc: 'Eye diseases (broad)',
    expectedLabel: 'CANDIDATE_MAPPING',
    expectedColor: 'var(--emerald)',
  },
  {
    code: 'SAT-D.14',
    display: 'netradAhaH',
    desc: 'Inflammation of eyes',
    expectedLabel: 'CANDIDATE_MAPPING',
    expectedColor: 'var(--emerald)',
  },
  {
    code: 'SAT-D.99',
    display: 'aMsa mathana vat vyathA',
    desc: 'Shoulder churning sensation',
    expectedLabel: 'NO_CANDIDATE',
    expectedColor: 'var(--rose)',
  },
  {
    code: 'SAT-D.60',
    display: 'tvagrotra',
    desc: 'Proper functioning of eyes',
    expectedLabel: 'NO_CANDIDATE',
    expectedColor: 'var(--rose)',
  },
];

const STAT_CARDS = [
  {
    accent: 'var(--cyan)',
    icon: '🌐',
    iconBg: 'rgba(6,182,212,0.12)',
    valueKey: 'tm2',
    label: 'WHO TM2 Concepts',
    sub: 'OFFICIAL · ICD-11 2026-01',
    provenance: 'who',
  },
  {
    accent: 'var(--indigo)',
    icon: '📜',
    iconBg: 'rgba(99,102,241,0.12)',
    valueKey: 'namaste',
    label: 'NAMASTE Concepts',
    sub: 'LOCAL · AYUSH SAT-D',
    provenance: 'local',
  },
  {
    accent: 'var(--emerald)',
    icon: '⬡',
    iconBg: 'rgba(16,185,129,0.12)',
    value: '$translate',
    label: 'FHIR R4 Endpoint',
    sub: 'Parameters Resource · Active',
    provenance: null,
  },
  {
    accent: 'var(--amber)',
    icon: '⚙',
    iconBg: 'rgba(245,158,11,0.12)',
    value: 'Active',
    label: 'Clinical Rules Engine',
    sub: '6 Hard Rejection Rules',
    provenance: 'algo',
  },
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

export default function DashboardView({ onSelectConcept }) {
  const [counts, setCounts] = useState({ namaste: null, tm2: null });

  useEffect(() => {
    fetchNamasteConcepts().then(d => setCounts(p => ({ ...p, namaste: d.length }))).catch(() => {});
    fetchTm2Concepts().then(d => setCounts(p => ({ ...p, tm2: d.length }))).catch(() => {});
  }, []);

  const getDisplayValue = (card) => {
    if (card.value) return card.value;
    const v = counts[card.valueKey];
    return v !== null ? v : '–';
  };

  return (
    <div>
      <div className="disclaimer-banner">
        <span style={{ fontSize: 16, flexShrink: 0 }}>⚠</span>
        <div>
          <strong>Hackathon Demo — Candidate Mapping Gateway.</strong>{' '}
          This system generates deterministic candidate mappings for EHR integration demonstration.
          It does <strong>not</strong> establish official WHO or NAMASTE clinical equivalence.
          Data sources are clearly distinguished: <strong>OFFICIAL</strong> (WHO ICD-11 TM2),{' '}
          <strong>LOCAL</strong> (AYUSH SAT-D), <strong>ALGORITHMIC</strong> (candidate engine).
        </div>
      </div>

      {/* Stats */}
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

      {/* Test Case Suite */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <div className="section-header">
          <div>
            <div className="section-title">Clinical Validation Suite</div>
            <div className="section-subtitle">
              Select a test case to run the full mapping engine — feature extraction, hard rejection, candidate scoring, and FHIR translation.
            </div>
          </div>
          <span className="badge badge-high" style={{ flexShrink: 0 }}>6 Cases</span>
        </div>

        <div className="test-cases-grid">
          {TEST_CASES.map((tc) => (
            <div
              key={tc.code}
              className="glass-panel test-case-card"
              onClick={() => onSelectConcept(tc.code)}
            >
              <div className="test-case-header">
                <span className="test-code">{tc.code}</span>
                <span style={{ fontSize: 14, color: 'var(--cyan)' }}>→</span>
              </div>
              <div className="test-display">{tc.display}</div>
              <div className="test-desc">"{tc.desc}"</div>
              <div className="test-expected">
                <span style={{ color: tc.expectedColor }}>● {tc.expectedLabel}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture Summary */}
      <div className="glass-panel" style={{ padding: '22px 24px' }}>
        <div className="section-title" style={{ marginBottom: 12 }}>Architecture Overview</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          {[
            { step: '01', label: 'NAMASTE Lookup', desc: 'SAT-D code → Sanskrit clinical concept' },
            { step: '02', label: 'Feature Extraction', desc: 'Anatomy · Symptoms · Quality · Temporal' },
            { step: '03', label: 'Hard Rejection (5 rules)', desc: 'Anatomy conflict · Object mismatch · Functional guard' },
            { step: '04', label: 'Candidate Scoring', desc: 'Deterministic weighted clinical overlap' },
            { step: '05', label: 'FHIR R4 $translate', desc: 'WHO Parameters resource output with match evidence' },
          ].map(s => (
            <div key={s.step} style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.025)', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '0.68rem', color: 'var(--cyan)', fontWeight: 700, marginBottom: 4 }}>STEP {s.step}</div>
              <div style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
