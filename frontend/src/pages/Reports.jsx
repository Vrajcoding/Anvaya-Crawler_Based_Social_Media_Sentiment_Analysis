import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import { generateReport } from '../services/api';
import { FileText, Download, Sparkles, Printer } from 'lucide-react';

export default function Reports() {
  const [title, setTitle] = useState('Surat Mob Gathering & Incitement Briefing');
  const [description, setDescription] = useState('Automated Cyber Threat Intelligence summary documenting coordinated calls to violence and stone pelting in Surat.');
  const [severity, setSeverity] = useState('CRITICAL');
  const [generating, setGenerating] = useState(false);
  const [reportResult, setReportResult] = useState(null);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const res = await generateReport({ title, description, severity });
      setReportResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      <Header 
        title="CTI Incident Report Generator" 
        subtitle="Automated intelligence briefing compilation for senior command and law enforcement response"
        onRefresh={() => {}}
      />

      <div className="card-glass" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles color="var(--accent-cyan)" size={20} /> Compile Formal Incident Report
        </h3>

        <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Incident Title:</label>
              <input 
                type="text" 
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{ width: '100%', background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem', borderRadius: '6px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Severity Rating:</label>
              <select 
                value={severity} 
                onChange={(e) => setSeverity(e.target.value)}
                style={{ width: '100%', background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem', borderRadius: '6px' }}
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Incident Executive Briefing:</label>
            <textarea 
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ width: '100%', background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem', borderRadius: '6px' }}
            />
          </div>

          <button type="submit" className="btn-primary" disabled={generating} style={{ width: 'fit-content' }}>
            <FileText size={16} />
            <span>{generating ? 'Compiling CTI Report...' : 'Generate Official Report'}</span>
          </button>
        </form>
      </div>

      {reportResult && (
        <div className="card-glass" style={{ background: '#090d16', borderColor: 'var(--accent-cyan)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
            <h3 style={{ color: 'var(--accent-cyan)', fontSize: '1.1rem' }}>Generated Incident Report Briefing</h3>
            <button className="btn-secondary" onClick={() => window.print()}>
              <Printer size={16} /> Print / Export PDF
            </button>
          </div>

          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9rem', color: '#e2e8f0', lineHeight: 1.6 }}>
            {reportResult.report_md}
          </pre>
        </div>
      )}
    </div>
  );
}
