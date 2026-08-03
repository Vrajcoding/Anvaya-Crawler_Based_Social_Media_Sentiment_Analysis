import React, { useState, useRef } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

const PLATFORMS = [
  { id: 'X', label: 'X (Twitter)', emoji: '𝕏', color: '#000000', badge: '#1a1a2e' },
  { id: 'YouTube', label: 'YouTube', emoji: '▶', color: '#FF0000', badge: '#1a0000' },
  { id: 'Instagram', label: 'Instagram', emoji: '📸', color: '#E1306C', badge: '#1a0010' },
  { id: 'GoogleSuggest', label: 'Google Suggest', emoji: '🔍', color: '#4285F4', badge: '#00101a' },
  { id: 'Web', label: 'Web', emoji: '🌐', color: '#00BFA5', badge: '#001a18' },
  { id: 'Reddit', label: 'Reddit', emoji: '🤖', color: '#FF4500', badge: '#1a0a00' },
  { id: 'Telegram', label: 'Telegram', emoji: '✈️', color: '#2AABEE', badge: '#001520' },
];

// ── Styles ────────────────────────────────────────────────────────────────────
const S = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #111827 100%)',
    padding: '2rem',
    fontFamily: "'Inter', 'Segoe UI', sans-serif",
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
    background: 'linear-gradient(135deg, #60a5fa, #a78bfa, #34d399)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: '0 0 0.5rem',
    lineHeight: 1.2,
  },
  subtitle: { color: '#94a3b8', fontSize: '1rem', margin: 0 },
  card: {
    background: 'rgba(255,255,255,0.04)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '20px',
    padding: '2rem',
    marginBottom: '1.5rem',
  },
  inputRow: { display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' },
  input: {
    flex: 1,
    background: 'rgba(255,255,255,0.06)',
    border: '1.5px solid rgba(255,255,255,0.12)',
    borderRadius: '12px',
    padding: '0.875rem 1.25rem',
    color: '#f1f5f9',
    fontSize: '1rem',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  btnPrimary: {
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
    border: `1.5px solid ${active ? color : 'rgba(255,255,255,0.12)'}`,
    background: active ? `${color}22` : 'rgba(255,255,255,0.04)',
    color: active ? color : '#94a3b8',
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
  label: { color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.35rem', display: 'block' },
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
    background: active ? 'linear-gradient(90deg,#3b82f6,#8b5cf6)' : 'rgba(255,255,255,0.1)',
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
  toggleLabel: { color: '#94a3b8', fontSize: '0.85rem', cursor: 'pointer', userSelect: 'none' },
  sectionTitle: {
    color: '#e2e8f0',
    fontWeight: 700,
    fontSize: '1.1rem',
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  platformResult: (color) => ({
    background: 'rgba(255,255,255,0.03)',
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
    background: 'rgba(255,255,255,0.04)',
    borderRadius: '10px',
    padding: '0.75rem 1rem',
    borderLeft: '3px solid rgba(255,255,255,0.1)',
  },
  postContent: { color: '#e2e8f0', fontSize: '0.87rem', lineHeight: 1.5, margin: '0 0 0.4rem' },
  postMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  metaChip: { color: '#64748b', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' },
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
    borderTop: '1px solid rgba(255,255,255,0.06)',
  },
  commentItem: {
    fontSize: '0.78rem',
    color: '#94a3b8',
    padding: '0.25rem 0',
  },
  summaryBar: {
    display: 'flex',
    gap: '1.5rem',
    flexWrap: 'wrap',
    padding: '1rem 1.5rem',
    background: 'rgba(59,130,246,0.08)',
    border: '1px solid rgba(59,130,246,0.2)',
    borderRadius: '12px',
    marginBottom: '1.5rem',
  },
  summaryItem: { display: 'flex', flexDirection: 'column', gap: '0.15rem' },
  summaryVal: { color: '#60a5fa', fontWeight: 800, fontSize: '1.3rem' },
  summaryLbl: { color: '#64748b', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' },
  skeletonCard: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '16px',
    padding: '1.25rem',
    marginBottom: '1rem',
  },
  skeleton: (w, h) => ({
    background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)',
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
    color: '#475569',
  },
  emptyIcon: { fontSize: '3rem', marginBottom: '0.75rem' },
  emptyText: { fontSize: '1rem', fontWeight: 600, color: '#64748b' },
  emptySub: { fontSize: '0.85rem', color: '#475569', marginTop: '0.35rem' },
  errorCard: {
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.25)',
    borderRadius: '12px',
    padding: '1rem 1.25rem',
    color: '#fca5a5',
    fontSize: '0.9rem',
    marginBottom: '1rem',
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
        <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, whiteSpace: 'nowrap' }}>
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

        <span style={{ color: '#475569', fontSize: '0.7rem' }}>{showBreakdown ? '▲' : '▼'}</span>
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
            <p style={{ color: '#94a3b8', margin: '0 0 0.5rem', lineHeight: 1.5 }}>
              <strong style={{ color: '#cbd5e1' }}>AI Reason:</strong> {reason}
            </p>
          )}
          {Object.keys(breakdown).length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {Object.entries(breakdown).map(([key, val]) => (
                <span key={key} style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '6px',
                  padding: '0.15rem 0.5rem',
                  color: '#64748b',
                  fontSize: '0.68rem',
                }}>
                  {key.replace('_component', '')}: <strong style={{ color: '#94a3b8' }}>{val}</strong>
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
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.78rem', padding: 0 }}
          >
            {showComments ? '▲ Hide' : '▼ Show'} {post.comments.length} comment{post.comments.length !== 1 ? 's' : ''}
          </button>
          {showComments && post.comments.map((c, i) => (
            <div key={i} style={S.commentItem}>
              <strong style={{ color: '#94a3b8' }}>{c.author}: </strong>{c.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Platform result block ─────────────────────────────────────────────────────
function PlatformResultBlock({ platformId, data }) {
  const [expanded, setExpanded] = useState(true);
  const pInfo = PLATFORMS.find((p) => p.id === platformId) || { emoji: '🌐', color: '#94a3b8', label: platformId };
  const isOk = data.status === 'success' || data.status === 'no_results' ? data.count > 0 : false;

  return (
    <div style={S.platformResult(pInfo.color)}>
      <div style={S.platformHeader}>
        <div style={S.platformTitle(pInfo.color)}>
          <span>{pInfo.emoji}</span>
          <span>{pInfo.label}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={S.statusBadge(isOk)}>
            {isOk ? `✓ ${data.count} posts` : data.status === 'error' ? '✗ Error' : '○ No results'}
          </span>
          <span style={{ color: '#64748b', fontSize: '0.75rem' }}>{data.duration_s}s</span>
          <button
            onClick={() => setExpanded((p) => !p)}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.85rem' }}
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
        <p style={{ color: '#475569', fontSize: '0.85rem', textAlign: 'center', padding: '0.75rem 0' }}>
          {data.status === 'error' ? `⚠ ${data.error || 'Crawl failed'}` : 'No posts found for this platform.'}
        </p>
      )}
    </div>
  );
}

// ── Main PromptCrawler component ─────────────────────────────────────────────
export default function PromptCrawler() {
  const [prompt, setPrompt] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState(['GoogleSuggest', 'Web', 'X']);
  const [limit, setLimit] = useState(20);
  const [timeFilter, setTimeFilter] = useState('any');
  const [fetchComments, setFetchComments] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(null);
  const inputRef = useRef(null);

  const togglePlatform = (id) =>
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );

  const handleCrawl = async () => {
    if (!prompt.trim()) {
      setError('Please enter a search prompt.');
      inputRef.current?.focus();
      return;
    }
    if (selectedPlatforms.length === 0) {
      setError('Please select at least one platform.');
      return;
    }
    setError('');
    setResults(null);
    setLoading(true);
    setElapsed(null);
    const t0 = Date.now();
    try {
      const resp = await fetch(`${API_BASE}/crawl/prompt`, {
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
      const data = await resp.json();
      setResults(data);
      setElapsed(((Date.now() - t0) / 1000).toFixed(1));
    } catch (e) {
      setError(`Crawl failed: ${e.message}`);
    } finally {
      setLoading(false);
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
          <div style={S.badge}>⚡ Prompt Crawler v2.1</div>
          <h1 style={S.title}>Social Media Intelligence</h1>
          <p style={S.subtitle}>
            Enter any search prompt — SentinelAI crawls all platforms in parallel
          </p>
        </div>

        {/* Search card */}
        <div style={S.card}>
          <label style={{ ...S.label, fontSize: '0.9rem', color: '#cbd5e1', marginBottom: '0.6rem' }}>
            Search Prompt
          </label>
          <div style={S.inputRow}>
            <input
              ref={inputRef}
              type="text"
              placeholder='e.g. "india protest" or "cjp news"'
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
              {loading ? '⏳ Crawling…' : '🚀 Start Crawling'}
            </button>
          </div>

          {/* Platform toggles */}
          <label style={S.label}>Platforms</label>
          <div style={S.platformGrid}>
            {PLATFORMS.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePlatform(p.id)}
                style={S.platformBtn(selectedPlatforms.includes(p.id), p.color)}
              >
                <span>{p.emoji}</span> {p.label}
              </button>
            ))}
          </div>

          {/* Options row */}
          <div style={S.optionRow}>
            <div>
              <label style={S.label}>Results per platform</label>
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
              <label style={S.label}>Time Filter</label>
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
                <option value="any">Any Time</option>
                <option value="24h">Past 24h</option>
                <option value="48h">Past 48h</option>
                <option value="1week">Past 1 Week</option>
                <option value="1month">Past 1 Month</option>
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
                Fetch comments <span style={{ color: '#475569' }}>(+30s)</span>
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
                <span style={S.summaryLbl}>Total Posts</span>
              </div>
              <div style={S.summaryItem}>
                <span style={S.summaryVal}>{results.platforms_crawled}</span>
                <span style={S.summaryLbl}>Platforms</span>
              </div>
              <div style={S.summaryItem}>
                <span style={S.summaryVal}>{elapsed || results.duration_s}s</span>
                <span style={S.summaryLbl}>Duration</span>
              </div>
              <div style={S.summaryItem}>
                <span style={{ ...S.summaryVal, fontSize: '0.95rem', paddingTop: '0.2rem' }}>
                  {results.query}
                </span>
                <span style={S.summaryLbl}>Query</span>
              </div>
            </div>

            {/* Per-platform results */}
            <div style={{ ...S.sectionTitle }}>
              📊 Results by Platform
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
            <div style={S.emptyText}>Ready to crawl</div>
            <div style={S.emptySub}>
              Enter a prompt above and click "Start Crawling" to harvest social intelligence
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
