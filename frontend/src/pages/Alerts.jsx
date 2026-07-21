import React, { useEffect, useState } from 'react';
import { fetchAlerts, acknowledgeAlert, resolveAlert } from '../services/api';
import { Bell, CheckCircle, AlertOctagon, Clock, ShieldAlert } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function Alerts() {
  const { t } = useLanguage();
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('open');

  const loadAlerts = async () => {
    try {
      const data = await fetchAlerts(filter);
      setAlerts(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const handleAck = async (id) => {
    await acknowledgeAlert(id);
    loadAlerts();
  };

  const handleResolve = async (id) => {
    await resolveAlert(id);
    loadAlerts();
  };

  return (
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>{t('alerts_page_title')}</h2>
          <p>{t('alerts_page_subtitle')}</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button 
          className={`btn-gov-secondary ${filter === 'open' ? 'btn-gov-primary' : ''}`} 
          onClick={() => setFilter('open')}
        >
          🚨 {t('alert_status_open')} ({alerts.filter(a => a.status === 'open').length})
        </button>
        <button 
          className={`btn-gov-secondary ${filter === 'acknowledged' ? 'btn-gov-primary' : ''}`} 
          onClick={() => setFilter('acknowledged')}
        >
          👁️ {t('alert_status_ack')}
        </button>
        <button 
          className={`btn-gov-secondary ${filter === 'resolved' ? 'btn-gov-primary' : ''}`} 
          onClick={() => setFilter('resolved')}
        >
          ✅ {t('alert_status_resolved')}
        </button>
        <button 
          className={`btn-gov-secondary ${filter === 'all' ? 'btn-gov-primary' : ''}`} 
          onClick={() => setFilter('all')}
        >
          📋 {t('filter_all')}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {alerts.length === 0 ? (
          <div className="gov-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            {t('alert_status_resolved')}
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="gov-card" style={{ borderLeft: `8px solid ${alert.severity === 'CRITICAL' ? '#dc2626' : '#c2410c'}`, background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontWeight: 800, color: alert.severity === 'CRITICAL' ? '#dc2626' : '#c2410c', fontSize: '1.2rem' }}>
                      🚨 {alert.severity}: {alert.threat_type}
                    </span>
                    <span style={{ background: '#f1f5f9', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 800, color: '#475569' }}>
                      {alert.status.toUpperCase()}
                    </span>
                  </div>

                  <p style={{ marginTop: '0.6rem', color: '#0f172a', fontSize: '1.1rem', fontWeight: 600 }}>
                    {alert.description}
                  </p>

                  <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                    <Clock size={14} /> {new Date(alert.created_at).toLocaleString()}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  {alert.status === 'open' && (
                    <button className="btn-gov-secondary" style={{ padding: '0.6rem 1.25rem' }} onClick={() => handleAck(alert.id)}>
                      {t('btn_ack')}
                    </button>
                  )}
                  {alert.status !== 'resolved' && (
                    <button className="btn-gov-primary" style={{ padding: '0.6rem 1.25rem', background: '#166534', borderColor: '#166534' }} onClick={() => handleResolve(alert.id)}>
                      <CheckCircle size={18} /> {t('btn_resolve')}
                    </button>
                  )}
                </div>

              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

