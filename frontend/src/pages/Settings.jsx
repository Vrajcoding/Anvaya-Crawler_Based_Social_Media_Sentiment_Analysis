import React, { useState } from 'react';
import Header from '../components/Header';
import { submitFeedback } from '../services/api';
import { Sliders, Cpu, Save, RefreshCw } from 'lucide-react';

export default function Settings() {
  const [postId, setPostId] = useState('post-gu-002');
  const [correctedLabel, setCorrectedLabel] = useState('Incitement to Violence');
  const [notes, setNotes] = useState('Confirmed by analyst on ground duty.');
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
    <div>
      <Header 
        title="Analyst Settings & Learning Feedback Loop" 
        subtitle="Human-in-the-loop ML model tuning and agent orchestration parameters"
        onRefresh={() => {}}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* HUMAN IN THE LOOP FEEDBACK FORM */}
        <div className="card-glass">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu color="var(--accent-cyan)" size={20} /> Submit Analyst Feedback (Retrain Loop)
          </h3>

          <form onSubmit={handleSubmitFeedback} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Post ID to correct:</label>
              <input 
                type="text" 
                value={postId}
                onChange={(e) => setPostId(e.target.value)}
                style={{ width: '100%', background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem', borderRadius: '6px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Corrected Threat Label:</label>
              <select 
                value={correctedLabel}
                onChange={(e) => setCorrectedLabel(e.target.value)}
                style={{ width: '100%', background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem', borderRadius: '6px' }}
              >
                <option value="Incitement to Violence">Incitement to Violence</option>
                <option value="Fake News">Fake News</option>
                <option value="Inflammatory">Inflammatory</option>
                <option value="Neutral">Neutral</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Analyst Verification Notes:</label>
              <textarea 
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ width: '100%', background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem', borderRadius: '6px' }}
              />
            </div>

            <button type="submit" className="btn-primary" style={{ width: 'fit-content' }}>
              <Save size={16} /> Submit Corrected Label
            </button>

            {submitted && (
              <div style={{ color: '#4ade80', fontSize: '0.9rem', fontWeight: 600 }}>
                ✅ Feedback recorded! Learning Agent has updated weights for the next training cycle.
              </div>
            )}
          </form>
        </div>

        {/* THREAT SCORING WEIGHTS CONFIGURATION */}
        <div className="card-glass">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders color="var(--accent-purple)" size={20} /> Threat Formula Model Weights
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1e293b', borderRadius: '6px' }}>
              <span>Sentiment Weight (w1):</span>
              <strong style={{ color: 'var(--accent-cyan)' }}>0.15 (15%)</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1e293b', borderRadius: '6px' }}>
              <span>Threat Category Weight (w2):</span>
              <strong style={{ color: '#ef4444' }}>0.30 (30% - Highest)</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1e293b', borderRadius: '6px' }}>
              <span>Hate Speech Weight (w3):</span>
              <strong style={{ color: '#f97316' }}>0.20 (20%)</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1e293b', borderRadius: '6px' }}>
              <span>Viral Velocity Weight (w4):</span>
              <strong style={{ color: '#eab308' }}>0.10 (10%)</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1e293b', borderRadius: '6px' }}>
              <span>Coordination Group Weight (w5):</span>
              <strong style={{ color: '#a855f7' }}>0.15 (15%)</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1e293b', borderRadius: '6px' }}>
              <span>Bot Detection Weight (w6):</span>
              <strong style={{ color: '#a855f7' }}>0.10 (10%)</strong>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
