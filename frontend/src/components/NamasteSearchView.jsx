import React, { useEffect, useState } from 'react';
import { fetchNamasteConcepts } from '../services/api';
import { Search, ArrowRight, BookOpen } from 'lucide-react';

export default function NamasteSearchView({ onSelectConcept }) {
  const [concepts, setConcepts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNamasteConcepts()
      .then(data => {
        setConcepts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filtered = concepts.filter(c => 
    c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.display.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.definition.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
        <div className="input-group">
          <input
            type="text"
            className="form-input"
            placeholder="Search NAMASTE concepts by code (SAT-D.8), Sanskrit display, or definition..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button className="btn">
            <Search size={16} />
            Search
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Loading catalog...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '20px' }}>
          {filtered.map(c => (
            <div key={c.code} className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span className="badge badge-high">{c.code}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{c.terminology}</span>
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '6px' }}>{c.display}</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
                "{c.definition}"
              </p>
              <button 
                className="btn btn-secondary" 
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => onSelectConcept(c.code)}
              >
                Map to ICD-11 TM2
                <ArrowRight size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
