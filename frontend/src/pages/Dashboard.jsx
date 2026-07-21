import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import PostCard from '../components/PostCard';
import ThreatBadge from '../components/ThreatBadge';
import { fetchStatsOverview, fetchPosts, fetchAlerts } from '../services/api';
import { ShieldAlert, AlertTriangle, Cpu, Radio, Activity } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['#3b82f6', '#ec4899', '#1877f2', '#ff0000'];

export default function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState(null);
  const [recentPosts, setRecentPosts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    try {
      const statsData = await fetchStatsOverview();
      const postsData = await fetchPosts({ limit: 5 });
      const alertsData = await fetchAlerts('open');
      setStats(statsData);
      setRecentPosts(postsData.items || []);
      setAlerts(alertsData || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 8000);
    return () => clearInterval(interval);
  }, []);

  const pieData = stats?.platform_distribution ? [
    { name: 'X (Twitter)', value: stats.platform_distribution.x || 0 },
    { name: 'Instagram', value: stats.platform_distribution.instagram || 0 },
    { name: 'Facebook', value: stats.platform_distribution.facebook || 0 },
    { name: 'YouTube', value: stats.platform_distribution.youtube || 0 },
  ] : [];

  return (
    <div>
      <Header 
        title="OSINT Cyber Threat Command Center" 
        subtitle="Real-time multi-platform threat monitoring, sentiment analysis & bot detection"
        onRefresh={loadDashboardData}
      />

      {/* STATS GRID */}
      <div className="stat-grid">
        <div className="card-glass stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>THREAT INDEX SCORE</div>
            <div className="stat-val" style={{ color: stats?.threat_index_score > 50 ? '#ef4444' : '#22c55e' }}>
              {stats?.threat_index_score || '0.0'} / 100
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Composite Threat Level</div>
          </div>
          <div className="stat-icon" style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}>
            <AlertTriangle color="#ef4444" size={24} />
          </div>
        </div>

        <div className="card-glass stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>MONITORED POSTS</div>
            <div className="stat-val">{stats?.total_monitored_posts || 0}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Near real-time stream</div>
          </div>
          <div className="stat-icon">
            <Radio color="var(--accent-cyan)" size={24} />
          </div>
        </div>

        <div className="card-glass stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>ACTIVE CRITICAL ALERTS</div>
            <div className="stat-val" style={{ color: '#f97316' }}>{stats?.active_alerts || 0}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Action required</div>
          </div>
          <div className="stat-icon">
            <ShieldAlert color="#f97316" size={24} />
          </div>
        </div>

        <div className="card-glass stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>BOT NETWORKS DETECTED</div>
            <div className="stat-val" style={{ color: '#a855f7' }}>{stats?.bot_amplification_count || 0}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Coordinated clusters</div>
          </div>
          <div className="stat-icon">
            <Cpu color="#a855f7" size={24} />
          </div>
        </div>
      </div>

      {/* MAIN TWO-COLUMN DASHBOARD CONTENT */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        
        {/* LEFT COLUMN: RECENT HIGH-RISK THREAT FEED */}
        <div className="card-glass">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity color="var(--accent-cyan)" size={20} /> Live Social Threat Ingestion Feed
            </h2>
            <button className="btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActiveTab('feed')}>
              View Full Feed →
            </button>
          </div>

          <div className="feed-list">
            {recentPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: ANALYTICS & PLATFORM BREAKDOWN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* PLATFORM DISTRIBUTION CHART */}
          <div className="card-glass">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Platform Coverage</h3>
            <div style={{ height: '220px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <span>𝕏 X (Twitter)</span>
              <span>📸 IG</span>
              <span>📘 FB</span>
              <span>▶️ YT</span>
            </div>
          </div>

          {/* ACTIVE HIGH-PRIORITY ALERTS QUEUE */}
          <div className="card-glass">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertTriangle size={18} /> High-Severity Alerts ({alerts.length})
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {alerts.length === 0 ? (
                <div style={{ color: 'var(--text-dim)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>
                  No open high-severity alerts.
                </div>
              ) : (
                alerts.slice(0, 4).map((alert) => (
                  <div key={alert.id} style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 700, color: '#fca5a5' }}>
                      <span>{alert.severity} • {alert.threat_type}</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', marginTop: '4px', color: '#e2e8f0' }}>
                      {alert.description}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
