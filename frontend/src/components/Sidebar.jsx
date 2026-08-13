import React from 'react';

const NAV = [
  { id: 'dashboard', icon: '⊞', label: 'Dashboard' },
  { id: 'namaste', icon: '☽', label: 'NAMASTE Concepts' },
  { id: 'mapping', icon: '⇄', label: 'Mapping Engine' },
  { id: 'fhir', icon: '⬡', label: 'FHIR $translate' },
  { id: 'audit', icon: '⊙', label: 'Audit Trail' },
  { id: 'docs', icon: '⊡', label: 'API Docs' },
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="sidebar">
      <div className="brand-header">
        <div className="brand-icon">🌿</div>
        <div>
          <div className="brand-title">NAMASTE Gateway</div>
          <div className="brand-subtitle">ICD-11 TM2 · FHIR R4</div>
        </div>
      </div>

      <div className="nav-section">
        <div className="nav-section-label">Navigation</div>
        <ul className="nav-list">
          {NAV.map(item => (
            <li
              key={item.id}
              className={`nav-item${activeTab === item.id ? ' active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="nav-icon" style={{ fontSize: 16, lineHeight: 1 }}>{item.icon}</span>
              <span>{item.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-chip">
          <span className="sidebar-chip-dot" />
          WHO ICD-11 TM2 · 2026-01
        </div>
        <div className="sidebar-chip" style={{ color: 'var(--text-tertiary)' }}>
          AYUSH NAMASTE SAT-D Standard
        </div>
        <div className="sidebar-chip" style={{ color: 'var(--text-tertiary)' }}>
          FHIR R4 Compliant API
        </div>
      </div>
    </aside>
  );
}
