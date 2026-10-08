import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000/api/v1';

// Color mapping for threat scores
function threatColor(score) {
  if (score >= 0.85) return '#ef4444';
  if (score >= 0.70) return '#f97316';
  if (score >= 0.50) return '#eab308';
  return '#22c55e';
}

function botColor(bot) {
  if (bot >= 0.6) return '#a855f7';
  if (bot >= 0.3) return '#ec4899';
  return '#64748b';
}

// Simple force simulation (without d3 dependency)
function useForceSimulation(nodes, edges, width, height) {
  const [positions, setPositions] = useState({});

  useEffect(() => {
    if (!nodes.length) return;
    // Initialize random positions
    const pos = {};
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      const r = Math.min(width, height) * 0.35;
      pos[n.id] = {
        x: width / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 60,
        y: height / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 60,
        vx: 0,
        vy: 0,
      };
    });

    let positions_state = { ...pos };
    const iterations = 80;

    for (let iter = 0; iter < iterations; iter++) {
      // Repulsion between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const ni = nodes[i].id, nj = nodes[j].id;
          const pi = positions_state[ni], pj = positions_state[nj];
          if (!pi || !pj) continue;
          const dx = pi.x - pj.x;
          const dy = pi.y - pj.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 2500 / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          pi.vx += fx * 0.1;
          pi.vy += fy * 0.1;
          pj.vx -= fx * 0.1;
          pj.vy -= fy * 0.1;
        }
      }

      // Attraction along edges
      edges.forEach(e => {
        const ps = positions_state[e.source], pt = positions_state[e.target];
        if (!ps || !pt) return;
        const dx = pt.x - ps.x;
        const dy = pt.y - ps.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = dist * 0.003;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        ps.vx += fx;
        ps.vy += fy;
        pt.vx -= fx;
        pt.vy -= fy;
      });

      // Centering + apply velocity + damping
      nodes.forEach(n => {
        const p = positions_state[n.id];
        if (!p) return;
        p.vx += (width / 2 - p.x) * 0.002;
        p.vy += (height / 2 - p.y) * 0.002;
        p.x = Math.max(30, Math.min(width - 30, p.x + p.vx));
        p.y = Math.max(30, Math.min(height - 30, p.y + p.vy));
        p.vx *= 0.85;
        p.vy *= 0.85;
      });
    }

    setPositions(positions_state);
  }, [nodes.length, edges.length]);

  return positions;
}

// Community color palette
const COMMUNITY_COLORS = [
  '#6366f1', '#ec4899', '#f59e0b', '#10b981',
  '#3b82f6', '#8b5cf6', '#ef4444', '#06b6d4',
  '#84cc16', '#f97316',
];

