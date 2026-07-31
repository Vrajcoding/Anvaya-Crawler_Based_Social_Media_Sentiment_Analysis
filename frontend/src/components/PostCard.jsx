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
      case 'hinglish': case 'hi-en-mixed': return 'Hinglish (Code-Mixed)';
      case 'gu-en-mixed': return 'Gujarati-English Mix';
      default: return 'English';
    }
  };

  // Extract sentiment from either top-level or nested nlp_analysis
  const getSentiment = () => {
    const s = post.sentiment;
    if (typeof s === 'object' && s?.label) return s;
    const nlp = post.nlp_analysis?.sentiment;
    if (nlp) return nlp;
    return { label: s || 'neutral', confidence: 0 };
  };

  const sentiment = getSentiment();
  const sentimentLabel = (sentiment.label || 'neutral').toLowerCase();
  const sentimentConf = sentiment.confidence || sentiment.score || 0;

  const getSentimentStyle = () => {
    switch (sentimentLabel) {
      case 'positive': return { bg: 'rgba(34, 197, 94, 0.18)', color: '#4ade80', border: '#22c55e', icon: '✅', text: 'Positive' };
      case 'negative': return { bg: 'rgba(239, 68, 68, 0.18)', color: '#fca5a5', border: '#ef4444', icon: '⛔', text: 'Negative' };
      default:         return { bg: 'rgba(99, 102, 241, 0.18)', color: '#a5b4fc', border: '#6366f1', icon: '▫️', text: 'Neutral' };
    }
  };
  const sentStyle = getSentimentStyle();

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
    <div className="gov-post-card transition-all hover:shadow-lg">
      <div className="gov-post-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ background: 'var(--gov-navy)', color: '#fff', padding: '0.3rem 0.8rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            {getPlatformLabel(post.platform)}
          </span>

          <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text-dark)' }}>
            {post.author_username}
          </span>

          {post.is_bot && (
            <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid #ef4444', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '4px' }} className="animate-pulse">
              🤖 Bot Network Account
            </span>
          )}

          <span style={{ background: 'var(--bg-card-alt)', color: 'var(--text-muted)', border: '1px solid var(--border-gov)', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700 }}>
            {t('label_language')} {getLangBadge(post.language)}
          </span>
        </div>

        <ThreatBadge level={post.threat_level} />

        {/* SENTIMENT BADGE */}
        <span style={{
          background: sentStyle.bg,
          color: sentStyle.color,
          border: `1.5px solid ${sentStyle.border}`,
          padding: '0.25rem 0.7rem',
          borderRadius: '6px',
          fontSize: '0.82rem',
          fontWeight: 800,
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          letterSpacing: '0.02em'
        }}>
          {sentStyle.icon} {sentStyle.text} ({(sentimentConf * 100).toFixed(0)}%)
        </span>
      </div>

      {/* POST BODY CONTENT */}
      <div className="gov-post-body">
        "{post.content}"
      </div>

      {post.ocr_result && (
        <div style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid #3b82f6', padding: '0.75rem', borderRadius: '6px', fontSize: '0.95rem', color: '#93c5fd', marginBottom: '1rem', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <Sparkles size={18} className="shrink-0 mt-0.5 text-blue-400" />
          <div>
            <strong className="block text-xs uppercase tracking-wider text-blue-300">OCR Embedded Infographic / Reel Text:</strong>
            <span className="font-semibold text-blue-100 mt-0.5 block">{post.ocr_result.ocr_text}</span>
          </div>
        </div>
      )}

      {/* EXPANDABLE AI ANALYSIS ACCORDION (HERMES AGENT REASONING & 6-FACTOR SCORE BREAKDOWN) */}
      <div className="mb-4 border border-indigo-900/60 rounded-lg overflow-hidden bg-slate-900/40">
        <button
          onClick={() => setShowAnalysis(!showAnalysis)}
          className="w-full px-4 py-2.5 bg-indigo-950/40 hover:bg-indigo-900/60 text-indigo-200 font-bold text-xs flex items-center justify-between transition-colors border-b border-indigo-900/60"
        >
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <span>{lang === 'hi' ? 'न्यूरल एआई विश्लेषण व खतरा स्कोर विवरण' : 'Neural AI Threat & Sentiment Score Breakdown'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-indigo-900 text-indigo-200 border border-indigo-700 rounded font-mono font-black">
              {post.threat_score} / 1.0
            </span>
            {showAnalysis ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>

        {showAnalysis && (
          <div className="p-4 bg-slate-900/80 space-y-3.5 text-xs animate-fadeIn text-slate-200">

            {/* SENTIMENT ANALYSIS RESULT */}
            <div className="p-3 rounded-lg border" style={{ background: sentStyle.bg, borderColor: sentStyle.border }}>
              <span className="font-bold uppercase tracking-wider block text-[10px]" style={{ color: sentStyle.color }}>
                Sentiment Analysis Result ({sentiment.model || post.nlp_analysis?.sentiment?.model || 'transformer'}):
              </span>
              <div className="mt-1.5 flex items-center gap-3 flex-wrap">
                <span className="text-sm font-black" style={{ color: sentStyle.color }}>
                  {sentStyle.icon} {sentStyle.text}
                </span>
                <span className="px-2 py-0.5 bg-slate-950/60 rounded font-mono font-bold text-[11px]" style={{ color: sentStyle.color }}>
                  Confidence: {(sentimentConf * 100).toFixed(1)}%
                </span>
              </div>
              {/* Probability bars */}
              {(sentiment.probabilities || post.nlp_analysis?.sentiment?.probabilities) && (
                <div className="mt-2 space-y-1">
                  {Object.entries(sentiment.probabilities || post.nlp_analysis?.sentiment?.probabilities || {}).map(([label, prob]) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="w-16 text-[10px] font-semibold text-slate-400 capitalize">{label}</span>
                      <div className="flex-1 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${(prob * 100).toFixed(0)}%`,
                            background: label === 'positive' ? '#22c55e' : label === 'negative' ? '#ef4444' : '#818cf8',
                          }}
                        />
                      </div>
                      <span className="font-mono font-bold text-[10px] text-slate-300 w-10 text-right">{(prob * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* THREAT CLASSIFICATION */}
            <div className="p-3 bg-slate-800/80 rounded-lg border border-slate-700">
              <span className="font-bold text-slate-400 uppercase tracking-wider block text-[10px]">
                Threat Classification ({post.nlp_analysis?.threat_category?.model || 'zero-shot NLI'}):
              </span>
              <p className="text-slate-200 font-semibold mt-1 text-sm leading-relaxed">{aiReason}</p>
              {/* Threat score bars */}
              {(post.nlp_analysis?.threat_category?.all_scores) && (
                <div className="mt-2 space-y-1">
                  {Object.entries(post.nlp_analysis.threat_category.all_scores).map(([label, score]) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="w-28 text-[10px] font-semibold text-slate-400">{label}</span>
                      <div className="flex-1 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${(score * 100).toFixed(0)}%`,
                            background: label === 'Neutral' ? '#22c55e' : label === 'Inflammatory' ? '#f59e0b' : label === 'Incitement to Violence' ? '#ef4444' : '#a855f7',
                          }}
                        />
                      </div>
                      <span className="font-mono font-bold text-[10px] text-slate-300 w-10 text-right">{(score * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* HATE SPEECH DETECTION */}
            {(post.nlp_analysis?.hate_speech || post.is_hate_speech) && (
              <div className={`p-3 rounded-lg border ${
                (post.nlp_analysis?.hate_speech?.flag || post.is_hate_speech)
                  ? 'bg-red-950/40 border-red-800'
                  : 'bg-emerald-950/40 border-emerald-800'
              }`}>
                <span className={`font-bold uppercase tracking-wider block text-[10px] ${
                  (post.nlp_analysis?.hate_speech?.flag || post.is_hate_speech) ? 'text-red-400' : 'text-emerald-400'
                }`}>
                  Hate Speech Detection ({post.nlp_analysis?.hate_speech?.model || 'ensemble'}):
                </span>
                <div className="mt-1 flex items-center gap-2">
                  {(post.nlp_analysis?.hate_speech?.flag || post.is_hate_speech) ? (
                    <span className="text-red-300 font-bold flex items-center gap-1">
                      <AlertTriangle size={14} /> HATE SPEECH DETECTED
                      <span className="ml-1 font-mono">({((post.nlp_analysis?.hate_speech?.confidence || 0) * 100).toFixed(0)}%)</span>
                    </span>
                  ) : (
                    <span className="text-emerald-300 font-bold flex items-center gap-1">
                      <ShieldCheck size={14} /> No hate speech detected
                    </span>
                  )}
                </div>
                {post.nlp_analysis?.hate_speech?.target_group_hint && (
                  <span className="text-[10px] text-red-400 mt-1 block">Target: {post.nlp_analysis.hate_speech.target_group_hint}</span>
                )}
              </div>
            )}

            {/* 6-FACTOR COMPOSITE SCORE */}
            <div>
              <span className="font-bold text-slate-300 block mb-2 text-xs">
                {lang === 'hi' ? '6-कारक खतरा स्कोर गणना (Threat Scoring Breakdown):' : '6-Factor Composite Threat Scoring Formula:'}
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                  <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
                    <span>Threat Lexicon (30%)</span>
                    <span>{Math.round((scoreBreakdown.classification || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-red-500 h-full" style={{ width: `${(scoreBreakdown.classification || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                  <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
                    <span>Negative Sentiment (20%)</span>
                    <span>{Math.round((scoreBreakdown.sentiment || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-amber-500 h-full" style={{ width: `${(scoreBreakdown.sentiment || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                  <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
                    <span>Hate Speech (15%)</span>
                    <span>{Math.round((scoreBreakdown.hate_speech || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-purple-500 h-full" style={{ width: `${(scoreBreakdown.hate_speech || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                  <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
                    <span>Viral Velocity (15%)</span>
                    <span>{Math.round((scoreBreakdown.velocity || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full" style={{ width: `${(scoreBreakdown.velocity || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                  <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
                    <span>Coordination Ring (10%)</span>
                    <span>{Math.round((scoreBreakdown.coordination || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full" style={{ width: `${(scoreBreakdown.coordination || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                  <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
                    <span>Bot Network Likelihood (10%)</span>
                    <span>{Math.round((scoreBreakdown.bot || 0) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-rose-500 h-full" style={{ width: `${(scoreBreakdown.bot || 0) * 100}%` }}></div>
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
