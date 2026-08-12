import React from 'react';
import { Shield, Server } from 'lucide-react';

export default function Header({ title, description }) {
  return (
    <header className="top-header">
      <div>
        <h1 className="page-title">{title}</h1>
        <p className="page-description">{description}</p>
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <div className="auth-badge">
          <Server size={14} />
          <span>FHIR R4 Connected</span>
        </div>
        <div className="auth-badge" style={{ background: 'rgba(6, 182, 212, 0.1)', color: '#06b6d4', borderColor: 'rgba(6, 182, 212, 0.3)' }}>
          <Shield size={14} />
          <span>JWT Authed</span>
        </div>
      </div>
    </header>
  );
}
