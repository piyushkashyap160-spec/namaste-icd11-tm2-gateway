import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/DashboardView';
import NamasteSearchView from './components/NamasteSearchView';
import ConceptMappingView from './components/ConceptMappingView';
import FhirTesterView from './components/FhirTesterView';
import AuditLogsView from './components/AuditLogsView';
import ApiDocsView from './components/ApiDocsView';

const TAB_META = {
  dashboard: {
    eyebrow: 'System Overview',
    title: 'Dashboard',
    description: 'Concept counts, validation test suite, and architecture overview',
  },
  namaste: {
    eyebrow: 'Terminology Catalog',
    title: 'AYUSH NAMASTE Concepts',
    description: 'SAT-D Ayurvedic terminology catalog — searchable Sanskrit clinical concepts',
  },
  mapping: {
    eyebrow: 'Mapping Engine',
    title: 'Clinical Terminology Mapping',
    description: 'Deterministic feature extraction, hard rejection evaluation, and ICD-11 TM2 candidate scoring',
  },
  fhir: {
    eyebrow: 'FHIR R4',
    title: 'FHIR $translate Tester',
    description: 'Interactive FHIR Parameters request tester — live $translate API with JSON response',
  },
  audit: {
    eyebrow: 'Compliance',
    title: 'Audit Trail',
    description: 'Non-PHI access logs for EHR governance and interoperability compliance',
  },
  docs: {
    eyebrow: 'Developer Reference',
    title: 'API Documentation',
    description: 'OpenAPI 3.0 endpoints, JWT auth, FHIR specification, and standards references',
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedConceptCode, setSelectedConceptCode] = useState('SAT-D.8');

  const handleSelectConcept = (code) => {
    setSelectedConceptCode(code);
    setActiveTab('mapping');
  };

  const meta = TAB_META[activeTab] || TAB_META.dashboard;

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-content">
        <Header eyebrow={meta.eyebrow} title={meta.title} description={meta.description} />

        {activeTab === 'dashboard' && (
          <DashboardView onSelectConcept={handleSelectConcept} />
        )}
        {activeTab === 'namaste' && (
          <NamasteSearchView onSelectConcept={handleSelectConcept} />
        )}
        {activeTab === 'mapping' && (
          <ConceptMappingView
            selectedCode={selectedConceptCode}
            onCodeChange={setSelectedConceptCode}
          />
        )}
        {activeTab === 'fhir' && <FhirTesterView />}
        {activeTab === 'audit' && <AuditLogsView />}
        {activeTab === 'docs' && <ApiDocsView />}
      </main>
    </div>
  );
}
