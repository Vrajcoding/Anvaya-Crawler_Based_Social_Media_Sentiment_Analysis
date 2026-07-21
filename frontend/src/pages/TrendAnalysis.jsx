import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import { fetchTrendingHashtags, fetchTrendingKeywords } from '../services/api';
import { TrendingUp, Flame, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function TrendAnalysis() {
  const [hashtags, setHashtags] = useState([]);
  const [keywords, setKeywords] = useState([]);

  const loadTrends = async () => {
    try {
      const tagData = await fetchTrendingHashtags();
      const kwData = await fetchTrendingKeywords();
      setHashtags(tagData || []);
      setKeywords(kwData || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadTrends();
  }, []);

  return (
    <div>
      <Header 
        title="Trend & Spike Anomaly Analysis" 
        subtitle="Tracking high-velocity regional keywords, viral hashtags, and Z-score spike anomalies"
        onRefresh={loadTrends}
      />

      {/* TOP CHART BAR */}
      <div className="card-glass" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp color="var(--accent-cyan)" size={20} /> Regional Hashtag Velocity & Volume
        </h3>

        <div style={{ height: '300px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hashtags}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hashtag" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155' }} />
              <Bar dataKey="count" fill="var(--accent-cyan)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* TWO COLUMN TREND BREAKDOWN */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* HASHTAGS SPIKE LIST */}
        <div className="card-glass">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Flame color="#f97316" size={20} /> Spiking Hashtags (Z-Score &gt; 2.0)
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {hashtags.map((h, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1e293b', padding: '0.85rem 1rem', borderRadius: '8px' }}>
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{h.hashtag}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Volume: {h.count} posts</div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, background: h.is_spiking ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)', color: h.is_spiking ? '#ef4444' : '#22c55e' }}>
                    Z-SCORE: {h.z_score} {h.is_spiking && '🔥 SPIKE'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* KEYWORDS SPIKE LIST */}
        <div className="card-glass">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle color="#eab308" size={20} /> High-Risk Keywords Monitored
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {keywords.map((k, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1e293b', padding: '0.85rem 1rem', borderRadius: '8px' }}>
                <div>
                  <div style={{ fontWeight: 700, color: '#fde047' }}>{k.keyword}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Occurrences: {k.count}</div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, background: 'rgba(234,179,8,0.2)', color: '#fde047' }}>
                    SPIKE METRIC: {k.z_score}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