export default function NetworkGraph() {
  const [networkData, setNetworkData] = useState({ nodes: [], edges: [], stats: {} });
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hovered, setHovered] = useState(null);
  const svgRef = useRef(null);
  const W = 900, H = 580;

  const positions = useForceSimulation(networkData.nodes, networkData.edges, W, H);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [netRes, campRes] = await Promise.all([
          axios.get(`${API}/network`),
          axios.get(`${API}/network/campaigns`),
        ]);
        setNetworkData(netRes.data);
        setCampaigns(campRes.data.campaigns || []);
      } catch (e) {
        console.error('Network fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  const nodeRadius = (node) => {
    const base = 6;
    const pr = node.pagerank || 0;
    return base + pr * 200;
  };

  return (
    <div style={{ padding: '1.5rem', background: 'var(--bg-main)', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-dark)', margin: 0 }}>
          🕸️ Influence Network Graph
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.3rem', fontSize: '0.9rem' }}>
          Author interaction graph — node size = PageRank influence, color = community, red ring = bot-suspected
        </p>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {[
          { label: 'Nodes', value: networkData.stats?.total_nodes ?? 0 },
          { label: 'Edges', value: networkData.stats?.total_edges ?? 0 },
          { label: 'Communities', value: networkData.stats?.communities_count ?? 0 },
          { label: 'Campaigns', value: campaigns.length },
        ].map(s => (
          <div key={s.label} style={{
            background: 'var(--card-bg)', borderRadius: '10px', padding: '0.7rem 1.2rem',
            border: '1px solid var(--border-color)', minWidth: '100px',
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent)' }}>{s.value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem' }}>
        {/* SVG Graph */}
        <div style={{
          background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
          overflow: 'hidden', position: 'relative',
        }}>
          {loading && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(0,0,0,0.4)', zIndex: 10, borderRadius: '14px',
            }}>
              <div style={{ color: '#fff', fontSize: '1.1rem' }}>⏳ Building graph…</div>
            </div>
          )}

          {networkData.nodes.length === 0 && !loading ? (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              height: `${H}px`, color: 'var(--text-muted)', flexDirection: 'column', gap: '1rem',
            }}>
              <span style={{ fontSize: '3rem' }}>🕸️</span>
              <p>No interaction data yet. Posts with reply/quote/mention metadata will build the graph.</p>
            </div>
          ) : (
            <svg ref={svgRef} width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: 'block' }}>
              {/* Edges */}
              {networkData.edges.map((e, i) => {
                const ps = positions[e.source], pt = positions[e.target];
                if (!ps || !pt) return null;
                const edgeColor = e.type === 'retweet' ? '#f97316' : e.type === 'quote' ? '#6366f1' : '#64748b';
                return (
                  <line key={i}
                    x1={ps.x} y1={ps.y} x2={pt.x} y2={pt.y}
                    stroke={edgeColor} strokeOpacity={0.35}
                    strokeWidth={e.weight || 1}
                  />
                );
              })}

              {/* Nodes */}
              {networkData.nodes.map((node) => {
                const p = positions[node.id];
                if (!p) return null;
                const r = nodeRadius(node);
                const commColor = COMMUNITY_COLORS[node.community % COMMUNITY_COLORS.length] || '#64748b';
                const isBot = node.bot_score >= 0.6;
                const isSel = selectedNode?.id === node.id;
                const isHov = hovered === node.id;

                return (
                  <g key={node.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedNode(isSel ? null : node)}
                    onMouseEnter={() => setHovered(node.id)}
                    onMouseLeave={() => setHovered(null)}
                  >
                    {/* Bot ring */}
                    {isBot && (
                      <circle cx={p.x} cy={p.y} r={r + 4} fill="none" stroke="#ef4444"
                        strokeWidth={2} strokeDasharray="4 2" />
                    )}
                    {/* Selected ring */}
                    {isSel && (
                      <circle cx={p.x} cy={p.y} r={r + 7} fill="none" stroke="#fff"
                        strokeWidth={2} opacity={0.8} />
                    )}
                    {/* Main node */}
                    <circle cx={p.x} cy={p.y} r={isHov || isSel ? r + 2 : r}
                      fill={commColor}
                      opacity={0.9}
                      stroke={isSel ? '#fff' : 'rgba(0,0,0,0.3)'}
                      strokeWidth={1.5}
                    />
                    {/* Threat score inner dot */}
                    {node.max_threat_score > 0.7 && (
                      <circle cx={p.x} cy={p.y} r={Math.max(r * 0.35, 3)}
                        fill={threatColor(node.max_threat_score)} opacity={0.9} />
                    )}
                    {/* Label for prominent nodes */}
                    {(r > 10 || isSel || isHov) && (
                      <text x={p.x} y={p.y + r + 12} textAnchor="middle"
                        fontSize={isHov || isSel ? 11 : 9} fill="var(--text-dark)" opacity={0.8}>
                        {node.id.slice(0, 14)}{node.id.length > 14 ? '…' : ''}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          )}

          {/* Legend */}
          <div style={{ position: 'absolute', bottom: '12px', left: '12px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {[
              { label: 'Reply', color: '#64748b' },
              { label: 'Quote', color: '#6366f1' },
              { label: 'Retweet', color: '#f97316' },
            ].map(l => (
              <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <div style={{ width: 20, height: 2, background: l.color }} />
                {l.label}
              </div>
            ))}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', border: '2px dashed #ef4444' }} />
              Bot-suspected
            </div>
          </div>
        </div>

        {/* Side Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Node detail */}
          {selectedNode ? (
            <div style={{
              background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
              padding: '1rem',
            }}>
              <h3 style={{ margin: '0 0 0.75rem', color: 'var(--text-dark)', fontSize: '1rem' }}>
                👤 @{selectedNode.id}
              </h3>
              {[
                { label: 'PageRank', value: selectedNode.pagerank?.toFixed(4) },
                { label: 'Betweenness', value: selectedNode.betweenness?.toFixed(4) },
                { label: 'Community', value: `#${selectedNode.community}` },
                { label: 'Bot Score', value: `${(selectedNode.bot_score * 100).toFixed(0)}%` },
                { label: 'Max Threat', value: `${(selectedNode.max_threat_score * 100).toFixed(0)}%` },
                { label: 'Post Count', value: selectedNode.post_count },
                { label: 'Platforms', value: (selectedNode.platforms || []).join(', ') || '—' },
              ].map(r => (
                <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{r.label}</span>
                  <span style={{ color: 'var(--text-dark)', fontWeight: 600 }}>{r.value}</span>
                </div>
              ))}
              {selectedNode.bot_score >= 0.6 && (
                <div style={{
                  marginTop: '0.75rem', background: '#ef444420', border: '1px solid #ef4444',
                  borderRadius: '8px', padding: '0.5rem', fontSize: '0.8rem', color: '#ef4444',
                }}>
                  ⚠️ High bot likelihood — consider flagging this account
                </div>
              )}
            </div>
          ) : (
            <div style={{
              background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
              padding: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center',
            }}>
              Click a node to see account details
            </div>
          )}

          {/* Campaigns */}
          <div style={{
            background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
            padding: '1rem', maxHeight: '340px', overflowY: 'auto',
          }}>
            <h3 style={{ margin: '0 0 0.75rem', color: 'var(--text-dark)', fontSize: '1rem' }}>
              🎯 Coordination Campaigns
            </h3>
            {campaigns.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No campaigns detected yet.</p>
            ) : campaigns.map((c) => (
              <div key={c.campaign_id} style={{
                background: 'var(--bg-main)', borderRadius: '8px', padding: '0.7rem',
                marginBottom: '0.5rem', border: '1px solid var(--border-color)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {c.platforms?.join(', ')}
                  </span>
                  <span style={{
                    background: `${c.confidence > 0.7 ? '#ef4444' : '#f97316'}20`,
                    color: c.confidence > 0.7 ? '#ef4444' : '#f97316',
                    borderRadius: '999px', padding: '0.1rem 0.5rem', fontSize: '0.7rem', fontWeight: 700,
                  }}>
                    {(c.confidence * 100).toFixed(0)}% conf
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-dark)', lineHeight: 1.4 }}>
                  {c.narrative_summary?.slice(0, 90)}…
                </p>
                <div style={{ marginTop: '0.3rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  👥 {c.unique_accounts} accounts · 📊 {c.total_posts} posts · ⚡ {c.growth_rate}/hr
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
