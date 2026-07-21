import React, { useState, useEffect } from 'react';
import PostCard from '../components/PostCard';
import { fetchPosts, analyzeCustomText } from '../services/api';
import { Filter, Search, Send, Sparkles, AlertCircle } from 'lucide-react';

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
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>📰 सोशल मीडिया लाइव फीड (Social Media Threat Feed)</h2>
          <p>गुजरात राज्य पुलिस द्वारा निगरानी की जा रही एक्स (ट्विटर), इंस्टाग्राम, फेसबुक एवं यूट्यूब की पोस्ट्स</p>
        </div>
      </div>

      {/* QUICK PRESET SEARCH BUTTONS FOR POLICE OFFICERS */}
      <div className="gov-card" style={{ background: '#f8fafc', borderLeft: '6px solid var(--gov-gold)' }}>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Search size={18} color="var(--gov-gold)" /> एक-क्लिक त्वरित खोज (Quick One-Click Search Presets for Police):
        </h4>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('सुरत')}>
            📍 सूरत (Surat)
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('पथराव')}>
            🧱 पत्थरबाजी (Stone Pelting)
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('जहर')}>
            ⚠️ पानी में जहर (Water Poison Rumor)
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('दंगा')}>
            🔥 दंगा / हिंसा (Riots Call)
          </button>
          <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.9rem' }} onClick={() => setQuery('')}>
            🔄 सभी फ़िल्टर साफ़ करें (Clear Filter)
          </button>
        </div>
      </div>

      {/* CUSTOM SUSPICIOUS TEXT TESTER */}
      <div className="gov-card" style={{ border: '2px solid var(--gov-navy)' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles color="var(--gov-navy)" size={20} /> संदिग्ध संदेश का AI विश्लेषण करें (Test Suspicious Text)
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          व्हाट्सएप या सोशल मीडिया पर प्राप्त किसी भी संदिग्ध हिंदी, गुजराती या हिंग्लिश संदेश को यहाँ पेस्ट करके जांचें:
        </p>

        <form onSubmit={handleCustomAnalyze} style={{ display: 'flex', gap: '0.75rem' }}>
          <input 
            type="text" 
            placeholder="उदा: કાલે ચોક બજારમાં ઈંટ પથ્થર સાથે રાત્રે 9 વાગે ભેગા થાઓ... या कल 10 बजे हमला करेंगे!"
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            style={{ flex: 1, border: '2px solid var(--border-gov)', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '1rem', outline: 'none' }}
          />
          <button type="submit" className="btn-gov-primary" disabled={analyzing}>
            <Send size={18} />
            <span>{analyzing ? 'जांच जारी...' : 'जांच करें (Analyze)'}</span>
          </button>
        </form>

        {analysisResult && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#f0fdf4', borderRadius: '8px', border: '2px solid #4ade80' }}>
            <h4 style={{ color: '#166534', marginBottom: '0.5rem' }}>✅ विश्लेषण परिणाम (Analysis Complete):</h4>
            <PostCard post={analysisResult} />
          </div>
        )}
      </div>

      {/* FILTERS CONTROL BAR */}
      <div className="gov-card" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={18} color="var(--gov-navy)" />
          <strong style={{ fontSize: '0.95rem' }}>प्लेटफ़ॉर्म:</strong>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem', fontWeight: 600 }}>
            <option value="all">सभी प्लेटफ़ॉर्म (All)</option>
            <option value="x">X (Twitter)</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="youtube">YouTube</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <strong style={{ fontSize: '0.95rem' }}>खतरा स्तर:</strong>
          <select value={threatLevel} onChange={(e) => setThreatLevel(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem', fontWeight: 600 }}>
            <option value="all">सभी खतरे (All Threat Levels)</option>
            <option value="Incitement to Violence">हिंसा भड़काना (Incitement to Violence)</option>
            <option value="Fake News">झूठी खबर (Fake News)</option>
            <option value="Inflammatory">भड़काऊ (Inflammatory)</option>
            <option value="Neutral">सामान्य (Neutral)</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <strong style={{ fontSize: '0.95rem' }}>भाषा:</strong>
          <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-gov)', fontSize: '0.95rem', fontWeight: 600 }}>
            <option value="all">सभी भाषाएं (All Languages)</option>
            <option value="gu">ગુજરાતી (Gujarati)</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="hinglish">Hinglish (कोड-मिक्स)</option>
            <option value="en">English</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Search size={18} color="var(--text-muted)" />
          <input 
            type="text" 
            placeholder="खोजें (Search text or account)..."
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
            चयनित फ़िल्टर के अनुसार कोई संदेश नहीं मिला। (No posts found)
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
