import React, { useState } from 'react';
import ThreatBadge from './ThreatBadge';
import { MapPin, ExternalLink, Bot, AlertOctagon, CheckCircle, Printer, Sparkles, ChevronDown, ChevronUp, Cpu, Activity, ShieldCheck, AlertTriangle } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function PostCard({ post }) {
  const { t, lang } = useLanguage();
  const [actionDone, setActionDone] = useState(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

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
      case 'hinglish': return 'Hinglish (Code-Mixed)';
      default: return 'English';
    }
  };

  const scoreBreakdown = post.scoring_breakdown || {
    sentiment: 0.1,
    classification: post.threat_score || 0.2,
    hate_speech: 0.0,
    velocity: 0.2,
    coordination: post.coordination_group ? 0.3 : 0.0,
    bot: post.is_bot ? 0.2 : 0.0
  };

  const aiReason = post.nlp_breakdown?.threat_classification?.reason || 
    (post.threat_level === 'Incitement to Violence' ? 'Contains keywords calling for mob assembly and stone pelting.' : 
     post.threat_level === 'Fake News' ? 'Unverified rumor regarding civic utilities / communal panic.' : 
     'Standard social interaction / general civic discussion.');

  return (
    <div className="gov-post-card transition-all hover:shadow-lg hover:border-indigo-300">
      <div className="gov-post-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ background: 'var(--gov-navy)', color: '#fff', padding: '0.3rem 0.8rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.9rem', display: 'flex', itemsCenter: true, gap: '6px' }}>
            {getPlatformLabel(post.platform)}
          </span>

          <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--gov-navy-dark)' }}>
            {post.author_username}
          </span>

          {post.is_bot && (
            <span style={{ background: '#fee2e2', color: '#991b1b', border: '1px solid #f87171', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '4px' }} className="animate-pulse">
              🤖 Bot Network Account
            </span>
          )}

          <span style={{ background: '#e2e8f0', color: '#334155', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700 }}>
            {t('label_language')} {getLangBadge(post.language)}
          </span>
        </div>

        <ThreatBadge level={post.threat_level} />
      </div>

      {/* POST BODY CONTENT */}
      <div className="gov-post-body">
        "{post.content}"
      </div>

      {post.ocr_result && (
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', padding: '0.75rem', borderRadius: '6px', fontSize: '0.95rem', color: '#1e40af', marginBottom: '1rem', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <Sparkles size={18} className="shrink-0 mt-0.5 text-blue-600" />
          <div>
            <strong className="block text-xs uppercase tracking-wider text-blue-800">OCR Embedded Infographic / Reel Text:</strong>
            <span className="font-semibold text-blue-950 mt-0.5 block">{post.ocr_result.ocr_text}</span>
          </div>
        </div>
      )}

      {/* EXPANDABLE AI ANALYSIS ACCORDION (HERMES AGENT REASONING & 6-FACTOR SCORE BREAKDOWN) */}
      <div className="mb-4 border border-indigo-100 rounded-lg overflow-hidden bg-indigo-50/30">
        <button
          onClick={() => setShowAnalysis(!showAnalysis)}
          className="w-full px-4 py-2.5 bg-indigo-50 hover:bg-indigo-100/80 text-indigo-900 font-bold text-xs flex items-center justify-between transition-colors border-b border-indigo-100/60"
        >
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-600" />
            <span>{lang === 'hi' ? 'हर्मिस एआई विश्लेषण व खतरा स्कोर विवरण' : 'Hermes AI Analysis & 6-Factor Threat Score Breakdown'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-indigo-200 text-indigo-900 rounded font-mono font-black">
              {post.threat_score} / 1.0
            </span>
            {showAnalysis ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>

        {showAnalysis && (
          <div className="p-4 bg-white space-y-3.5 text-xs animate-fadeIn">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="font-bold text-slate-500 uppercase tracking-wider block text-[10px]">
                {lang === 'hi' ? 'एआई इंटेलिजेंस मूल्यांकन (OpenRouter Multi-Agent):' : 'Hermes AI Intelligence Assessment:'}
              </span>
              <p className="text-slate-800 font-semibold mt-1 text-sm leading-relaxed">{aiReason}</p>
            </div>

            <div>
              <span className="font-bold text-gray-700 block mb-2 text-xs">
                {lang === 'hi' ? '6-कारक खतरा स्कोर गणना (Threat Scoring Breakdown):' : '6-Factor Composite Threat Scoring Formula:'}
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                <div className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between text-[11px] text-gray-600 font-semibold mb-1">
                    <span>Threat Lexicon (30%)</span>
                    <span>{Math.round((scoreBreakdown.classification || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-red-600 h-full" style={{ width: `${(scoreBreakdown.classification || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between text-[11px] text-gray-600 font-semibold mb-1">
                    <span>Negative Sentiment (20%)</span>
                    <span>{Math.round((scoreBreakdown.sentiment || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-amber-600 h-full" style={{ width: `${(scoreBreakdown.sentiment || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between text-[11px] text-gray-600 font-semibold mb-1">
                    <span>Hate Speech (15%)</span>
                    <span>{Math.round((scoreBreakdown.hate_speech || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-purple-600 h-full" style={{ width: `${(scoreBreakdown.hate_speech || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between text-[11px] text-gray-600 font-semibold mb-1">
                    <span>Viral Velocity (15%)</span>
                    <span>{Math.round((scoreBreakdown.velocity || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-blue-600 h-full" style={{ width: `${(scoreBreakdown.velocity || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between text-[11px] text-gray-600 font-semibold mb-1">
                    <span>Coordination Ring (10%)</span>
                    <span>{Math.round((scoreBreakdown.coordination || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-indigo-600 h-full" style={{ width: `${(scoreBreakdown.coordination || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between text-[11px] text-gray-600 font-semibold mb-1">
                    <span>Bot Network Likelihood (10%)</span>
                    <span>{Math.round((scoreBreakdown.bot || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-rose-600 h-full" style={{ width: `${(scoreBreakdown.bot || 0) * 100}%` }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* FOOTER & ACCESSIBLE ACTION BUTTONS FOR POLICE OFFICERS */}
      <div className="gov-post-footer">
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {post.geo_location?.city && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: 'var(--gov-navy)' }}>
              <MapPin size={18} color="var(--gov-navy)" /> {post.geo_location.city}, {post.geo_location.state}
            </span>
          )}

          <span style={{ fontWeight: 700 }}>
            Threat Rating: <span style={{ color: post.threat_score >= 0.7 ? '#dc2626' : '#166534', fontSize: '1.1rem' }}>{post.threat_score} / 1.0</span>
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {actionDone ? (
            <span style={{ color: '#166534', fontWeight: 800, background: '#dcfce7', padding: '0.4rem 0.8rem', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldCheck size={16} /> {actionDone}
            </span>
          ) : (
            <>
              {post.threat_score >= 0.7 && (
                <button className="btn-gov-danger animate-pulse" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActionDone('Field Alert Sent')}>
                  <AlertOctagon size={16} /> Dispatch Team
                </button>
              )}

              <button className="btn-gov-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setActionDone('Marked Safe')}>
                <CheckCircle size={16} color="#166534" /> Safe
              </button>

              <a href={post.url} target="_blank" rel="noreferrer" className="btn-gov-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', textDecoration: 'none' }}>
                Source <ExternalLink size={14} />
              </a>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
