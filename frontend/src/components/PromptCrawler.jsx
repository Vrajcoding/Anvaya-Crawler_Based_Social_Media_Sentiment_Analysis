import React, { useState, useRef } from 'react';
import { useLanguage } from '../services/LanguageContext';

// Import custom PNG platform icons
import xIcon from '../assets/x.png';
import youtubeIcon from '../assets/youtube.png';
import instaIcon from '../assets/insta.png';
import webIcon from '../assets/web.png';
import redditIcon from '../assets/reddit.png';
import telegramIcon from '../assets/telegram.png';
import searchIcon from '../assets/search.png';
 

const API_BASE = 'http://localhost:8000/api/v1';

const PLATFORMS = [
  { id: 'X', label: 'X (Twitter)', icon: xIcon, emoji: '𝕏', color: '#000000', badge: '#1a1a2e' },
  { id: 'YouTube', label: 'YouTube', icon: youtubeIcon, emoji: '▶', color: '#FF0000', badge: '#1a0000' },
  { id: 'Instagram', label: 'Instagram', icon: instaIcon, emoji: '📸', color: '#E1306C', badge: '#1a0010' },
  { id: 'GoogleSuggest', label: 'Google Suggest', emoji: '🔍', color: '#4285F4', badge: '#00101a' },
  { id: 'Web', label: 'Web', icon: webIcon, emoji: '🌐', color: '#00BFA5', badge: '#001a18' },
  { id: 'Reddit', label: 'Reddit', icon: redditIcon, emoji: '🤖', color: '#FF4500', badge: '#1a0a00' },
  { id: 'Telegram', label: 'Telegram', icon: telegramIcon, emoji: '✈️', color: '#2AABEE', badge: '#001520' },
];

