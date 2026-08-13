import React from 'react';

export default function Header({ eyebrow, title, description }) {
  return (
    <div className="top-header">
      <div className="header-text">
        {eyebrow && <div className="page-eyebrow">{eyebrow}</div>}
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      <div className="auth-badge">
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px rgba(16,185,129,0.6)', display: 'inline-block' }} />
        API Online · JWT Auth
      </div>
    </div>
  );
}
