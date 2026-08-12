import React, { useEffect, useState } from 'react';
import { fetchNamasteConcepts, fetchTm2Concepts } from '../services/api';
import { AlertTriangle, ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function DashboardView({ onSelectConcept }) {
  const [namasteCount, setNamasteCount] = useState(0);
  const [tm2Count, setTm2Count] = useState(0);

  useEffect(() => {
    fetchNamasteConcepts().then(data => setNamasteCount(data.length)).catch(() => {});
    fetchTm2Concepts().then(data => setTm2Count(data.length)).catch(() => {});
  }, []);

  const testCases = [
    { code: 'SAT-D.8', display: 'aMsadAhaH', desc: 'burning in shoulder', expected: 'High Match (1564853364)' },
    { code: 'SAT-D.51', display: 'akasmAt SithilamalapravRuttiH', desc: 'sudden onset of loose stools', expected: 'Loose stool match ("sudden" not rejected)' },
    { code: 'SAT-D.12', display: 'netrarogaH', desc: 'eye diseases', expected: 'Broad Eye disorders (1249767098)' },
    { code: 'SAT-D.14', display: 'netradAhaH', desc: 'inflammation of eyes', expected: 'Inflammatory eye disorder (1874623910)' },
    { code: 'SAT-D.99', display: 'aMsa mathana vat vyathA', desc: 'shoulder being churned', expected: 'NO_CANDIDATE (No false forced match)' },
    { code: 'SAT-D.60', display: 'tvagrotra', desc: 'proper functioning of eyes', expected: 'NO_CANDIDATE (Functional query rule)' },
  ];

  return (
    <div>
      <div className="disclaimer-banner">
        <AlertTriangle size={18} />
        <div>
          <strong>Interoperability Candidate Mapping Gateway:</strong> This system generates candidate mappings for EHR integration demonstration. It does <strong>not</strong> establish official WHO or NAMASTE equivalence.
        </div>
      </div>

      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <span className="stat-label">Supported NAMASTE Concepts</span>
          <span className="stat-value">{namasteCount || 9}</span>
          <span className="tag tag-anatomy">SAT-D Ayush Standard</span>
        </div>
        <div className="glass-panel stat-card">
          <span className="stat-label">ICD-11 TM2 Concepts</span>
          <span className="stat-value">{tm2Count || 13}</span>
          <span className="tag tag-symptom">WHO ICD-11 Module 2</span>
        </div>
        <div className="glass-panel stat-card">
          <span className="stat-label">FHIR R4 Endpoint</span>
          <span className="stat-value" style={{ fontSize: '1.5rem', color: '#10b981' }}>$translate</span>
          <span className="tag">Parameters Resource</span>
        </div>
        <div className="glass-panel stat-card">
          <span className="stat-label">Hard Rejection Engine</span>
          <span className="stat-value" style={{ fontSize: '1.5rem', color: '#3b82f6' }}>Active</span>
          <span className="tag">6 Clinical Rules</span>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '24px', marginBottom: '32px' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 700 }}>
          Interactive Validation & Test Cases
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>
          Select a test case below to inspect clinical feature extraction, score breakdown, hard rejection rules, and FHIR translation output:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {testCases.map((tc) => (
            <div
              key={tc.code}
              className="glass-panel"
              style={{
                padding: '16px',
                cursor: 'pointer',
                background: 'rgba(255, 255, 255, 0.03)',
                borderColor: 'rgba(255, 255, 255, 0.08)'
              }}
              onClick={() => onSelectConcept(tc.code)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="tag tag-anatomy" style={{ fontWeight: 700 }}>{tc.code}</span>
                <ArrowRight size={16} color="var(--primary-cyan)" />
              </div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{tc.display}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '4px 0 10px 0' }}>
                "{tc.desc}"
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--primary-cyan)', fontWeight: 600 }}>
                Expected: {tc.expected}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
