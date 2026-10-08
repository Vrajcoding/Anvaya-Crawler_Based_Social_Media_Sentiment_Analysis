import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import ThreatFeed from './pages/ThreatFeed';
import TrendAnalysis from './pages/TrendAnalysis';
import Alerts from './pages/Alerts';
import Watchlist from './pages/Watchlist';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import PromptCrawler from './components/PromptCrawler';
import NetworkGraph from './pages/NetworkGraph';
import MapView from './pages/MapView';
import { AlertOctagon, X } from 'lucide-react';
import { useLanguage } from './services/LanguageContext';

export default function App() {
  const [activeTab, setActiveTab] = useState('crawl');
  const [liveAlertNotification, setLiveAlertNotification] = useState(null);
  const { t } = useLanguage();

  useEffect(() => {
    // Establish WebSocket connection for real-time live alert toast popups
    let ws;
    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws/alerts');

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Handle both NEW_ALERT (from real scoring) and NEW_POST broadcasts
          if (data.type === 'NEW_ALERT') {
            setLiveAlertNotification(data.data);
          }
        } catch (e) {
          console.error(e);
        }
      };

      ws.onclose = () => {
        // Reconnect after 3 seconds
        setTimeout(connect, 3000);
      };
    };

    connect();
    return () => ws && ws.close();
  }, []);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={setActiveTab} />;
      case 'feed':
        return <ThreatFeed />;
      case 'trends':
        return <TrendAnalysis />;
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
      case 'network':
        return <NetworkGraph />;
      case 'map':
        return <MapView />;
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
          background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
          color: '#ffffff',
          padding: '0.9rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 4px 20px rgba(220, 38, 38, 0.5)',
          position: 'sticky',
          top: 0,
          zIndex: 1000,
          animation: 'slideDown 0.3s ease',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <AlertOctagon size={28} style={{ animation: 'pulse 1s infinite' }} />
            <div>
              <strong style={{ fontSize: '1.1rem' }}>
                🚨 {liveAlertNotification.severity} ALERT — {liveAlertNotification.platform?.toUpperCase()}
              </strong>
              {liveAlertNotification.district && (
                <span style={{ marginLeft: '8px', fontSize: '0.9rem', opacity: 0.9 }}>
                  📍 {liveAlertNotification.district}
                </span>
              )}
              <span style={{ marginLeft: '10px', fontSize: '0.95rem', fontWeight: 500 }}>
                {liveAlertNotification.description?.slice(0, 120)}…
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexShrink: 0 }}>
            <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>
              Score: {(liveAlertNotification.threat_score * 100)?.toFixed(0)}%
            </span>
            <button
              style={{ padding: '0.4rem 1rem', fontSize: '0.85rem', background: '#fff', color: '#dc2626', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
              onClick={() => {
                setActiveTab('alerts');
                setLiveAlertNotification(null);
              }}
            >
              View Alert
            </button>
            <button
              onClick={() => setLiveAlertNotification(null)}
              style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}
            >
              <X size={22} />
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideDown {
          from { transform: translateY(-100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>

      {renderTabContent()}
    </div>
  );
}
