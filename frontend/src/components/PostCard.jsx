import React from 'react';
import ThreatBadge from './ThreatBadge';
import { ExternalLink, Bot, MapPin, Sparkles } from 'lucide-react';

export default function PostCard({ post }) {
  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'x': return '𝕏';
      case 'instagram': return '📸';
      case 'facebook': return '📘';
      case 'youtube': return '▶️';
      default: return '🌐';
    }
  };

  const formatLangName = (code) => {
    switch (code) {
      case 'gu': return 'Gujarati (ગુજરાતી)';
      case 'hi': return 'Hindi (हिंदी)';
      case 'hinglish': return 'Hinglish (Code-Mixed)';
      default: return 'English';
    }
  };

  return (
    <div className="feed-item">
      <div className="feed-header">
        <div className="author-info">
          <span style={{ fontSize: '1.2rem' }}>{getPlatformIcon(post.platform)}</span>
          <span className="author-name">{post.author_username}</span>
          {post.is_bot && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px', background: 'rgba(239,68,68,0.2)', color: '#ef4444', padding: '1px 6px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
              <Bot size={12} /> BOT ACCOUNT
            </span>
          )}
          <span className="badge-lang">{formatLangName(post.language)}</span>
        </div>

        <ThreatBadge level={post.threat_level} />
      </div>

      <div className="feed-content">
        {post.content}
      </div>

      {post.ocr_result && (
        <div style={{ background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem', color: '#38bdf8' }}>
          <strong style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={14} /> Meme OCR Text Extracted:
          </strong>
          {post.ocr_result.ocr_text}
        </div>
      )}

      <div className="feed-footer">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {post.geo_location?.city && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <MapPin size={14} color="var(--accent-cyan)" /> {post.geo_location.city}, {post.geo_location.state}
            </span>
          )}
          <span>Threat Score: <strong style={{ color: post.threat_score >= 0.7 ? '#ef4444' : '#e2e8f0' }}>{post.threat_score}</strong> / 1.0</span>
        </div>

        <a href={post.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
          View Source <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}
