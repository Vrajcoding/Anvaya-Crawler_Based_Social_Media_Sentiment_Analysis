import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import ThreatFeed from './pages/ThreatFeed';
import TrendAnalysis from './pages/TrendAnalysis';
import NetworkView from './pages/NetworkView';
import Alerts from './pages/Alerts';
import Watchlist from './pages/Watchlist';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import PromptCrawler from './components/PromptCrawler';
import { AlertOctagon, X } from 'lucide-react';
import { useLanguage } from './services/LanguageContext';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [liveAlertNotification, setLiveAlertNotification] = useState(null);
  const { t } = useLanguage();


  useEffect(() => {
    // Establish WebSocket connection for real-time live alert toast popups
    const ws = new WebSocket('ws://localhost:8000/ws/alerts');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'NEW_ALERT') {
          setLiveAlertNotification(data.data);
        }
      } catch (e) {
        console.error(e);
      }
    };

    return () => ws.close();
  }, []);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={setActiveTab} />;
      case 'feed':
        return <ThreatFeed />;
      case 'trends':
        return <TrendAnalysis />;
      case 'network':
        return <NetworkView />;
      case 'alerts':
        return <Alerts />;
      case 'watchlist':
        return <Watchlist />;
      case 'reports':
        return <Reports />;
      case 'settings':
        return <Settings />;
      case 'crawl':
        return <PromptCrawler />;
      default:
        return <Dashboard setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div style={{ background: 'var(--bg-main)', color: 'var(--text-dark)', minHeight: '100vh', transition: 'background-color 0.3s ease, color 0.3s ease' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onRefresh={() => window.location.reload()} />
      
      {/* HIGH VISIBILITY EMERGENCY ALERT BANNER FOR POLICE OFFICERS */}
      {liveAlertNotification && (
        <div style={{
          background: '#dc2626',
          color: '#ffffff',
          padding: '1rem 2rem',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          boxShadow: '0 4px 12px rgba(220, 38, 38, 0.4)',
          position: 'sticky',
          top: 0,
          zIndex: 1000
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <AlertOctagon size={28} />
            <div>
              <strong style={{ fontSize: '1.15rem' }}>{t('emergency_banner_title')}</strong>
              <span style={{ marginLeft: '10px', fontSize: '1.05rem', fontWeight: 600 }}>{liveAlertNotification.description}</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button 
              className="btn-gov-secondary" 
              style={{ padding: '0.4rem 1rem', fontSize: '0.9rem', background: '#fff', color: '#dc2626', borderColor: '#fff' }}
              onClick={() => {
                setActiveTab('alerts');
                setLiveAlertNotification(null);
              }}
            >
              {t('btn_view_alert')}
            </button>

            <button 
              onClick={() => setLiveAlertNotification(null)}
              style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}
            >
              <X size={24} />
            </button>
          </div>
        </div>
      )}

      {renderTabContent()}
    </div>
  );
}
