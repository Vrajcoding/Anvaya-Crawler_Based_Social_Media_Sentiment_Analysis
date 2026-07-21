import React, { useState } from 'react';
import ThreatBadge from './ThreatBadge';
import { MapPin, ExternalLink, Bot, AlertOctagon, CheckCircle, Printer, Sparkles } from 'lucide-react';

export default function PostCard({ post }) {
  const [actionDone, setActionDone] = useState(null);

  const getPlatformLabel = (platform) => {
    switch (platform) {
      case 'x': return '𝕏 X (Twitter)';
      case 'instagram': return '📸 Instagram';
      case 'facebook': return '📘 Facebook';
      case 'youtube': return '▶️ YouTube';
      default: return '🌐 Web Social';
    }
  };

  const getLangBadge = (code) => {
    switch (code) {
      case 'gu': return 'ગુજરાતી (Gujarati)';
      case 'hi': return 'हिंदी (Hindi)';
      case 'hinglish': return 'Hinglish (कोड-मिक्स)';
      default: return 'English';
    }
  };

  return (
    <div className="gov-post-card">
      <div className="gov-post-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ background: 'var(--gov-navy)', color: '#fff', padding: '0.3rem 0.8rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.9rem' }}>
            {getPlatformLabel(post.platform)}
          </span>

          <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--gov-navy-dark)' }}>
            {post.author_username}
          </span>

          {post.is_bot && (
            <span style={{ background: '#fee2e2', color: '#991b1b', border: '1px solid #f87171', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 800 }}>
              🤖 स्वाचालित बॉट खाता (Bot)
            </span>
          )}

          <span style={{ background: '#e2e8f0', color: '#334155', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700 }}>
            भाषा: {getLangBadge(post.language)}
          </span>
        </div>

        <ThreatBadge level={post.threat_level} />
      </div>

      {/* POST BODY CONTENT */}
      <div className="gov-post-body">
        "{post.content}"
      </div>

      {post.ocr_result && (
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', padding: '0.75rem', borderRadius: '6px', fontSize: '0.95rem', color: '#1e40af', marginBottom: '1rem' }}>
          <strong style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={16} /> फोटो/मीम से निकाला गया पाठ (Image Meme OCR):
          </strong>
          {post.ocr_result.ocr_text}
        </div>
      )}

      {/* FOOTER & ACCESSIBLE ACTION BUTTONS FOR POLICE OFFICERS */}
      <div className="gov-post-footer">
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          {post.geo_location?.city && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: 'var(--gov-navy)' }}>
              <MapPin size={18} color="var(--gov-navy)" /> स्थान: {post.geo_location.city}, {post.geo_location.state}
            </span>
          )}

          <span style={{ fontWeight: 700 }}>
            खतरा स्कोर (Threat Rating): <span style={{ color: post.threat_score >= 0.7 ? '#dc2626' : '#166534', fontSize: '1.1rem' }}>{post.threat_score} / 1.0</span>
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {actionDone ? (
            <span style={{ color: '#166534', fontWeight: 800, background: '#dcfce7', padding: '0.4rem 0.8rem', borderRadius: '6px' }}>
              ✓ {actionDone}
            </span>
          ) : (
            <>
              {post.threat_score >= 0.7 && (
                <button className="btn-gov-danger" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActionDone('ग्राउंड टीम अलर्ट भेजी गई (Field Alert Sent)')}>
                  <AlertOctagon size={16} /> पुलिस टीम भेजें (Dispatch Team)
                </button>
              )}

              <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActionDone('सुरक्षित मार्क किया गया (Marked Safe)')}>
                <CheckCircle size={16} color="#166534" /> सुरक्षित (Safe)
              </button>

              <a href={post.url} target="_blank" rel="noreferrer" className="btn-gov-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', textDecoration: 'none' }}>
                मूल लिंक (Source) <ExternalLink size={14} />
              </a>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
