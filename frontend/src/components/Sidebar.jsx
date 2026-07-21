import React from 'react';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  Rss, 
  TrendingUp, 
  Network, 
  Bell, 
  Eye, 
  FileText, 
  Sliders 
} from 'lucide-react';

const navItems = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard },
  { id: 'feed', label: 'Threat Feed', icon: Rss },
  { id: 'trends', label: 'Trend & Spike Analysis', icon: TrendingUp },
  { id: 'network', label: 'Network & Bot Map', icon: Network },
  { id: 'alerts', label: 'Alert Queue', icon: Bell },
  { id: 'watchlist', label: 'Watchlist Manager', icon: Eye },
  { id: 'reports', label: 'Incident Reports', icon: FileText },
  { id: 'settings', label: 'Analyst Settings', icon: Sliders },
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="sidebar">
      <div className="brand-logo">
        <ShieldAlert />
        <span className="brand-title">SentinelAI</span>
      </div>

      <div className="nav-section-title">INTELLIGENCE MODULES</div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <div
              key={item.id}
              className={`nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </div>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '1rem 0.5rem', borderTop: '1px solid var(--border-color)' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>SYSTEM VERSION</div>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>SentinelAI v1.0 (ERH26_PS_05)</div>
      </div>
    </aside>
  );
}
