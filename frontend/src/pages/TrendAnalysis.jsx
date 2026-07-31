import React, { useEffect, useState } from 'react';
import { fetchTrendingHashtags, fetchTrendingKeywords } from '../services/api';
import { TrendingUp, Flame, AlertCircle, Printer } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useLanguage } from '../services/LanguageContext';

export default function TrendAnalysis() {
  const { t } = useLanguage();
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
          <h2>{t('trends_page_title')}</h2>
          <p>{t('trends_page_subtitle')}</p>
        </div>

        <button className="btn-gov-secondary" onClick={() => window.print()}>
          <Printer size={18} /> {t('btn_sync_data')}
        </button>
      </div>

      {/* HASHTAG VOLUME BAR CHART */}
      <div className="gov-card">
        <div className="gov-card-title">
          <span>{t('trends_chart_title')}</span>
        </div>

        <div style={{ height: '280px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hashtags}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-gov)" />
              <XAxis dataKey="hashtag" stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)' }} />
              <YAxis stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--border-gov)', color: 'var(--text-dark)' }} />
              <Bar dataKey="count" fill="var(--gov-navy-light)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* TWO COLUMN BREAKDOWN */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* HASHTAGS SPIKE LIST */}
        <div className="gov-card">
          <div className="gov-card-title" style={{ color: '#fb923c' }}>
            <span>{t('trends_spiking_tags')}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {hashtags.map((h, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-gov)' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--gov-navy-light)' }}>{h.hashtag}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>कुल पोस्ट संख्या: {h.count}</div>
                </div>

                <div>
                  <span style={{ padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, background: h.is_spiking ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)', color: h.is_spiking ? '#fca5a5' : '#86efac', border: `1px solid ${h.is_spiking ? '#ef4444' : '#22c55e'}` }}>
                    SPIKE score: {h.z_score} {h.is_spiking && '🔥 तेजी से फैला'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* KEYWORDS SPIKE LIST */}
        <div className="gov-card">
          <div className="gov-card-title" style={{ color: '#fde047' }}>
            <span>{t('trends_sensitive_keywords')}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {keywords.map((k, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-gov)' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1.05rem', color: '#f59e0b' }}>{k.keyword}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>पहचाने गए संदेश: {k.count}</div>
                </div>

                <div>
                  <span style={{ padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, background: 'rgba(234, 179, 8, 0.2)', color: '#fde047', border: '1px solid #eab308' }}>
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

