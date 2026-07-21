import React, { useState } from 'react';
import { generateReport } from '../services/api';
import { FileText, Printer, Shield, CheckCircle } from 'lucide-react';

export default function Reports() {
  const [title, setTitle] = useState('सूरत हिंसा एवं पत्थरबाजी भड़काने वाले सोशल मीडिया खातों की जांच रिपोर्ट');
  const [description, setDescription] = useState('साइबर सेल गुजरात राज्य द्वारा सूरत क्षेत्र में अफवाह फैलाने वाले एक्स एवं फेसबुक एकाउंट्स की विशेष साइबर थ्रेट रिपोर्ट।');
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
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>📄 सरकारी पुलिस थ्रेट रिपोर्ट जनरेटर (Official CTI Police Reports)</h2>
          <p>उच्चाधिकारियों एवं वरिष्ठ कमान को प्रस्तुत करने हेतु औपचारिक साइबर रिपोर्ट तैयार करें</p>
        </div>
      </div>

      <div className="gov-card" style={{ border: '2px solid var(--gov-navy)' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={20} color="var(--gov-navy)" /> नई पुलिस रिपोर्ट तैयार करें (Compile Official Incident Report)
        </h3>

        <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.95rem', fontWeight: 700, display: 'block', marginBottom: '0.25rem' }}>रिपोर्ट शीर्षक (Report Title):</label>
              <input 
                type="text" 
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{ width: '100%', border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.95rem', fontWeight: 700, display: 'block', marginBottom: '0.25rem' }}>गंभीरता स्तर (Severity):</label>
              <select 
                value={severity} 
                onChange={(e) => setSeverity(e.target.value)}
                style={{ width: '100%', border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem', fontWeight: 700 }}
              >
                <option value="CRITICAL">🔴 CRITICAL (अत्यंत गंभीर)</option>
                <option value="HIGH">🟧 HIGH (गंभीर)</option>
                <option value="MEDIUM">🟨 MEDIUM (मध्यम)</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.95rem', fontWeight: 700, display: 'block', marginBottom: '0.25rem' }}>घटना का विवरण (Incident Narrative Brief):</label>
            <textarea 
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ width: '100%', border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem' }}
            />
          </div>

          <button type="submit" className="btn-gov-primary" disabled={generating} style={{ width: 'fit-content' }}>
            <FileText size={18} />
            <span>{generating ? 'रिपोर्ट तैयार हो रही है...' : 'सरकारी रिपोर्ट जनरेट करें (Generate Report)'}</span>
          </button>
        </form>
      </div>

      {reportResult && (
        <div className="gov-card" style={{ background: '#ffffff', border: '3px solid var(--gov-navy)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '2px solid var(--gov-navy)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Shield size={32} color="var(--gov-navy)" />
              <div>
                <h3 style={{ color: 'var(--gov-navy-dark)', fontSize: '1.3rem', fontWeight: 800 }}>आधिकारिक साइबर पुलिस थ्रेट रिपोर्ट (Official Police Intelligence Report)</h3>
                <span style={{ fontSize: '0.85rem', color: '#64748b' }}>CONFIDENTIAL • GOVERNMENT OF GUJARAT CYBER CELL</span>
              </div>
            </div>

            <button className="btn-gov-primary" onClick={() => window.print()}>
              <Printer size={18} /> प्रिंट / PDF डाउनलोड करें (Print PDF)
            </button>
          </div>

          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '1rem', color: '#0f172a', lineHeight: 1.7, background: '#f8fafc', padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border-gov)' }}>
            {reportResult.report_md}
          </pre>

          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'space-between', paddingTop: '1.5rem', borderTop: '2px dashed var(--border-gov)' }}>
            <div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>जांच अधिकारी हस्ताक्षर (Investigating Officer Sign):</div>
              <div style={{ fontWeight: 800, marginTop: '1.5rem', color: 'var(--gov-navy-dark)' }}>इंसपेक्टर आर. के. पटेल</div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>मुहर / Official Stamp Area:</div>
              <div style={{ border: '2px dashed #94a3b8', width: '120px', height: '60px', borderRadius: '6px', marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyCenter: 'center', fontSize: '0.75rem', color: '#94a3b8' }}>
                SEAL STAMP
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
