import React, { useEffect, useState } from 'react';
import { fetchNetworkGraph, fetchBotClusters } from '../services/api';
import { Network, Bot, ShieldAlert, Cpu, Share2, Info, CheckCircle2, Zap } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function NetworkView() {
  const { t, lang } = useLanguage();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [botClusters, setBotClusters] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeView, setActiveView] = useState('graph'); // 'graph' or 'grid'

  const loadNetworkData = async () => {
    try {
      const g = await fetchNetworkGraph();
      const b = await fetchBotClusters();
      setGraphData(g || { nodes: [], links: [] });
      setBotClusters(b || []);
      if (g && g.nodes && g.nodes.length > 0 && !selectedNode) {
        setSelectedNode(g.nodes[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadNetworkData();
    const interval = setInterval(loadNetworkData, 10000);
    return () => clearInterval(interval);
  }, []);

  // Compute layout coordinates for SVG visualization
  const computeGraphPositions = () => {
    const nodes = graphData.nodes || [];
    const links = graphData.links || [];
    const width = 680;
    const height = 480;
    const centerX = width / 2;
    const centerY = height / 2;

    const positionedNodes = nodes.map((n, i) => {
      const angle = (i / Math.max(nodes.length, 1)) * 2 * Math.PI;
      const radius = n.is_bot ? 180 : (n.type === 'post' ? 110 : 60);
      return {
        ...n,
        cx: centerX + radius * Math.cos(angle) + (Math.sin(angle * 3) * 15),
        cy: centerY + radius * Math.sin(angle) + (Math.cos(angle * 2) * 15)
      };
    });

    const positionedLinks = links.map((l) => {
      const sourceNode = positionedNodes.find(n => n.id === l.source || n.label === l.source) || positionedNodes[0];
      const targetNode = positionedNodes.find(n => n.id === l.target || n.label === l.target) || positionedNodes[Math.min(1, positionedNodes.length - 1)];
      return {
        ...l,
        x1: sourceNode?.cx || centerX,
        y1: sourceNode?.cy || centerY,
        x2: targetNode?.cx || centerX,
        y2: targetNode?.cy || centerY,
        type: l.type || 'amplification'
      };
    });

    return { positionedNodes, positionedLinks, width, height };
  };

  const { positionedNodes, positionedLinks, width, height } = computeGraphPositions();

  return (
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>🌐 {t('nav_network')}</h2>
          <p>{lang === 'hi' ? 'समन्वित बॉटनेट, प्रवर्धन रिंग व सोशल मीडिया संदिग्ध खातों का लाइव विज़ुअलाइज़ेशन' : 'Interactive Force-Directed Graph Mapping Coordinated Botnets & Amplification Rings'}</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setActiveView('graph')}
            className={`px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-all ${activeView === 'graph' ? 'bg-indigo-700 text-white shadow-md' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'}`}
          >
            <Share2 size={16} /> {lang === 'hi' ? 'इंटरेक्टिव ग्राफ़ व्यू' : 'Interactive Graph View'}
          </button>
          <button
            onClick={() => setActiveView('grid')}
            className={`px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-all ${activeView === 'grid' ? 'bg-indigo-700 text-white shadow-md' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'}`}
          >
            <Network size={16} /> {lang === 'hi' ? 'कार्ड ग्रिड व्यू' : 'Card Grid View'}
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        
        {/* LEFT COLUMN: GRAPH / GRID VISUALIZATION */}
        <div className="gov-card">
          <div className="gov-card-title flex justify-between items-center">
            <span>🌐 {activeView === 'graph' ? (lang === 'hi' ? 'सक्रिय संदिग्ध नोड कनेक्शन (SVG Force Layout)' : 'Active Threat Graph Mapping') : (lang === 'hi' ? 'पहचाने गए संदिग्ध नोड्स ग्रिड' : 'Identified Threat Nodes Grid')} ({graphData.nodes.length} Nodes)</span>
            <span className="text-xs font-mono bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full border border-indigo-200">
              ⚡ Hermes NetworkAgent Analysis Active
            </span>
          </div>

          <div style={{ background: '#f8fafc', padding: '0.8rem 1rem', borderRadius: '8px', border: '1px solid var(--border-gov)', marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            🟢 <strong>{lang === 'hi' ? 'लीजेंड:' : 'Legend:'}</strong> 🔴 <span className="text-red-600 font-bold">Bot Accounts</span> | 🟠 <span className="text-amber-600 font-bold">Viral Posts</span> | 🔵 <span className="text-blue-600 font-bold">Verified/Standard Accounts</span> | ⚡ Click any node to inspect telemetry
          </div>

          {activeView === 'graph' ? (
            <div className="bg-slate-900 rounded-xl p-4 border-2 border-slate-700 relative overflow-hidden shadow-inner flex items-center justify-center">
              <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-[450px] max-w-full">
                {/* Background grid lines */}
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#334155" strokeWidth="0.5" strokeOpacity="0.4" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />

                {/* Connecting Links */}
                {positionedLinks.map((l, idx) => (
                  <g key={`link-${idx}`}>
                    <line
                      x1={l.x1}
                      y1={l.y1}
                      x2={l.x2}
                      y2={l.y2}
                      stroke={l.type === 'bot_coordination' ? '#ef4444' : '#6366f1'}
                      strokeWidth={l.type === 'bot_coordination' ? 2.5 : 1.5}
                      strokeDasharray={l.type === 'bot_coordination' ? '4 2' : 'none'}
                      strokeOpacity="0.75"
                    />
                    <circle cx={(l.x1 + l.x2) / 2} cy={(l.y1 + l.y2) / 2} r="2.5" fill="#38bdf8" />
                  </g>
                ))}

                {/* Nodes */}
                {positionedNodes.map((n, idx) => {
                  const isSelected = selectedNode && selectedNode.id === n.id;
                  const nodeColor = n.is_bot ? '#ef4444' : (n.type === 'post' ? '#f97316' : '#3b82f6');
                  const strokeColor = isSelected ? '#ffffff' : (n.is_bot ? '#991b1b' : '#1e3a8a');
                  const radius = isSelected ? 22 : (n.is_bot ? 17 : 14);

                  return (
                    <g key={`node-${idx}`} className="cursor-pointer transition-transform hover:scale-110" onClick={() => setSelectedNode(n)}>
                      {isSelected && (
                        <circle cx={n.cx} cy={n.cy} r={radius + 8} fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="3 3" className="animate-spin" style={{ transformOrigin: `${n.cx}px ${n.cy}px` }} />
                      )}
                      {n.is_bot && (
                        <circle cx={n.cx} cy={n.cy} r={radius + 4} fill={nodeColor} fillOpacity="0.2" className="animate-pulse" />
                      )}
                      <circle cx={n.cx} cy={n.cy} r={radius} fill={nodeColor} stroke={strokeColor} strokeWidth={isSelected ? 3 : 2} />
                      <text x={n.cx} y={n.cy + radius + 14} textAnchor="middle" fill="#e2e8f0" fontSize="11" fontWeight="bold" className="pointer-events-none drop-shadow">
                        {n.label?.slice(0, 14)}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.85rem' }}>
              {graphData.nodes.map((n, i) => (
                <div 
                  key={i} 
                  onClick={() => setSelectedNode(n)}
                  className="cursor-pointer transition-all hover:shadow-md"
                  style={{
                    background: selectedNode?.id === n.id ? '#eff6ff' : (n.is_bot ? '#fef2f2' : (n.type === 'post' ? '#fff7ed' : '#ffffff')),
                    border: `2px solid ${selectedNode?.id === n.id ? '#2563eb' : (n.is_bot ? '#f87171' : (n.type === 'post' ? '#fb923c' : 'var(--border-gov)'))}`,
                    padding: '1rem',
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--gov-navy-dark)', wordBreak: 'break-all' }}>
                    {n.is_bot ? '🤖 ' : (n.type === 'post' ? '📝 ' : '👤 ')}
                    {n.label}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px', fontWeight: 600 }}>
                    प्रकार: {n.type} | {t('wl_platform')}: {n.platform?.toUpperCase()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: INSPECTOR & BOT CLUSTERS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* NODE INSPECTOR PANEL */}
          {selectedNode ? (
            <div className="gov-card border-2 border-indigo-200 bg-indigo-50/40">
              <div className="gov-card-title flex items-center gap-2 text-indigo-900">
                <Info className="w-5 h-5 text-indigo-600" />
                <span>{lang === 'hi' ? 'नोड विस्तृत विवरण' : 'Selected Node Inspector'}</span>
              </div>

              <div className="space-y-3 pt-2 text-sm">
                <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-xs">
                  <span className="text-xs text-gray-500 font-bold uppercase block">{lang === 'hi' ? 'पहचानकर्ता' : 'Entity Identifier'}</span>
                  <span className="text-base font-bold text-gray-900 break-all">{selectedNode.label}</span>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white p-2.5 rounded-lg border border-gray-200">
                    <span className="text-xs text-gray-500 block">{lang === 'hi' ? 'प्रकार' : 'Node Type'}</span>
                    <span className="font-bold text-indigo-700 capitalize">{selectedNode.type}</span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-gray-200">
                    <span className="text-xs text-gray-500 block">{lang === 'hi' ? 'प्लेटफ़ॉर्म' : 'Platform'}</span>
                    <span className="font-bold text-gray-800 uppercase">{selectedNode.platform || 'General'}</span>
                  </div>
                </div>

                <div className={`p-3 rounded-lg border flex items-center justify-between ${selectedNode.is_bot ? 'bg-red-50 border-red-300 text-red-900' : 'bg-emerald-50 border-emerald-300 text-emerald-900'}`}>
                  <span className="font-bold">{lang === 'hi' ? 'बॉट वर्गीकरण:' : 'Bot Assessment:'}</span>
                  <span className="px-2.5 py-0.5 rounded font-extrabold text-xs bg-white shadow-xs">
                    {selectedNode.is_bot ? '🚨 IDENTIFIED BOTNET ACCOUNT' : '✅ HUMAN / LEGITIMATE'}
                  </span>
                </div>

                {selectedNode.threat_level && (
                  <div className="bg-white p-3 rounded-lg border border-gray-200">
                    <span className="text-xs text-gray-500 block">{lang === 'hi' ? 'थ्रेट स्तर' : 'Threat Level'}</span>
                    <span className="font-bold text-red-600">{selectedNode.threat_level}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="gov-card p-6 text-center text-gray-500">
              {lang === 'hi' ? 'विस्तृत जानकारी देखने के लिए ग्राफ़ में किसी नोड पर क्लिक करें।' : 'Click any node on the graph or grid to inspect intelligence telemetry.'}
            </div>
          )}

          {/* DETECTED BOT CLUSTERS */}
          <div className="gov-card">
            <div className="gov-card-title" style={{ color: '#7e22ce' }}>
              <span>🤖 {lang === 'hi' ? 'सक्रिय बॉट क्लस्टर्स' : 'Detected Bot Clusters'} ({botClusters.length})</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
              {botClusters.length === 0 ? (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '1.5rem', fontWeight: 600 }}>
                  {t('alert_status_resolved')}
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
    </div>
  );
}
