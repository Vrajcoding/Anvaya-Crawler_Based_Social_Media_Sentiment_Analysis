import React from 'react';
import { Activity, Bell, RefreshCw } from 'lucide-react';

export default function Header({ title, subtitle, onRefresh }) {
  return (
    <header className="header-bar">
      <div className="page-header-title">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn-secondary" onClick={onRefresh}>
          <RefreshCw size={16} />
          <span>Sync</span>
        </button>

        <div className="header-status-badge">
          <div className="pulse-dot"></div>
          <span>LIVE INGESTION ACTIVE</span>
        </div>
      </div>
    </header>
  );
}
