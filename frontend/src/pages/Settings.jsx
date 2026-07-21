import React, { useState } from 'react';
import { submitFeedback } from '../services/api';
import { Save, CheckCircle, Sliders } from 'lucide-react';

export default function Settings() {
  const [postId, setPostId] = useState('post-gu-002');
  const [correctedLabel, setCorrectedLabel] = useState('Incitement to Violence');
  const [notes, setNotes] = useState('फील्ड टीम द्वारा पुष्टि की गई कि यह फर्जी आईडी द्वारा भड़काऊ संदेश था।');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    await submitFeedback({
      post_id: postId,
      corrected_label: correctedLabel,
      notes
    });
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 4000);
  };

  return (
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>⚙️ पुलिस अधिकारी सेटिंग्स एवं फीडबैक रिफाइनर (Officer Controls)</h2>
          <p>मानव-सत्यापित (Human-in-the-Loop) AI मॉडल सुधार एवं थ्रेट स्कोरिंग पैरामीटर्स</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* HUMAN IN THE LOOP FORM */}
        <div className="gov-card" style={{ border: '2px solid var(--gov-navy)' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={20} color="var(--gov-navy)" /> AI वर्गीकरण में सुधार दर्ज करें (Submit AI Correction)
          </h3>

          <form onSubmit={handleSubmitFeedback} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label style={{ fontSize: '0.95rem', fontWeight: 700, display: 'block', marginBottom: '0.25rem' }}>पोस्ट आईडी (Post ID):</label>
              <input 
                type="text" 
                value={postId}
                onChange={(e) => setPostId(e.target.value)}
                style={{ width: '100%', border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.95rem', fontWeight: 700, display: 'block', marginBottom: '0.25rem' }}>सही खतरा लेबल (Corrected Threat Label):</label>
              <select 
                value={correctedLabel}
                onChange={(e) => setCorrectedLabel(e.target.value)}
                style={{ width: '100%', border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem', fontWeight: 700 }}
              >
                <option value="Incitement to Violence">हिंसा भड़काना (Incitement to Violence)</option>
                <option value="Fake News">झूठी खबर (Fake News)</option>
                <option value="Inflammatory">भड़काऊ (Inflammatory)</option>
                <option value="Neutral">सामान्य (Neutral)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.95rem', fontWeight: 700, display: 'block', marginBottom: '0.25rem' }}>अधिकारी जांच टिप्पणी (Officer Verification Note):</label>
              <textarea 
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ width: '100%', border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem' }}
              />
            </div>

            <button type="submit" className="btn-gov-primary" style={{ width: 'fit-content' }}>
              <Save size={18} /> सुधार सहेजें (Save Correction)
            </button>

            {submitted && (
              <div style={{ background: '#dcfce7', color: '#166534', padding: '0.75rem', borderRadius: '6px', fontWeight: 800 }}>
                ✅ सुधार दर्ज किया गया! मॉडल retraining चक्र में नया भार अपडेट कर दिया गया है।
              </div>
            )}
          </form>
        </div>

        {/* MODEL PARAMETERS INFO */}
        <div className="gov-card">
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '1rem' }}>
            📊 खतरा स्कोरिंग सूत्र के भार (Threat Weight Formula)
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '1rem', fontWeight: 600 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-gov)' }}>
              <span>भावना विश्लेषक भार (Sentiment Weight):</span>
              <strong style={{ color: 'var(--gov-navy)' }}>15%</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#fef2f2', borderRadius: '6px', border: '1px solid #f87171' }}>
              <span>खतरा श्रेणी भार (Threat Category Weight):</span>
              <strong style={{ color: '#dc2626' }}>30% (सर्वोच्च)</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#fff7ed', borderRadius: '6px', border: '1px solid #fb923c' }}>
              <span>नफरती भाषा भार (Hate Speech Weight):</span>
              <strong style={{ color: '#c2410c' }}>20%</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-gov)' }}>
              <span>फैलाव की गति भार (Viral Velocity Weight):</span>
              <strong>10%</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#f3e8ff', borderRadius: '6px', border: '1px solid #c084fc' }}>
              <span>गैंग नेटवर्क समन्वय भार (Coordination Group Weight):</span>
              <strong style={{ color: '#7e22ce' }}>15%</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-gov)' }}>
              <span>ऑटोमेटेड बॉट पहचान भार (Bot Likelihood Weight):</span>
              <strong>10%</strong>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