// ── Styles ────────────────────────────────────────────────────────────────────
const S = {
  page: {
    minHeight: '100vh',
    background: 'var(--crawler-bg-gradient)',
    padding: '2rem',
    fontFamily: "'Roboto', 'Inter', 'Segoe UI', sans-serif",
    transition: 'background 0.3s ease, color 0.3s ease',
  },
  container: { maxWidth: '1100px', margin: '0 auto' },
  header: {
    textAlign: 'center',
    marginBottom: '2.5rem',
  },
  badge: {
    display: 'inline-block',
    background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
    borderRadius: '50px',
    padding: '0.25rem 1rem',
    fontSize: '0.75rem',
    fontWeight: 700,
    color: '#fff',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    marginBottom: '0.75rem',
  },
  title: {
    fontSize: '2.4rem',
    fontWeight: 800,
    background: 'var(--crawler-text-title)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: '0 0 0.5rem',
    lineHeight: 1.2,
  },
  subtitle: { color: 'var(--text-muted)', fontSize: '1rem', margin: 0 },
  card: {
    background: 'var(--crawler-card-bg)',
    backdropFilter: 'blur(16px)',
    border: '1px solid var(--crawler-card-border)',
    borderRadius: '20px',
    padding: '2rem',
    marginBottom: '1.5rem',
  },
  inputRow: { display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' },
  input: {
    flex: 1,
    background: 'var(--crawler-input-bg)',
    border: '1.5px solid var(--crawler-input-border)',
    borderRadius: '12px',
    padding: '0.875rem 1.25rem',
    color: 'var(--crawler-input-text)',
    fontSize: '1rem',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  btnPrimary: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    border: 'none',
    borderRadius: '12px',
    padding: '0.875rem 2rem',
    color: '#fff',
    fontWeight: 700,
    fontSize: '0.95rem',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'opacity 0.2s, transform 0.15s',
    letterSpacing: '0.03em',
  },
  platformGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.6rem',
    marginBottom: '1.25rem',
  },
  platformBtn: (active, color) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.45rem 1rem',
    borderRadius: '50px',
    border: `1.5px solid ${active ? color : 'var(--crawler-btn-inactive-border)'}`,
    background: active ? `${color}22` : 'var(--crawler-btn-inactive-bg)',
    color: active ? color : 'var(--crawler-btn-inactive-text)',
    fontWeight: 600,
    fontSize: '0.82rem',
    cursor: 'pointer',
    transition: 'all 0.2s',
  }),
  optionRow: {
    display: 'flex',
    gap: '2rem',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  label: { color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.35rem', display: 'block' },
  rangeWrap: { display: 'flex', alignItems: 'center', gap: '0.75rem' },
  range: { accentColor: '#3b82f6', width: '130px', cursor: 'pointer' },
  rangeVal: {
    color: '#60a5fa',
    fontWeight: 700,
    fontSize: '0.9rem',
    minWidth: '2.5rem',
    textAlign: 'center',
  },
  toggle: (active) => ({
    width: '44px',
    height: '24px',
    borderRadius: '50px',
    background: active ? 'linear-gradient(90deg,#3b82f6,#8b5cf6)' : 'var(--crawler-btn-inactive-border)',
    border: 'none',
    cursor: 'pointer',
    position: 'relative',
    transition: 'background 0.25s',
    flexShrink: 0,
  }),
  toggleDot: (active) => ({
    position: 'absolute',
    top: '3px',
    left: active ? '23px' : '3px',
    width: '18px',
    height: '18px',
    borderRadius: '50%',
    background: '#fff',
    transition: 'left 0.25s',
    boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
  }),
  toggleLabel: { color: 'var(--text-muted)', fontSize: '0.85rem', cursor: 'pointer', userSelect: 'none' },
  sectionTitle: {
    color: 'var(--text-dark)',
    fontWeight: 700,
    fontSize: '1.1rem',
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  platformResult: (color) => ({
    background: 'var(--crawler-card-bg)',
    border: `1px solid ${color}33`,
    borderRadius: '16px',
    padding: '1.25rem',
    marginBottom: '1rem',
  }),
  platformHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '0.75rem',
  },
  platformTitle: (color) => ({
    color,
    fontWeight: 700,
    fontSize: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
  }),
  statusBadge: (ok) => ({
    padding: '0.2rem 0.7rem',
    borderRadius: '50px',
    fontSize: '0.72rem',
    fontWeight: 700,
    background: ok ? '#052e16' : '#1c0007',
    color: ok ? '#4ade80' : '#fb7185',
    border: `1px solid ${ok ? '#16a34a' : '#be123c'}`,
  }),
  postList: { display: 'flex', flexDirection: 'column', gap: '0.6rem' },
  postItem: {
    background: 'var(--crawler-post-bg)',
    borderRadius: '10px',
    padding: '0.75rem 1rem',
    borderLeft: '3px solid var(--crawler-post-border)',
  },
  postContent: { color: 'var(--crawler-post-text)', fontSize: '0.87rem', lineHeight: 1.5, margin: '0 0 0.4rem' },
  postMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  metaChip: { color: 'var(--crawler-meta-text)', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' },
  engagementRow: { display: 'flex', gap: '0.75rem', marginTop: '0.3rem' },
  engChip: (color) => ({
    fontSize: '0.72rem',
    color,
    background: `${color}18`,
    border: `1px solid ${color}33`,
    borderRadius: '50px',
    padding: '0.1rem 0.5rem',
    fontWeight: 600,
  }),
  commentsBox: {
    marginTop: '0.6rem',
    paddingTop: '0.6rem',
    borderTop: '1px solid var(--crawler-post-border)',
  },
  commentItem: {
    fontSize: '0.78rem',
    color: 'var(--text-muted)',
    padding: '0.25rem 0',
  },
  summaryBar: {
    display: 'flex',
    gap: '1.5rem',
    flexWrap: 'wrap',
    padding: '1rem 1.5rem',
    background: 'var(--crawler-summary-bg)',
    border: '1px solid var(--crawler-summary-border)',
    borderRadius: '12px',
    marginBottom: '1.5rem',
  },
  summaryItem: { display: 'flex', flexDirection: 'column', gap: '0.15rem' },
  summaryVal: { color: '#60a5fa', fontWeight: 800, fontSize: '1.3rem' },
  summaryLbl: { color: 'var(--crawler-meta-text)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' },
  skeletonCard: {
    background: 'var(--crawler-card-bg)',
    border: '1px solid var(--crawler-card-border)',
    borderRadius: '16px',
    padding: '1.25rem',
    marginBottom: '1rem',
  },
  skeleton: (w, h) => ({
    background: 'var(--crawler-skeleton-shimmer)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
    borderRadius: '6px',
    width: w,
    height: h,
    marginBottom: '0.5rem',
  }),
  emptyState: {
    textAlign: 'center',
    padding: '3rem 1rem',
    color: 'var(--text-muted)',
  },
  emptyIcon: { fontSize: '3rem', marginBottom: '0.75rem' },
  emptyText: { fontSize: '1rem', fontWeight: 600, color: 'var(--text-dark)' },
  emptySub: { fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' },
  errorCard: {
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.25)',
    borderRadius: '12px',
    padding: '1rem 1.25rem',
    color: '#fca5a5',
    fontSize: '0.9rem',
    marginBottom: '1rem',
  },
  exportBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.85rem 1.25rem',
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '14px',
    marginBottom: '1.5rem',
    flexWrap: 'wrap',
  },
  exportLabel: {
    color: '#64748b',
    fontSize: '0.82rem',
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
    marginRight: '0.25rem',
  },
  btnExportPDF: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
    border: 'none',
    borderRadius: '10px',
    padding: '0.55rem 1.2rem',
    color: '#fff',
    fontWeight: 700,
    fontSize: '0.83rem',
    cursor: 'pointer',
    transition: 'opacity 0.2s, transform 0.15s',
    letterSpacing: '0.02em',
  },
  btnExportXLSX: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    background: 'linear-gradient(135deg, #16a34a 0%, #14532d 100%)',
    border: 'none',
    borderRadius: '10px',
    padding: '0.55rem 1.2rem',
    color: '#fff',
    fontWeight: 700,
    fontSize: '0.83rem',
    cursor: 'pointer',
    transition: 'opacity 0.2s, transform 0.15s',
    letterSpacing: '0.02em',
  },
};

