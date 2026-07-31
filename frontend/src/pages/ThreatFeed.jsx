import React, { useState, useEffect } from 'react';
import PostCard from '../components/PostCard';
import { fetchPosts, analyzeCustomText } from '../services/api';
import { Filter, Search, Send, Sparkles, AlertCircle } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function ThreatFeed() {
  const { t } = useLanguage();
  const [posts, setPosts] = useState([]);
  const [platform, setPlatform] = useState('all');
  const [threatLevel, setThreatLevel] = useState('all');
  const [language, setLanguage] = useState('all');
  const [query, setQuery] = useState('');
  
  // Custom analyze tester
  const [customText, setCustomText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const loadPosts = async () => {
    try {
      const data = await fetchPosts({
        platform,
        threat_level: threatLevel,
        language,
        query: query || undefined,
        limit: 50
      });
      setPosts(data.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadPosts();
  }, [platform, threatLevel, language, query]);

  const handleCustomAnalyze = async (e) => {
    e.preventDefault();
    if (!customText.trim()) return;
    setAnalyzing(true);
    try {
      const res = await analyzeCustomText({ text: customText });
      setAnalysisResult(res.post);
      setCustomText('');
      loadPosts();
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>{t('feed_page_title')}</h2>
          <p>{t('feed_page_subtitle')}</p>
        </div>
      </div>

      {/* QUICK PRESET SEARCH BUTTONS FOR POLICE OFFICERS */}
      <div className="gov-card" style={{ background: 'var(--bg-card-alt)', borderLeft: '6px solid var(--gov-gold)' }}>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-dark)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Search size={18} color="var(--gov-gold)" /> {t('preset_quick_search')}
        </h4>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('सुरत')}>
            {t('preset_surat')}
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('પથ્થરમારો')}>
            {t('preset_stone_pelting')}
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('जहर')}>
            {t('preset_water_poison')}
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('દંગા')}>
            {t('preset_riots_call')}
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('')}>
            🔄 {t('filter_all')}
          </button>
        </div>
      </div>

      {/* CUSTOM SUSPICIOUS TEXT TESTER */}
      <div className="gov-card" style={{ border: '2px solid var(--gov-navy-light)' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-dark)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles color="var(--gov-navy-light)" size={20} /> {t('test_text_title')}
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {t('test_text_desc')}
        </p>

        <form onSubmit={handleCustomAnalyze} style={{ display: 'flex', gap: '0.75rem' }}>
          <input 
            type="text" 
            placeholder={t('test_text_placeholder')}
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            style={{ flex: 1, border: '2px solid var(--border-gov)', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '1rem', outline: 'none' }}
          />
          <button type="submit" className="btn-gov-primary" disabled={analyzing}>
            <Send size={18} />
            <span>{analyzing ? t('btn_analyzing') : t('btn_analyze')}</span>
          </button>
        </form>

        {analysisResult && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(34, 197, 94, 0.15)', borderRadius: '8px', border: '2px solid #22c55e' }}>
            <h4 style={{ color: '#4ade80', marginBottom: '0.5rem' }}>✅ {t('analysis_complete')}</h4>
            <PostCard post={analysisResult} />
          </div>
        )}
      </div>

      {/* FILTERS CONTROL BAR */}
      <div className="gov-card" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={18} color="var(--gov-navy-light)" />
          <strong style={{ fontSize: '0.95rem' }}>{t('label_platform')}</strong>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem', fontWeight: 600 }}>
            <option value="all">{t('all_platforms')}</option>
            <option value="x">X (Twitter)</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="youtube">YouTube</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <strong style={{ fontSize: '0.95rem' }}>{t('label_threat_level')}</strong>
          <select value={threatLevel} onChange={(e) => setThreatLevel(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem', fontWeight: 600 }}>
            <option value="all">{t('filter_all')}</option>
            <option value="Incitement to Violence">{t('filter_incitement')}</option>
            <option value="Fake News">{t('filter_fakenews')}</option>
            <option value="Inflammatory">{t('inflammatory')}</option>
            <option value="Neutral">{t('neutral')}</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <strong style={{ fontSize: '0.95rem' }}>{t('label_language')}</strong>
          <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem', fontWeight: 600 }}>
            <option value="all">{t('all_languages')}</option>
            <option value="gu">ગુજરાતી (Gujarati)</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="hinglish">Hinglish</option>
            <option value="en">English</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Search size={18} color="var(--text-muted)" />
          <input 
            type="text" 
            placeholder={t('search_placeholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ padding: '0.5rem 0.85rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem' }}
          />
        </div>
      </div>

      {/* POSTS LIST */}
      <div>
        {posts.length === 0 ? (
          <div className="gov-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            {t('no_posts_found')}
          </div>
        ) : (
          posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))
        )}
      </div>

    </div>
  );
}

