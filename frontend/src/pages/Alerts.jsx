import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import { fetchAlerts, acknowledgeAlert, resolveAlert } from '../services/api';
import { Bell, CheckCircle, AlertOctagon, Clock } from 'lucide-react';

export default function Alerts() {
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
    <div>
      <Header 
        title="High-Severity Alert Center" 
        subtitle="Real-time incident alert queue and analyst resolution workflow"
        onRefresh={loadAlerts}
      />

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <button 
          className={`btn-secondary ${filter === 'open' ? 'btn-primary' : ''}`} 
          onClick={() => setFilter('open')}
        >
          Open Alerts ({alerts.filter(a => a.status === 'open').length})
        </button>
        <button 
          className={`btn-secondary ${filter === 'acknowledged' ? 'btn-primary' : ''}`} 
          onClick={() => setFilter('acknowledged')}
        >
          Acknowledged
        </button>
        <button 
          className={`btn-secondary ${filter === 'resolved' ? 'btn-primary' : ''}`} 
          onClick={() => setFilter('resolved')}
        >
          Resolved
        </button>
        <button 
          className={`btn-secondary ${filter === 'all' ? 'btn-primary' : ''}`} 
          onClick={() => setFilter('all')}
        >
          All History
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {alerts.length === 0 ? (
          <div className="card-glass" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>
            No alerts found for this status.
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="card-glass" style={{ borderLeft: `6px solid ${alert.severity === 'CRITICAL' ? '#ef4444' : '#f97316'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, color: alert.severity === 'CRITICAL' ? '#ef4444' : '#f97316', fontSize: '1.1rem' }}>
                      {alert.severity}: {alert.threat_type}
                    </span>
                    <span style={{ background: '#1e293b', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      STATUS: {alert.status.toUpperCase()}
                    </span>
                  </div>

                  <p style={{ marginTop: '0.5rem', color: '#e2e8f0', fontSize: '0.95rem' }}>
                    {alert.description}
                  </p>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> Triggered At: {new Date(alert.created_at).toLocaleString()}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {alert.status === 'open' && (
                    <button className="btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => handleAck(alert.id)}>
                      Acknowledge
                    </button>
                  )}
                  {alert.status !== 'resolved' && (
                    <button className="btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => handleResolve(alert.id)}>
                      <CheckCircle size={14} /> Resolve Alert
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
