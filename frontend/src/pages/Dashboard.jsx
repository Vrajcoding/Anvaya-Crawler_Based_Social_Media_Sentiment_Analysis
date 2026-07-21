import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import PostCard from '../components/PostCard';
import ThreatBadge from '../components/ThreatBadge';
import { fetchStatsOverview, fetchPosts, fetchAlerts } from '../services/api';
import { ShieldAlert, AlertTriangle, Radio, Cpu, ArrowRight, Printer, CheckCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const GOV_COLORS = ['#1e3a8a', '#d97706', '#2563eb', '#dc2626'];

export default function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState(null);
  const [recentPosts, setRecentPosts] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const loadDashboardData = async () => {
    try {
      const statsData = await fetchStatsOverview();
      const postsData = await fetchPosts({ limit: 6 });
      const alertsData = await fetchAlerts('open');
      setStats(statsData);
      setRecentPosts(postsData.items || []);
      setAlerts(alertsData || []);
    } catch (e) {
      console.error(e);
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
    <div className="gov-container">
      {/* PAGE BANNER */}
      <div className="page-title-banner">
        <div>
          <h2>🏠 मुख्य डैशबोर्ड एवं सोशल मीडिया सुरक्षा मॉनिटर</h2>
          <p>National Cyber Threat Intelligence & Multilingual Sentiment Command Center</p>
        </div>

        <button className="btn-gov-secondary" onClick={() => window.print()}>
          <Printer size={18} /> आधिकारिक रिपोर्ट प्रिंट करें (Print Report)
        </button>
      </div>

      {/* STATS GRID FOR POLICE OFFICERS */}
      <div className="gov-stat-grid">
        <div className="gov-stat-card" style={{ borderColor: '#f87171' }}>
          <div className="gov-stat-icon" style={{ background: '#fef2f2', color: '#dc2626' }}>
            <AlertTriangle size={32} />
          </div>
          <div>
            <div className="gov-stat-number" style={{ color: stats?.threat_index_score > 50 ? '#dc2626' : '#166534' }}>
              {stats?.threat_index_score || '0.0'} / 100
            </div>
            <div className="gov-stat-label">राज्य स्तरीय खतरा इंडेक्स (Threat Index)</div>
          </div>
        </div>

        <div className="gov-stat-card">
          <div className="gov-stat-icon" style={{ background: '#eff6ff', color: '#1e3a8a' }}>
            <Radio size={32} />
          </div>
          <div>
            <div className="gov-stat-number">{stats?.total_monitored_posts || 0}</div>
            <div className="gov-stat-label">कुल ट्रैक किए गए संदेश (Total Monitored)</div>
          </div>
        </div>

        <div className="gov-stat-card" style={{ borderColor: '#fb923c' }}>
          <div className="gov-stat-icon" style={{ background: '#fff7ed', color: '#c2410c' }}>
            <ShieldAlert size={32} />
          </div>
          <div>
            <div className="gov-stat-number" style={{ color: '#c2410c' }}>{stats?.active_alerts || 0}</div>
            <div className="gov-stat-label">जरूरी आपातकालीन अलर्ट (Critical Alerts)</div>
          </div>
        </div>

        <div className="gov-stat-card">
          <div className="gov-stat-icon" style={{ background: '#f3e8ff', color: '#7e22ce' }}>
            <Cpu size={32} />
          </div>
          <div>
            <div className="gov-stat-number" style={{ color: '#7e22ce' }}>{stats?.bot_amplification_count || 0}</div>
            <div className="gov-stat-label">बॉट व संदिग्ध गैंग नेटवर्क (Bot Clusters)</div>
          </div>
        </div>
      </div>

      {/* TWO COLUMN CONTENT AREA */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        
        {/* LEFT COLUMN: LIVE POST FEED */}
        <div className="gov-card">
          <div className="gov-card-title">
            <span>📰 लाइव सोशल मीडिया संदेश (Recent Social Posts Stream)</span>
            <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActiveTab('feed')}>
              सभी संदेश देखें (View All) <ArrowRight size={16} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {recentPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: CRITICAL ALERTS & PLATFORM BREAKDOWN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* HIGH PRIORITY ALERTS */}
          <div className="gov-card" style={{ borderColor: '#f87171' }}>
            <div className="gov-card-title" style={{ color: '#dc2626' }}>
              <span>🚨 अति-संवेदनशील अलर्ट ({alerts.length})</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {alerts.length === 0 ? (
                <div style={{ padding: '1rem', color: '#64748b', textAlign: 'center', fontWeight: 600 }}>
                  वर्तमान में कोई नया आपातकालीन अलर्ट नहीं है। (No active alerts)
                </div>
              ) : (
                alerts.slice(0, 4).map((alert) => (
                  <div key={alert.id} style={{ background: '#fef2f2', border: '1px solid #f87171', borderRadius: '8px', padding: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 800, color: '#991b1b', fontSize: '0.95rem' }}>
                      <span>{alert.severity}: {alert.threat_type}</span>
                    </div>
                    <p style={{ marginTop: '0.4rem', fontSize: '0.95rem', color: '#1e293b', fontWeight: 600 }}>
                      {alert.description}
                    </p>
                    <button 
                      className="btn-gov-danger" 
                      style={{ marginTop: '0.75rem', padding: '0.3rem 0.8rem', fontSize: '0.8rem', width: '100%', justifyContent: 'center' }}
                      onClick={() => setActiveTab('alerts')}
                    >
                      कार्रवाई करें (Take Action)
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* PLATFORM DISTRIBUTION CHART */}
          <div className="gov-card">
            <div className="gov-card-title">
              <span>📊 प्लेटफ़ॉर्म कवरेज (Platform Share)</span>
            </div>

            <div style={{ height: '200px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={GOV_COLORS[index % GOV_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '0.9rem', fontWeight: 700, color: 'var(--gov-navy-dark)' }}>
              <span>𝕏 X (Twitter)</span>
              <span>📸 IG</span>
              <span>📘 FB</span>
              <span>▶️ YT</span>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
