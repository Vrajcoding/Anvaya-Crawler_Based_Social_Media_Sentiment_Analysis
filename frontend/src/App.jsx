import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ThreatFeed from './pages/ThreatFeed';
import TrendAnalysis from './pages/TrendAnalysis';
import NetworkView from './pages/NetworkView';
import Alerts from './pages/Alerts';
import Watchlist from './pages/Watchlist';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [liveAlertNotification, setLiveAlertNotification] = useState(null);

  useEffect(() => {
    // Establish WebSocket connection for real-time live alert toast popups
    const ws = new WebSocket('ws://localhost:8000/ws/alerts');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'NEW_ALERT') {
          setLiveAlertNotification(data.data);
          setTimeout(() => setLiveAlertNotification(null), 6000);
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
      default:
        return <Dashboard setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        {/* LIVE REAL-TIME ALERT TOAST POPUP */}
        {liveAlertNotification && (
          <div style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            background: '#090d16',
            border: '2px solid #ef4444',
            boxShadow: '0 0 30px rgba(239,68,68,0.5)',
            borderRadius: '12px',
            padding: '1.25rem',
            zIndex: 100,
            maxWidth: '400px',
            animation: 'slideIn 0.3s ease-out'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontWeight: 800 }}>
              <span>🚨 LIVE THREAT DETECTED</span>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#fff' }}>
              {liveAlertNotification.description}
            </div>
            <button 
              className="btn-primary" 
              style={{ marginTop: '0.75rem', width: '100%', justifyContent: 'center', background: '#ef4444' }}
              onClick={() => setActiveTab('alerts')}
            >
              View In Alert Queue
            </button>
          </div>
        )}

        {renderTabContent()}
      </main>
    </div>
  );
}
