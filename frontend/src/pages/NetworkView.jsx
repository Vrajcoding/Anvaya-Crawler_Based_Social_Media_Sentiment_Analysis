import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import { fetchNetworkGraph, fetchBotClusters } from '../services/api';
import { Network, Bot, Cpu, Share2, ShieldAlert } from 'lucide-react';

export default function NetworkView() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [botClusters, setBotClusters] = useState([]);

  const loadNetworkData = async () => {
    try {
      const g = await fetchNetworkGraph();
      const b = await fetchBotClusters();
      setGraphData(g || { nodes: [], links: [] });
      setBotClusters(b || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadNetworkData();
  }, []);

  return (
    <div>
      <Header 
        title="Network Analysis & Bot Coordination Map" 
        subtitle="Graph intelligence mapping account relationships, coordinated retweets, and bot cluster amplification"
        onRefresh={loadNetworkData}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        
        {/* GRAPH CANVAS SIMULATION PANEL */}
        <div className="card-glass">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network color="var(--accent-cyan)" size={20} /> Account & Post Relationship Graph ({graphData.nodes.length} Nodes)
          </h3>

          <div className="graph-container" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', background: '#0f172a', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
              🟢 Account Node | 🔴 High Threat Post Node | 🟣 Bot Cluster Account | ⚡ Edge: Coordinated Sharing
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
              {graphData.nodes.map((n, i) => (
                <div 
                  key={i} 
                  style={{
                    background: n.is_bot ? 'rgba(168, 85, 247, 0.15)' : (n.type === 'post' ? 'rgba(239, 68, 68, 0.15)' : '#1e293b'),
                    border: `1px solid ${n.is_bot ? '#a855f7' : (n.type === 'post' ? '#ef4444' : 'var(--border-color)')}`,
                    padding: '0.85rem',
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#fff', wordBreak: 'break-all' }}>
                    {n.is_bot ? '🤖 ' : (n.type === 'post' ? '📝 ' : '👤 ')}
                    {n.label}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Type: {n.type} | Platform: {n.platform?.toUpperCase()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* DETECTED BOT CLUSTERS PANEL */}
        <div className="card-glass">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: '#a855f7', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={20} /> Active Bot Clusters ({botClusters.length})
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {botClusters.length === 0 ? (
              <div style={{ color: 'var(--text-dim)', fontSize: '0.9rem', textAlign: 'center', padding: '2rem' }}>
                No active bot clusters detected.
              </div>
            ) : (
              botClusters.map((cluster, idx) => (
                <div key={idx} style={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.4)', borderRadius: '8px', padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#c084fc' }}>{cluster.cluster_id}</span>
                    <span style={{ background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
                      {cluster.account_count} BOTS SYNCED
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                    Linked Accounts: {cluster.accounts.join(', ')}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
