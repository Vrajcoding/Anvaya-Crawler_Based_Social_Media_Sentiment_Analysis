import React, { useEffect, useState } from 'react';
import { fetchNetworkGraph, fetchBotClusters } from '../services/api';
import { Network, Bot, ShieldAlert, Cpu } from 'lucide-react';

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
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>🕸️ संदिग्ध गैंग व बॉट नेटवर्क विश्लेषक (Bot & Network Coordination Tracker)</h2>
          <p>एक साथ अफवाह फैलाने वाले फेक अकाउंट्स एवं संगठित साइबर गिरोहों का नेटवर्क ग्राफ</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        
        {/* NETWORK NODES GRID */}
        <div className="gov-card">
          <div className="gov-card-title">
            <span>🌐 संदिग्ध खातों का नेटवर्क मानचित्र ({graphData.nodes.length} Nodes Identified)</span>
          </div>

          <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-gov)', marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            🟢 सामान्य यूजर | 🔴 उच्च-खतरा पोस्ट | 🤖 ऑटोमेटेड बॉट खाता | ⚡ एक साथ रिट्वीट / शेयर नेटवर्क
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.85rem' }}>
            {graphData.nodes.map((n, i) => (
              <div 
                key={i} 
                style={{
                  background: n.is_bot ? '#fef2f2' : (n.type === 'post' ? '#fff7ed' : '#ffffff'),
                  border: `2px solid ${n.is_bot ? '#f87171' : (n.type === 'post' ? '#fb923c' : 'var(--border-gov)')}`,
                  padding: '1rem',
                  borderRadius: '8px'
                }}
              >
                <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--gov-navy-dark)', wordBreak: 'break-all' }}>
                  {n.is_bot ? '🤖 ' : (n.type === 'post' ? '📝 ' : '👤 ')}
                  {n.label}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px', fontWeight: 600 }}>
                  प्रकार: {n.type} | प्लेटफ़ॉर्म: {n.platform?.toUpperCase()}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* DETECTED BOT CLUSTERS */}
        <div className="gov-card">
          <div className="gov-card-title" style={{ color: '#7e22ce' }}>
            <span>🤖 स्वचालित बॉट गैंग्स ({botClusters.length})</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {botClusters.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: '2rem', fontWeight: 600 }}>
                कोई संगठित बॉट क्लस्टर दर्ज नहीं है।
              </div>
            ) : (
              botClusters.map((cluster, idx) => (
                <div key={idx} style={{ background: '#f3e8ff', border: '2px solid #c084fc', borderRadius: '8px', padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 800, color: '#6b21a8', fontSize: '1rem' }}>{cluster.cluster_id}</span>
                    <span style={{ background: '#7e22ce', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 800 }}>
                      {cluster.account_count} बॉट्स जुड़े हैं
                    </span>
                  </div>

                  <div style={{ fontSize: '0.9rem', color: '#4c1d95', marginTop: '0.5rem', fontWeight: 600 }}>
                    शामिल यूजर एकाउंट्स: {cluster.accounts.join(', ')}
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
