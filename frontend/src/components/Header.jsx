import React, { useState } from 'react';
import { Shield, PhoneCall, UserCheck, RefreshCw, ZoomIn, ZoomOut, AlertTriangle } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function Header({ activeTab, setActiveTab, onRefresh }) {
  const { lang, setLang, t } = useLanguage();
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
          <span>{t('gov_top_title')}</span>
          <span>{t('gov_top_dept')}</span>
          <span style={{ color: '#facc15', fontWeight: 700 }}>
            <PhoneCall size={14} style={{ display: 'inline', marginRight: '4px' }} />
            {t('cyber_helpline')}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* ACCESSIBILITY TEXT RESIZER */}
          <button 
            onClick={toggleFontSize} 
            style={{ background: 'transparent', border: '1px solid #475569', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700 }}
          >
            {fontSize === 'normal' ? t('text_size_large') : t('text_size_normal')}
          </button>

          {/* LANGUAGE SELECTOR */}
          <select 
            value={lang} 
            onChange={(e) => setLang(e.target.value)}
            style={{ background: '#1e293b', color: '#fff', border: '1px solid #fde047', padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, cursor: 'pointer', boxShadow: '0 0 10px rgba(253, 224, 71, 0.2)' }}
          >
            <option value="en">🌐 English</option>
            <option value="hi">🇮🇳 हिंदी</option>
            <option value="gu">🇮🇳 ગુજરાતી</option>
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
            <h1>{t('portal_title')}</h1>
            <p>{t('portal_subtitle')}</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>{t('on_duty_label')}</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--gov-navy-dark)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <UserCheck size={18} color="var(--gov-navy)" /> {t('duty_officer_name')}
            </div>
          </div>

          <button className="btn-gov-secondary" onClick={onRefresh} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            <RefreshCw size={16} />
            <span>{t('btn_sync_data')}</span>
          </button>
        </div>
      </div>

      {/* NAVIGATION BAR */}
      <nav className="gov-nav-bar">
        <div 
          className={`gov-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          {t('nav_dashboard')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          {t('nav_alerts')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'feed' ? 'active' : ''}`}
          onClick={() => setActiveTab('feed')}
        >
          {t('nav_feed')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          {t('nav_trends')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'network' ? 'active' : ''}`}
          onClick={() => setActiveTab('network')}
        >
          {t('nav_network')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'watchlist' ? 'active' : ''}`}
          onClick={() => setActiveTab('watchlist')}
        >
          {t('nav_watchlist')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          {t('nav_reports')}
        </div>

        <div 
          className={`gov-nav-item ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          {t('nav_settings')}
        </div>
      </nav>
    </header>
  );
}

