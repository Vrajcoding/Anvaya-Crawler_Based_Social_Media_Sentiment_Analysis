import React, { useState, useEffect } from 'react';
import { submitFeedback } from '../services/api';
import { Save, CheckCircle, Sliders, Cpu, Key, Radio, Sparkles } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function Settings() {
  const { t } = useLanguage();
  
  // Human-in-the-loop feedback state
  const [postId, setPostId] = useState('post-gu-002');
  const [correctedLabel, setCorrectedLabel] = useState('Incitement to Violence');
  const [notes, setNotes] = useState('Confirmed by Surat cyber cell duty officer.');
  const [submitted, setSubmitted] = useState(false);

  // OpenRouter Multi-Agent settings state
  const [apiKey, setApiKey] = useState('your_openrouter_api_key_here');
  const [nlpModel, setNlpModel] = useState('google/gemini-2.0-flash-exp:free');
  const [threatModel, setThreatModel] = useState('meta-llama/llama-3.3-70b-instruct:free');
  const [reportModel, setReportModel] = useState('deepseek/deepseek-chat:free');
  const [alertModel, setAlertModel] = useState('qwen/qwen-2.5-7b-instruct:free');
  const [openRouterSaved, setOpenRouterSaved] = useState(false);

  useEffect(() => {
    // Load existing OpenRouter settings from backend
    fetch('http://localhost:8000/api/v1/settings/openrouter')
      .then(r => r.json())
      .then(data => {
        if (data.api_key) setApiKey(data.api_key);
        if (data.agent_nlp_model) setNlpModel(data.agent_nlp_model);
        if (data.agent_threat_model) setThreatModel(data.agent_threat_model);
        if (data.agent_report_model) setReportModel(data.agent_report_model);
        if (data.agent_alert_model) setAlertModel(data.agent_alert_model);
      })
      .catch(e => console.error(e));
  }, []);

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

  const handleSaveOpenRouter = async (e) => {
    e.preventDefault();
    try {
      await fetch('http://localhost:8000/api/v1/settings/openrouter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          agent_nlp_model: nlpModel,
          agent_threat_model: threatModel,
          agent_report_model: reportModel,
          agent_alert_model: alertModel
        })
      });
      setOpenRouterSaved(true);
      setTimeout(() => setOpenRouterSaved(false), 4000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>{t('settings_title')}</h2>
          <p>{t('settings_subtitle')}</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* OPENROUTER AI MULTI-AGENT SETTINGS */}
        <div className="gov-card" style={{ border: '2px solid #2563eb', background: '#eff6ff' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#1e3a8a', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={22} color="#2563eb" /> {t('settings_title')}
          </h3>

          <form onSubmit={handleSaveOpenRouter} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
            <div>
              <label style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1e3a8a', display: 'block', marginBottom: '0.25rem' }}>
                🔑 {t('api_key_label')}
              </label>
              <input 
                type="password" 
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ width: '100%', border: '2px solid #93c5fd', padding: '0.6rem', borderRadius: '6px', fontSize: '0.95rem', background: '#fff' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1e3a8a', display: 'block', marginBottom: '0.25rem' }}>
                🧠 {t('nlp_model_label')}
              </label>
              <select 
                value={nlpModel}
                onChange={(e) => setNlpModel(e.target.value)}
                style={{ width: '100%', border: '2px solid #93c5fd', padding: '0.6rem', borderRadius: '6px', fontSize: '0.95rem', fontWeight: 700, background: '#fff' }}
              >
                <option value="google/gemini-2.0-flash-exp:free">google/gemini-2.0-flash-exp:free (Fast Multilingual JSON)</option>
                <option value="meta-llama/llama-3.3-70b-instruct:free">meta-llama/llama-3.3-70b-instruct:free (High Reasoning)</option>
                <option value="deepseek/deepseek-chat:free">deepseek/deepseek-chat:free</option>
                <option value="qwen/qwen-2.5-7b-instruct:free">qwen/qwen-2.5-7b-instruct:free</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1e3a8a', display: 'block', marginBottom: '0.25rem' }}>
                🛡️ {t('threat_model_label')}
              </label>
              <select 
                value={threatModel}
                onChange={(e) => setThreatModel(e.target.value)}
                style={{ width: '100%', border: '2px solid #93c5fd', padding: '0.6rem', borderRadius: '6px', fontSize: '0.95rem', fontWeight: 700, background: '#fff' }}
              >
                <option value="meta-llama/llama-3.3-70b-instruct:free">meta-llama/llama-3.3-70b-instruct:free (Deep Threat Analysis)</option>
                <option value="google/gemini-2.0-flash-exp:free">google/gemini-2.0-flash-exp:free</option>
                <option value="deepseek/deepseek-chat:free">deepseek/deepseek-chat:free</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1e3a8a', display: 'block', marginBottom: '0.25rem' }}>
                📄 {t('report_model_label')}
              </label>
              <select 
                value={reportModel}
                onChange={(e) => setReportModel(e.target.value)}
                style={{ width: '100%', border: '2px solid #93c5fd', padding: '0.6rem', borderRadius: '6px', fontSize: '0.95rem', fontWeight: 700, background: '#fff' }}
              >
                <option value="deepseek/deepseek-chat:free">deepseek/deepseek-chat:free (Professional CTI Brief Synthesis)</option>
                <option value="google/gemini-2.0-flash-exp:free">google/gemini-2.0-flash-exp:free</option>
                <option value="meta-llama/llama-3.3-70b-instruct:free">meta-llama/llama-3.3-70b-instruct:free</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1e3a8a', display: 'block', marginBottom: '0.25rem' }}>
                ⚡ {t('alert_model_label')}
              </label>
              <select 
                value={alertModel}
                onChange={(e) => setAlertModel(e.target.value)}
                style={{ width: '100%', border: '2px solid #93c5fd', padding: '0.6rem', borderRadius: '6px', fontSize: '0.95rem', fontWeight: 700, background: '#fff' }}
              >
                <option value="qwen/qwen-2.5-7b-instruct:free">qwen/qwen-2.5-7b-instruct:free (Sub-second Alert Dispatch)</option>
                <option value="google/gemini-2.0-flash-exp:free">google/gemini-2.0-flash-exp:free</option>
              </select>
            </div>

            <button type="submit" className="btn-gov-primary" style={{ width: 'fit-content', background: '#2563eb' }}>
              <Save size={18} /> {t('btn_save_settings')}
            </button>

            {openRouterSaved && (
              <div style={{ background: '#dcfce7', color: '#166534', padding: '0.75rem', borderRadius: '6px', fontWeight: 800 }}>
                {t('settings_saved_msg')}
              </div>
            )}
          </form>
        </div>

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
                <option value="Incitement to Violence">{t('filter_incitement')}</option>
                <option value="Fake News">{t('filter_fakenews')}</option>
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

      </div>
    </div>
  );
}

