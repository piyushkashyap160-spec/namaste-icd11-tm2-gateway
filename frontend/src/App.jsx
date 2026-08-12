import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/DashboardView';
import NamasteSearchView from './components/NamasteSearchView';
import ConceptMappingView from './components/ConceptMappingView';
import FhirTesterView from './components/FhirTesterView';
import AuditLogsView from './components/AuditLogsView';
import ApiDocsView from './components/ApiDocsView';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedConceptCode, setSelectedConceptCode] = useState('SAT-D.8');

  const handleSelectConcept = (code) => {
    setSelectedConceptCode(code);
    setActiveTab('mapping');
  };

  const getTabMetadata = () => {
    switch (activeTab) {
      case 'dashboard':
        return { title: 'Dashboard Overview', description: 'System health, concept counts, and clinical mapping test suite' };
      case 'namaste':
        return { title: 'AYUSH NAMASTE Catalog', description: 'Search and inspect supported Ayush SAT-D terminology concepts' };
      case 'mapping':
        return { title: 'Candidate Terminology Mapping Engine', description: 'Deterministic clinical feature scoring, hard rejection evaluation, and ICD-11 TM2 candidate matching' };
      case 'fhir':
        return { title: 'FHIR R4 $translate Tester', description: 'Interactive FHIR Parameters JSON request/response testing tool' };
      case 'audit':
        return { title: 'Audit Trail & Governance', description: 'Non-PHI access logs for EHR compliance and traceability' };
      case 'docs':
        return { title: 'API Specifications', description: 'OpenAPI 3.0 & FHIR specification reference' };
      default:
        return { title: 'Interoperability Gateway', description: '' };
    }
  };

  const { title, description } = getTabMetadata();

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        <Header title={title} description={description} />
        
        {activeTab === 'dashboard' && <DashboardView onSelectConcept={handleSelectConcept} />}
        {activeTab === 'namaste' && <NamasteSearchView onSelectConcept={handleSelectConcept} />}
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