// ── Skeleton loader ───────────────────────────────────────────────────────────
function SkeletonResults({ platforms }) {
  return (
    <>
      <style>{`@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }`}</style>
      {platforms.map((p) => (
        <div key={p} style={S.skeletonCard}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={S.skeleton('6rem', '1.2rem')} />
            <div style={S.skeleton('4rem', '1.2rem')} />
          </div>
          {[1, 2, 3].map((i) => (
            <div key={i} style={{ marginBottom: '0.75rem' }}>
              <div style={S.skeleton('100%', '0.85rem')} />
              <div style={S.skeleton('70%', '0.85rem')} />
              <div style={S.skeleton('40%', '0.65rem')} />
            </div>
          ))}
        </div>
      ))}
    </>
  );
}


// ── NLP Threat Score Badge (All platforms) ──────────────────────────────────────────
function HermesScoreBadge({ post }) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  let score    = post.hermes_score ?? null;
  let severity = post.hermes_severity || 'LOW';
  let reason   = post.hermes_reason || '';
  let breakdown = post.hermes_breakdown || {};

  if (score === null && post.nlp_analysis) {
    const nlp = post.nlp_analysis;
    const cat = nlp.threat_category || {};
    const label = cat.label || 'Neutral';

    if (label === 'Neutral') {
      const allScores = cat.all_scores || {};
      const nonNeutral = Object.entries(allScores)
        .filter(([k]) => k !== 'Neutral')
        .map(([_, v]) => v);
      if (nonNeutral.length > 0) {
        score = Math.round(Math.max(...nonNeutral) * 100);
      } else {
        score = Math.round((1 - (cat.confidence || 0.5)) * 100);
      }
    } else {
      score = Math.round((cat.confidence || 0) * 100);
    }
    
    if (label === 'Incitement to Violence') severity = 'CRITICAL';
    else if (label === 'Fake News') severity = 'HIGH';
    else if (label === 'Inflammatory') severity = 'MEDIUM';
    else severity = 'LOW';
    
    reason = `Detected ${label}. Sentiment: ${nlp.sentiment?.label || 'neutral'}.`;
    breakdown = cat.all_scores || {};
  }

  if (score === null) return null;

  const severityColor = {
    CRITICAL: '#ef4444',
    HIGH:     '#f97316',
    MEDIUM:   '#eab308',
    LOW:      '#22c55e',
  }[severity] || '#22c55e';

  const severityBg = {
    CRITICAL: 'rgba(239,68,68,0.12)',
    HIGH:     'rgba(249,115,22,0.12)',
    MEDIUM:   'rgba(234,179,8,0.12)',
    LOW:      'rgba(34,197,94,0.12)',
  }[severity] || 'rgba(34,197,94,0.12)';

  return (
    <div style={{ marginTop: '0.65rem' }}>
      {/* Score bar row */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}
        onClick={() => setShowBreakdown(p => !p)}
        title="Click to see Hermes breakdown"
      >
        {/* Icon + label */}
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap' }}>
          🛡️ NLP Threat Score
        </span>

        {/* Progress bar */}
        <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.07)', borderRadius: '50px', overflow: 'hidden' }}>
          <div style={{
            width: `${score}%`,
            height: '100%',
            background: `linear-gradient(90deg, ${severityColor}88, ${severityColor})`,
            borderRadius: '50px',
            transition: 'width 0.6s ease',
          }} />
        </div>

        {/* Numeric badge */}
        <span style={{
          padding: '0.15rem 0.55rem',
          borderRadius: '50px',
          fontSize: '0.72rem',
          fontWeight: 800,
          color: severityColor,
          background: severityBg,
          border: `1px solid ${severityColor}44`,
          minWidth: '2.5rem',
          textAlign: 'center',
        }}>
          {score}/100
        </span>

        {/* Severity chip */}
        <span style={{
          padding: '0.1rem 0.45rem',
          borderRadius: '50px',
          fontSize: '0.68rem',
          fontWeight: 700,
          color: severityColor,
          border: `1px solid ${severityColor}55`,
          letterSpacing: '0.04em',
        }}>
          {severity}
        </span>

        <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{showBreakdown ? '▲' : '▼'}</span>
      </div>

      {/* Expandable breakdown panel */}
      {showBreakdown && (
        <div style={{
          marginTop: '0.5rem',
          padding: '0.65rem 0.85rem',
          background: 'rgba(255,255,255,0.03)',
          border: `1px solid ${severityColor}22`,
          borderRadius: '8px',
          fontSize: '0.75rem',
        }}>
          {reason && (
            <p style={{ color: 'var(--text-muted)', margin: '0 0 0.5rem', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--text-dark)' }}>AI Reason:</strong> {reason}
            </p>
          )}
          {Object.keys(breakdown).length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {Object.entries(breakdown).map(([key, val]) => (
                <span key={key} style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '6px',
                  padding: '0.15rem 0.55rem',
                  color: 'var(--text-muted)',
                  fontSize: '0.68rem',
                }}>
                  {key.replace('_component', '')}: <strong style={{ color: 'var(--text-dark)' }}>{val}</strong>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
// ── Post card ─────────────────────────────────────────────────────────────────
function PostCard({ post, platformColor }) {
  const { t } = useLanguage();
  const [showComments, setShowComments] = useState(false);
  const eng = post.engagement || {};
  const hasComments = post.comments && post.comments.length > 0;

  return (
    <div style={{ ...S.postItem, borderLeftColor: `${platformColor}55` }}>
      {post.author_username && (
        <div style={{ color: platformColor, fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.3rem' }}>
          {post.author_username}
        </div>
      )}
      <p style={S.postContent}>{post.content || '—'}</p>
      <div style={S.postMeta}>
        {post.url && (
          <a
            href={post.url}
            target="_blank"
            rel="noreferrer"
            style={{ ...S.metaChip, color: '#60a5fa', textDecoration: 'none' }}
          >
            🔗 Open
          </a>
        )}
        <span style={S.metaChip}>📡 {post.source_type || 'CRAWL'}</span>
        {post.language && <span style={S.metaChip}>🌐 {post.language.toUpperCase()}</span>}
      </div>
      {(eng.likes > 0 || eng.shares > 0 || eng.comments > 0 || eng.views > 0) && (
        <div style={S.engagementRow}>
          {eng.likes > 0 && <span style={S.engChip('#f472b6')}>❤ {eng.likes.toLocaleString()}</span>}
          {eng.shares > 0 && <span style={S.engChip('#60a5fa')}>🔁 {eng.shares.toLocaleString()}</span>}
          {eng.comments > 0 && <span style={S.engChip('#a78bfa')}>💬 {eng.comments.toLocaleString()}</span>}
          {eng.views > 0 && <span style={S.engChip('#34d399')}>👁 {eng.views.toLocaleString()}</span>}
        </div>
      )}

      {/* Hermes Score — shown only for Reddit posts */}
      <HermesScoreBadge post={post} />

      {hasComments && (
        <div style={S.commentsBox}>
          <button
            onClick={() => setShowComments((p) => !p)}
            style={{ background: 'none', border: 'none', color: 'var(--crawler-meta-text)', cursor: 'pointer', fontSize: '0.78rem', padding: 0 }}
          >
            {showComments ? `▲ ${t('crawl_hide')}` : `▼ ${t('crawl_show')}`} {post.comments.length} {post.comments.length !== 1 ? t('crawl_comments') : t('crawl_comment')}
          </button>
          {showComments && post.comments.map((c, i) => (
            <div key={i} style={S.commentItem}>
              <strong style={{ color: 'var(--text-muted)' }}>{c.author}: </strong>{c.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Platform result block ─────────────────────────────────────────────────────
function PlatformResultBlock({ platformId, data }) {
  const { t } = useLanguage();
  const [expanded, setExpanded] = useState(true);
  const pInfo = PLATFORMS.find((p) => p.id === platformId) || { emoji: '🌐', color: '#94a3b8', label: platformId };
  const isOk = data.status === 'success' || data.status === 'no_results' ? data.count > 0 : false;

  return (
    <div style={S.platformResult(pInfo.color)}>
      <div style={S.platformHeader}>
        <div style={S.platformTitle(pInfo.color)}>
          {pInfo.icon ? (
            <img src={pInfo.icon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
          ) : (
            <span>{pInfo.emoji}</span>
          )}
          <span>{pInfo.label}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={S.statusBadge(isOk)}>
            {isOk ? `✓ ${data.count} ${t('crawl_posts_count')}` : data.status === 'error' ? `✗ ${t('crawl_error')}` : `○ ${t('crawl_no_results')}`}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{data.duration_s}s</span>
          <button
            onClick={() => setExpanded((p) => !p)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>
      {expanded && data.posts && data.posts.length > 0 && (
        <div style={S.postList}>
          {data.posts.map((post, i) => (
            <PostCard key={post.id || i} post={post} platformColor={pInfo.color} />
          ))}
        </div>
      )}
      {expanded && (!data.posts || data.posts.length === 0) && (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '0.75rem 0' }}>
          {data.status === 'error' ? `⚠ ${data.error || t('crawl_failed_msg')}` : t('crawl_no_posts_platform')}
        </p>
      )}
    </div>
  );
}

// ── Main PromptCrawler component ─────────────────────────────────────────────
export default function PromptCrawler() {
  const { t } = useLanguage();
  const [prompt, setPrompt] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState(['GoogleSuggest', 'Web', 'X']);
  const [limit, setLimit] = useState(20);
  const [timeFilter, setTimeFilter] = useState('any');
  const [fetchComments, setFetchComments] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(null);
  const [exportLoading, setExportLoading] = useState({ pdf: false, excel: false });
  const inputRef = useRef(null);

  const togglePlatform = (id) =>
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );

  const handleCrawl = async () => {
    if (!prompt.trim()) {
      setError(t('crawl_err_prompt'));
      inputRef.current?.focus();
      return;
    }
    if (selectedPlatforms.length === 0) {
      setError(t('crawl_err_platform'));
      return;
    }
    setError('');
    
    // Initialize results state for streaming
    setResults({
      query: prompt.trim(),
      platforms_crawled: 0,
      total_posts: 0,
      duration_s: 0,
      timestamp: new Date().toISOString(),
      results: {}
    });
    
    setLoading(true);
    setElapsed(null);
    
    try {
      const resp = await fetch(`${API_BASE}/crawl/prompt/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt.trim(),
          platforms: selectedPlatforms,
          limit,
          time_filter: timeFilter,
          fetch_comments: fetchComments,
        }),
      });
      
      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}));
        throw new Error(detail?.detail || `HTTP ${resp.status}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep the last incomplete line in buffer

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'platform_result') {
              setResults(prev => {
                if (!prev) return prev;
                return {
                  ...prev,
                  results: {
                    ...prev.results,
                    [data.platform]: data.data
                  }
                };
              });
            } else if (data.type === 'summary') {
              setElapsed(data.duration_s);
              setResults(prev => {
                if (!prev) return prev;
                return {
                  ...prev,
                  duration_s: data.duration_s,
                  total_posts: data.total_posts,
                  platforms_crawled: data.platforms_crawled
                };
              });
            }
          } catch (e) {
            console.error("Error parsing stream chunk", e, line);
          }
        }
      }
    } catch (e) {
      setError(`${t('crawl_failed_msg')}: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const exportResults = async (format) => {
    if (!results) return;
    setExportLoading((prev) => ({ ...prev, [format]: true }));
    try {
      const resp = await fetch(`${API_BASE}/crawl/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format, results }),
      });
      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}));
        throw new Error(detail?.detail || `HTTP ${resp.status}`);
      }
      const blob = await resp.blob();
      const ext = format === 'pdf' ? 'pdf' : 'xlsx';
      const filename = `sentinelai_${(results.query || 'crawl').replace(/\s+/g, '_')}.${ext}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(`Export failed: ${e.message}`);
    } finally {
      setExportLoading((prev) => ({ ...prev, [format]: false }));
    }
  };

  const totalPosts = results
    ? Object.values(results.results || {}).reduce((s, r) => s + (r.count || 0), 0)
    : 0;

  return (
    <div style={S.page}>
      <div style={S.container}>
        {/* Header */}
        <div style={S.header}>
          <div style={S.badge}>⚡ {t('nav_crawl')} v2.1</div>
          <h1 style={S.title}>{t('crawl_title')}</h1>
          <p style={S.subtitle}>
            {t('crawl_subtitle')}
          </p>
        </div>

        {/* Search card */}
        <div style={S.card}>
          <label style={{ ...S.label, fontSize: '0.9rem', color: 'var(--text-dark)', marginBottom: '0.6rem' }}>
            {t('crawl_search_prompt')}
          </label>
          <div style={S.inputRow}>
            <input
              ref={inputRef}
              type="text"
              placeholder={t('crawl_placeholder')}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCrawl()}
              style={S.input}
            />
            <button
              onClick={handleCrawl}
              disabled={loading}
              style={{ ...S.btnPrimary, opacity: loading ? 0.6 : 1 }}
            >
              {loading ? (
                <>⏳ {t('crawl_crawling')}</>
              ) : (
                <>
                  <img src={searchIcon} alt="" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
                  <span>{t('crawl_start')}</span>
                </>
              )}
            </button>
          </div>

          {/* Platform toggles */}
          <label style={S.label}>{t('crawl_platforms')}</label>
          <div style={S.platformGrid}>
            {PLATFORMS.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePlatform(p.id)}
                style={S.platformBtn(selectedPlatforms.includes(p.id), p.color)}
              >
                {p.icon ? (
                  <img src={p.icon} alt="" style={{ width: '16px', height: '16px', objectFit: 'contain' }} />
                ) : (
                  <span>{p.emoji}</span>
                )}
                <span>{p.label}</span>
              </button>
            ))}
          </div>

          {/* Options row */}
          <div style={S.optionRow}>
            <div>
              <label style={S.label}>{t('crawl_results_per_platform')}</label>
              <div style={S.rangeWrap}>
                <input
                  type="range"
                  min={5}
                  max={5000}
                  step={50}
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  style={S.range}
                />
                <span style={S.rangeVal}>{limit}</span>
              </div>
            </div>
            
            {/* Time Filter */}
            <div>
              <label style={S.label}>{t('crawl_time_filter')}</label>
              <select
                value={timeFilter}
                onChange={(e) => setTimeFilter(e.target.value)}
                style={{
                  ...S.input,
                  padding: '0.5rem 1rem',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  width: '120px'
                }}
              >
                <option value="any">{t('crawl_time_any')}</option>
                <option value="24h">{t('crawl_time_24h')}</option>
                <option value="48h">{t('crawl_time_48h')}</option>
                <option value="1week">{t('crawl_time_1week')}</option>
                <option value="1month">{t('crawl_time_1month')}</option>
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <button
                onClick={() => setFetchComments((p) => !p)}
                style={S.toggle(fetchComments)}
                aria-label="Toggle comment extraction"
              >
                <div style={S.toggleDot(fetchComments)} />
              </button>
              <span
                style={S.toggleLabel}
                onClick={() => setFetchComments((p) => !p)}
              >
                {t('crawl_fetch_comments')} <span style={{ color: 'var(--text-muted)' }}>(+30s)</span>
              </span>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && <div style={S.errorCard}>⚠ {error}</div>}

        {/* Loading skeleton */}
        {loading && <SkeletonResults platforms={selectedPlatforms} />}

        {/* Results */}
        {results && !loading && (
          <>
            {/* Summary bar */}
            <div style={S.summaryBar}>
              <div style={S.summaryItem}>
                <span style={S.summaryVal}>{totalPosts}</span>
                <span style={S.summaryLbl}>{t('crawl_total_posts')}</span>
              </div>
              <div style={S.summaryItem}>
                <span style={S.summaryVal}>{results.platforms_crawled}</span>
                <span style={S.summaryLbl}>{t('crawl_platforms')}</span>
              </div>
              <div style={S.summaryItem}>
                <span style={S.summaryVal}>{elapsed || results.duration_s}s</span>
                <span style={S.summaryLbl}>{t('crawl_duration')}</span>
              </div>
              <div style={S.summaryItem}>
                <span style={{ ...S.summaryVal, fontSize: '0.95rem', paddingTop: '0.2rem' }}>
                  {results.query}
                </span>
                <span style={S.summaryLbl}>{t('crawl_query')}</span>
              </div>
            </div>

            {/* Export toolbar */}
            <div style={S.exportBar}>
              <span style={S.exportLabel}>⬇ Export</span>
              <button
                id="export-pdf-btn"
                onClick={() => exportResults('pdf')}
                disabled={exportLoading.pdf || exportLoading.excel}
                style={{
                  ...S.btnExportPDF,
                  opacity: exportLoading.pdf ? 0.65 : 1,
                  transform: exportLoading.pdf ? 'scale(0.97)' : 'scale(1)',
                }}
                title="Download results as a styled PDF report"
              >
                {exportLoading.pdf ? '⏳' : '📄'} {exportLoading.pdf ? 'Generating PDF…' : 'Export PDF'}
              </button>
              <button
                id="export-excel-btn"
                onClick={() => exportResults('excel')}
                disabled={exportLoading.pdf || exportLoading.excel}
                style={{
                  ...S.btnExportXLSX,
                  opacity: exportLoading.excel ? 0.65 : 1,
                  transform: exportLoading.excel ? 'scale(0.97)' : 'scale(1)',
                }}
                title="Download results as an Excel spreadsheet (.xlsx)"
              >
                {exportLoading.excel ? '⏳' : '📊'} {exportLoading.excel ? 'Generating Excel…' : 'Export Excel'}
              </button>
              <span style={{ color: '#334155', fontSize: '0.78rem', marginLeft: 'auto' }}>
                {totalPosts} posts · {results.platforms_crawled} platforms
              </span>
            </div>

            {/* Per-platform results */}
            <div style={{ ...S.sectionTitle }}>
              📊 {t('crawl_results_by_platform')}
            </div>
            {Object.entries(results.results).map(([platformId, data]) => (
              <PlatformResultBlock key={platformId} platformId={platformId} data={data} />
            ))}
          </>
        )}

        {/* Empty state */}
        {!results && !loading && !error && (
          <div style={S.emptyState}>
            <div style={S.emptyIcon}>🔍</div>
            <div style={S.emptyText}>{t('crawl_ready')}</div>
            <div style={S.emptySub}>
              {t('crawl_ready_desc')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
