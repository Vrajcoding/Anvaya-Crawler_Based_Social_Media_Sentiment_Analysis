import React, { useState } from 'react';
import { Shield, PhoneCall, UserCheck, RefreshCw, ZoomIn, ZoomOut, AlertTriangle } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, onRefresh }) {
  const [lang, setLang] = useState('hi');
  const [fontSize, setFontSize] = useState('normal');

  const toggleFontSize = () => {
    if (fontSize === 'normal') setFontSize('large');
    else setFontSize('normal');
    document.body.classList.toggle('font-lg');
  };

  return (
    <header>
      {/* GOV TOP UTILITY BAR */}
      <div className="gov-top-bar">
        <div>
          <span>🇮🇳 भारत सरकार | Govt. of India</span>
          <span>गृह विभाग (गुजरात राज्य) | Home Department</span>
          <span style={{ color: '#facc15', fontWeight: 700 }}>
            <PhoneCall size={14} style={{ display: 'inline', marginRight: '4px' }} />
            साइबर कंट्रोल रूम हेल्पलाइन: 1930 / 079-23254300
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* ACCESSIBILITY TEXT RESIZER */}
          <button 
            onClick={toggleFontSize} 
            style={{ background: 'transparent', border: '1px solid #475569', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700 }}
          >
            {fontSize === 'normal' ? '🔍 बड़ा टेक्स्ट (A+)' : '🔍 सामान्य टेक्स्ट (A-)'}
          </button>

          {/* LANGUAGE SELECTOR */}
          <select 
            value={lang} 
            onChange={(e) => setLang(e.target.value)}
            style={{ background: '#1e293b', color: '#fff', border: '1px solid #475569', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700 }}
          >
            <option value="hi">हिंदी (Hindi)</option>
            <option value="gu">ગુજરાતી (Gujarati)</option>
            <option value="en">English</option>
          </select>
        </div>
      </div>

      {/* EMBLEM & BRANDING BANNER */}
      <div className="gov-emblem-section">
        <div className="emblem-brand">
          <div className="emblem-icon">
            <Shield size={32} color="#fde047" />
          </div>

          <div className="emblem-title">
            <h1>SentinelAI — राष्ट्रीय सोशल मीडिया सुरक्षा एवं खतरा विश्लेषक</h1>
            <p>National Social Media Threat & Intelligence Monitoring Portal (ERH26_PS_05)</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>ड्यूटी अधिकारी (On-Duty Officer):</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--gov-navy-dark)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <UserCheck size={18} color="var(--gov-navy)" /> इंसपेक्टर आर. के. पटेल (Surat Cyber Cell)
            </div>
          </div>

          <button className="btn-gov-secondary" onClick={onRefresh} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            <RefreshCw size={16} />
            <span>डेटा अपडेट / Sync</span>
          </button>
        </div>
      </div>

      {/* NAVIGATION BAR */}
      <nav className="gov-nav-bar">
        <div 
          className={`gov-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          🏠 मुख्य डैशबोर्ड (Overview)
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          🚨 आपातकालीन अलर्ट (Critical Alerts)
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'feed' ? 'active' : ''}`}
          onClick={() => setActiveTab('feed')}
        >
          📰 सोशल मीडिया लाइव फीड (Social Feed)
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          📈 अफवाहें और ट्रेंड (Spikes & Rumors)
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'network' ? 'active' : ''}`}
          onClick={() => setActiveTab('network')}
        >
          🕸️ संदिग्ध गैंग व बॉट नेटवर्क (Bot Networks)
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'watchlist' ? 'active' : ''}`}
          onClick={() => setActiveTab('watchlist')}
        >
          🎯 निगरानी सूची (Watchlist Targets)
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          📄 सरकारी पुलिस रिपोर्ट (Police Reports)
        </div>
      </nav>
    </header>
  );
}
