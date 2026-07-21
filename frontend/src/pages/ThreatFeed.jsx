import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import PostCard from '../components/PostCard';
import { fetchPosts, analyzeCustomText } from '../services/api';
import { Filter, Search, Send, Sparkles } from 'lucide-react';

export default function ThreatFeed() {
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
    <div>
      <Header 
        title="Multilingual Threat Feed" 
        subtitle="Filterable social posts with local-language Gujarati, Hindi, and Hinglish NLP breakdown"
        onRefresh={loadPosts}
      />

      {/* ANALYST TESTER TOOL */}
      <div className="card-glass" style={{ marginBottom: '1.5rem', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%)', borderColor: 'var(--accent-cyan)' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} /> Test Real-time NLP Threat Classifier
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Enter any sample text in Gujarati, Hindi, Hinglish, or English to test classification, transliteration, and threat scoring.
        </p>

        <form onSubmit={handleCustomAnalyze} style={{ display: 'flex', gap: '0.75rem' }}>
          <input 
            type="text" 
            placeholder="e.g. કાલે ચોક બજારમાં ઈંટ પથ્થર લઈને ભેગા થાઓ... OR kal 10 baje petrol bomb leke aao!"
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            style={{ flex: 1, background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.75rem 1rem', borderRadius: '8px', outline: 'none' }}
          />
          <button type="submit" className="btn-primary" disabled={analyzing}>
            <Send size={16} />
            <span>{analyzing ? 'Analyzing...' : 'Run NLP Classifier'}</span>
          </button>
        </form>

        {analysisResult && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#090d16', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.9rem', color: '#4ade80', marginBottom: '0.5rem' }}>✅ Classification Complete:</h4>
            <PostCard post={analysisResult} />
          </div>
        )}
      </div>

      {/* FILTERS BAR */}
      <div className="filter-bar">
        <div className="filter-group">
          <Filter size={16} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Platform:</span>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
            <option value="all">All Platforms</option>
            <option value="x">X (Twitter)</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="youtube">YouTube</option>
          </select>
        </div>

        <div className="filter-group">
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Threat Level:</span>
          <select value={threatLevel} onChange={(e) => setThreatLevel(e.target.value)}>
            <option value="all">All Threat Levels</option>
            <option value="Incitement to Violence">Incitement to Violence</option>
            <option value="Fake News">Fake News</option>
            <option value="Inflammatory">Inflammatory</option>
            <option value="Neutral">Neutral</option>
          </select>
        </div>

        <div className="filter-group">
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Language:</span>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="all">All Languages</option>
            <option value="gu">Gujarati (ગુજરાતી)</option>
            <option value="hi">Hindi (हिंदी)</option>
            <option value="hinglish">Hinglish (Code-Mixed)</option>
            <option value="en">English</option>
          </select>
        </div>

        <div className="filter-group" style={{ marginLeft: 'auto' }}>
          <Search size={16} color="var(--text-dim)" />
          <input 
            type="text" 
            placeholder="Search keywords or @user..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      {/* POSTS FEED LIST */}
      <div className="feed-list">
        {posts.length === 0 ? (
          <div className="card-glass" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>
            No posts found matching the selected filters.
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
