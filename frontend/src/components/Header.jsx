import React, { useState, useEffect } from 'react';
import { Shield, PhoneCall, UserCheck, RefreshCw, ChevronDown, Moon, Sun } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

// Import custom PNG assets
import thunderIcon from '../assets/thunder.png';
import houseIcon from '../assets/house.png';
import sateliteIcon from '../assets/satelite.png';
import operationIcon from '../assets/operation.png';
import documentsIcon from '../assets/documents.png';
import growthIcon from '../assets/growth.png';
import socialmediaIcon from '../assets/socialmedia.png';
import criticalareaIcon from '../assets/criticalarea.png';
import targetwatchlistIcon from '../assets/targetwatchlist.png';

export default function Header({ activeTab, setActiveTab, onRefresh }) {
  const { lang, setLang, t } = useLanguage();
  const [fontSize, setFontSize] = useState('normal');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [openDropdown, setOpenDropdown] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const toggleFontSize = () => {
    if (fontSize === 'normal') setFontSize('large');
    else setFontSize('normal');
    document.body.classList.toggle('font-lg');
  };

  const handleNavClick = (tab) => {
    setActiveTab(tab);
    setOpenDropdown(null);
  };

  return (
    <header>
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
          <button
            onClick={toggleTheme}
            style={{
              background: theme === 'dark' ? '#1e293b' : '#3b82f6',
              border: '1px solid #fde047',
              color: '#fff',
              padding: '0.3rem 0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 0 10px rgba(253, 224, 71, 0.25)',
              transition: 'all 0.2s ease'
            }}
          >
            {theme === 'dark' ? <><Moon size={15} color="#fde047" /> <span>Dark</span></> : <><Sun size={15} color="#fde047" /> <span>Light</span></>}
          </button>

          <button 
            onClick={toggleFontSize} 
            style={{ background: 'transparent', border: '1px solid #475569', color: '#fff', padding: '0.25rem 0.6rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700 }}
          >
            {fontSize === 'normal' ? t('text_size_large') : t('text_size_normal')}
          </button>

          <select 
            value={lang} 
            onChange={(e) => setLang(e.target.value)}
            style={{ background: '#1e293b', color: '#fff', border: '1px solid #fde047', padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, cursor: 'pointer' }}
          >
            <option value="en">🌐 English</option>
            <option value="hi">🇮🇳 हिंदी</option>
            <option value="gu">🇮🇳 ગુજરાતી</option>
          </select>
        </div>
      </div>

      <div className="gov-emblem-section">
        <div className="emblem-brand">
          <div className="emblem-icon"><Shield size={32} color="#fde047" /></div>
          <div className="emblem-title">
            <h1>{t('portal_title')}</h1>
            <p>{t('portal_subtitle')}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>{t('on_duty_label')}</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-dark)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <UserCheck size={18} color="var(--gov-navy-light)" /> {t('duty_officer_name')}
            </div>
          </div>
          <button className="btn-gov-secondary" onClick={onRefresh} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            <RefreshCw size={16} />
            <span>{t('btn_sync_data')}</span>
          </button>
        </div>
      </div>

      <nav className="gov-nav-bar" style={{ display: 'flex', position: 'relative' }} onMouseLeave={() => setOpenDropdown(null)}>

        <div
          className={`gov-nav-item ${activeTab === 'crawl' ? 'active' : ''}`}
          onClick={() => handleNavClick('crawl')}
          style={activeTab === 'crawl' ? { background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)', color: '#fff', borderRadius: '6px', borderBottom: '4px solid #8b5cf6', display: 'flex', alignItems: 'center', gap: '0.6rem' } : { display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        >
          <img src={thunderIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          <span>{t('nav_crawl')}</span>
        </div>

        <div
          className={`gov-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => handleNavClick('dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        >
          <img src={houseIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          <span>{t('nav_dashboard')}</span>
        </div>

        <div
          className={`gov-nav-item has-dropdown ${['feed', 'trends', 'network', 'map'].includes(activeTab) ? 'dropdown-active' : ''}`}
          onMouseEnter={() => setOpenDropdown('intel')}
          onClick={() => setOpenDropdown(openDropdown === 'intel' ? null : 'intel')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        >
          <img src={sateliteIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          <span>{t('nav_intelligence')}</span>
          <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: openDropdown === 'intel' ? 'rotate(180deg)' : 'rotate(0deg)' }} />
          {openDropdown === 'intel' && (
            <div className="nav-dropdown">
              <div className={activeTab === 'feed' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); handleNavClick('feed'); }} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <img src={socialmediaIcon} alt="" style={{ width: '18px', height: '18px', objectFit: 'contain' }} />
                <span>{t('nav_feed')}</span>
              </div>
              <div className={activeTab === 'trends' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); handleNavClick('trends'); }} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <img src={growthIcon} alt="" style={{ width: '18px', height: '18px', objectFit: 'contain' }} />
                <span>{t('nav_trends')}</span>
              </div>
              <div className={activeTab === 'network' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); handleNavClick('network'); }} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <span style={{ fontSize: '1rem' }}>🕸️</span>
                <span>Network Graph</span>
              </div>
              <div className={activeTab === 'map' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); handleNavClick('map'); }} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <span style={{ fontSize: '1rem' }}>🗺️</span>
                <span>Risk Map</span>
              </div>
            </div>
          )}
        </div>

        <div
          className={`gov-nav-item has-dropdown ${['alerts', 'watchlist'].includes(activeTab) ? 'dropdown-active' : ''}`}
          onMouseEnter={() => setOpenDropdown('ops')}
          onClick={() => setOpenDropdown(openDropdown === 'ops' ? null : 'ops')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        >
          <img src={operationIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          <span>{t('nav_operations')}</span>
          <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: openDropdown === 'ops' ? 'rotate(180deg)' : 'rotate(0deg)' }} />
          {openDropdown === 'ops' && (
            <div className="nav-dropdown">
              <div className={activeTab === 'alerts' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); handleNavClick('alerts'); }} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <img src={criticalareaIcon} alt="" style={{ width: '18px', height: '18px', objectFit: 'contain' }} />
                <span>{t('nav_alerts')}</span>
              </div>
              <div className={activeTab === 'watchlist' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); handleNavClick('watchlist'); }} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <img src={targetwatchlistIcon} alt="" style={{ width: '18px', height: '18px', objectFit: 'contain' }} />
                <span>{t('nav_watchlist')}</span>
              </div>
            </div>
          )}
        </div>

        <div
          className={`gov-nav-item ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => handleNavClick('reports')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        >
          <img src={documentsIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          <span>{t('nav_reports')}</span>
        </div>

        <div
          className={`gov-nav-item ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => handleNavClick('settings')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        >
          <img src={operationIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          <span>{t('nav_settings')}</span>
        </div>

      </nav>
    </header>
  );
}
