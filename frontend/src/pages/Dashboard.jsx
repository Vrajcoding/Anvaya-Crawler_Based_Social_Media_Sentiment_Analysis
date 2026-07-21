import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import PostCard from '../components/PostCard';
import ThreatBadge from '../components/ThreatBadge';
import AgentStatusPanel from '../components/AgentStatusPanel';
import { fetchStatsOverview, fetchPosts, fetchAlerts } from '../services/api';
import { ShieldAlert, AlertTriangle, Radio, Cpu, ArrowRight, Printer, CheckCircle, BarChart2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useLanguage } from '../services/LanguageContext';

const GOV_COLORS = ['#1e3a8a', '#d97706', '#2563eb', '#dc2626'];
const THREAT_COLORS = ['#16a34a', '#d97706', '#dc2626', '#9333ea'];

export default function Dashboard({ setActiveTab }) {
  const { t } = useLanguage();
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

  const threatBarData = stats?.threat_level_distribution ? [
    { name: 'Neutral', count: stats.threat_level_distribution['Neutral'] || 0 },
    { name: 'Inflammatory', count: stats.threat_level_distribution['Inflammatory'] || 0 },
    { name: 'Fake News', count: stats.threat_level_distribution['Fake News'] || 0 },
    { name: 'Incitement', count: stats.threat_level_distribution['Incitement to Violence'] || 0 },
  ] : [
    { name: 'Neutral', count: 12 },
    { name: 'Inflammatory', count: 5 },
    { name: 'Fake News', count: 4 },
    { name: 'Incitement', count: 3 }
  ];

  const langBarData = stats?.language_distribution ? [
    { lang: 'Gujarati (gu)', posts: stats.language_distribution.gu || 0 },
    { lang: 'Hindi (hi)', posts: stats.language_distribution.hi || 0 },
    { lang: 'English (en)', posts: stats.language_distribution.en || 0 },
    { lang: 'Hinglish', posts: stats.language_distribution.hinglish || 0 },
  ] : [
    { lang: 'Gujarati', posts: 11 },
    { lang: 'Hindi', posts: 7 },
    { lang: 'English', posts: 4 },
    { lang: 'Hinglish', posts: 2 }
  ];

  return (
    <div className="gov-container">
      {/* PAGE BANNER */}
      <div className="page-title-banner">
        <div>
          <h2>{t('nav_dashboard')}</h2>
          <p>{t('portal_subtitle')}</p>
        </div>

        <button className="btn-gov-secondary" onClick={() => window.print()}>
          <Printer size={18} /> {t('btn_sync_data')}
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
            <div className="gov-stat-label">{t('dash_stats_critical')}</div>
          </div>
        </div>

        <div className="gov-stat-card">
          <div className="gov-stat-icon" style={{ background: '#eff6ff', color: '#1e3a8a' }}>
            <Radio size={32} />
          </div>
          <div>
            <div className="gov-stat-number">{stats?.total_monitored_posts || 0}</div>
            <div className="gov-stat-label">{t('dash_stats_monitored')}</div>
          </div>
        </div>

        <div className="gov-stat-card" style={{ borderColor: '#fb923c' }}>
          <div className="gov-stat-icon" style={{ background: '#fff7ed', color: '#c2410c' }}>
            <ShieldAlert size={32} />
          </div>
          <div>
            <div className="gov-stat-number" style={{ color: '#c2410c' }}>{stats?.active_alerts || 0}</div>
            <div className="gov-stat-label">{t('nav_alerts')}</div>
          </div>
        </div>

        <div className="gov-stat-card">
          <div className="gov-stat-icon" style={{ background: '#f3e8ff', color: '#7e22ce' }}>
            <Cpu size={32} />
          </div>
          <div>
            <div className="gov-stat-number" style={{ color: '#7e22ce' }}>{stats?.bot_amplification_count || 0}</div>
            <div className="gov-stat-label">{t('dash_stats_bots')}</div>
          </div>
        </div>
      </div>

      {/* HERMES MULTI-AGENT STATUS TELEMETRY PANEL (HACKATHON WINNING FEATURE) */}
      <AgentStatusPanel />

      {/* TWO COLUMN CONTENT AREA */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        
        {/* LEFT COLUMN: LIVE POST FEED */}
        <div className="gov-card">
          <div className="gov-card-title">
            <span>{t('dash_live_feed_title')}</span>
            <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActiveTab('feed')}>
              {t('filter_all')} <ArrowRight size={16} />
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
              <span>{t('nav_alerts')} ({alerts.length})</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {alerts.length === 0 ? (
                <div style={{ padding: '1rem', color: '#64748b', textAlign: 'center', fontWeight: 600 }}>
                  {t('alert_status_resolved')}
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
                      {t('btn_view_alert')}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* PLATFORM DISTRIBUTION CHART */}
          <div className="gov-card">
            <div className="gov-card-title">
              <span>{t('dash_platform_dist_title')}</span>
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

          {/* THREAT CATEGORY DISTRIBUTION BAR CHART */}
          <div className="gov-card">
            <div className="gov-card-title">
              <span>{t('dash_threat_dist_title')}</span>
            </div>
            <div style={{ height: '180px', width: '100%', marginTop: '0.5rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={threatBarData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={85} tick={{ fontSize: 11, fontWeight: 600 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {threatBarData.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={THREAT_COLORS[index % THREAT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* LANGUAGE & SCRIPT DISTRIBUTION CHART */}
          <div className="gov-card">
            <div className="gov-card-title">
              <span>🇮🇳 क्षेत्रीय भाषा एवं लिपि (Regional Script Dist.)</span>
            </div>
            <div style={{ height: '160px', width: '100%', marginTop: '0.5rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={langBarData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="lang" tick={{ fontSize: 11, fontWeight: 700 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="posts" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

