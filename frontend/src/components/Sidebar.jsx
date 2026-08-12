import React from 'react';
import { 
  LayoutDashboard, 
  Search, 
  GitMerge, 
  FileCode2, 
  BookOpen, 
  ShieldCheck 
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'namaste', label: 'NAMASTE Catalog', icon: Search },
    { id: 'mapping', label: 'Concept Mapper', icon: GitMerge },
    { id: 'fhir', label: 'FHIR $translate', icon: FileCode2 },
    { id: 'audit', label: 'Audit Trail', icon: ShieldCheck },
    { id: 'docs', label: 'API Specs', icon: BookOpen },
  ];

  return (
    <aside className="sidebar">
      <div className="brand-header">
        <div className="brand-icon">🌿</div>
        <div>
          <div className="brand-title">AYUSH Interop</div>
          <div className="brand-subtitle">NAMASTE ↔ ICD-11 TM2</div>
        </div>
      </div>

      <ul className="nav-list">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <li
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon className="nav-icon" />
              <span>{item.label}</span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
