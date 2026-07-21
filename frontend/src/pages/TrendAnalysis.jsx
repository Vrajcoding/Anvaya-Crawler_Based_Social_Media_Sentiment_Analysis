import React, { useEffect, useState } from 'react';
import { fetchTrendingHashtags, fetchTrendingKeywords } from '../services/api';
import { TrendingUp, Flame, AlertCircle, Printer } from 'lucide-react';
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
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>📈 अफवाहें एवं ट्रेंड विश्लेषण (Social Rumors & Spike Anomaly Tracker)</h2>
          <p>क्षेत्रीय हैशटैग, भड़काऊ कीवर्ड एवं अपरिमेय उछाल (Z-score spike) का स्वचालित मापन</p>
        </div>

        <button className="btn-gov-secondary" onClick={() => window.print()}>
          <Printer size={18} /> प्रिंट रिपोर्ट (Print)
        </button>
      </div>

      {/* HASHTAG VOLUME BAR CHART */}
      <div className="gov-card">
        <div className="gov-card-title">
          <span>📊 ट्रेंडिंग हैशटैग आयतन (Trending Hashtag Volume Velocity)</span>
        </div>

        <div style={{ height: '280px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hashtags}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="hashtag" stroke="#1e293b" />
              <YAxis stroke="#1e293b" />
              <Tooltip />
              <Bar dataKey="count" fill="var(--gov-navy)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* TWO COLUMN BREAKDOWN */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* HASHTAGS SPIKE LIST */}
        <div className="gov-card">
          <div className="gov-card-title" style={{ color: '#c2410c' }}>
            <span>🔥 तेजी से फैलते हैशटैग (High Velocity Hashtags)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {hashtags.map((h, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-gov)' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--gov-navy)' }}>{h.hashtag}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>कुल पोस्ट संख्या: {h.count}</div>
                </div>

                <div>
                  <span style={{ padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, background: h.is_spiking ? '#fef2f2' : '#f0fdf4', color: h.is_spiking ? '#dc2626' : '#166534', border: `1px solid ${h.is_spiking ? '#f87171' : '#4ade80'}` }}>
                    SPIKE score: {h.z_score} {h.is_spiking && '🔥 तेजी से फैला'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* KEYWORDS SPIKE LIST */}
        <div className="gov-card">
          <div className="gov-card-title" style={{ color: 'var(--gov-navy-dark)' }}>
            <span>⚠️ निगरानी योग्य संवेदनशील शब्द (High Risk Keywords)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {keywords.map((k, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-gov)' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1.05rem', color: '#b45309' }}>{k.keyword}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>पहचाने गए संदेश: {k.count}</div>
                </div>

                <div>
                  <span style={{ padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, background: '#fefce8', color: '#a16207', border: '1px solid #facc15' }}>
                    गंभीरता (Anomaly Rating): {k.z_score}
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
