import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000/api/v1';

// Gujarat district approximate center coordinates for SVG map
const DISTRICT_SVG_POSITIONS = {
  'Kutch': { x: 120, y: 100 },
  'Banaskantha': { x: 230, y: 80 },
  'Patan': { x: 240, y: 130 },
  'Mahesana': { x: 270, y: 160 },
  'Mehsana': { x: 270, y: 160 },
  'Gandhinagar': { x: 300, y: 200 },
  'Ahmedabad': { x: 300, y: 230 },
  'Anand': { x: 330, y: 270 },
  'Vadodara': { x: 340, y: 310 },
  'Panchmahal': { x: 380, y: 290 },
  'Dahod': { x: 420, y: 300 },
  'Rajkot': { x: 190, y: 240 },
  'Surendranagar': { x: 230, y: 210 },
  'Bhavnagar': { x: 250, y: 310 },
  'Amreli': { x: 210, y: 340 },
  'Junagadh': { x: 170, y: 370 },
  'Porbandar': { x: 120, y: 360 },
  'Jamnagar': { x: 140, y: 280 },
  'Dwarka': { x: 90, y: 300 },
  'Surat': { x: 310, y: 390 },
  'Navsari': { x: 340, y: 420 },
  'Valsad': { x: 360, y: 450 },
  'Bharuch': { x: 310, y: 350 },
  'Narmada': { x: 360, y: 330 },
};

function riskColor(eri) {
  if (eri >= 75) return '#ef4444';
  if (eri >= 50) return '#f97316';
  if (eri >= 25) return '#eab308';
  return '#22c55e';
}

function riskLabel(eri) {
  if (eri >= 75) return 'CRITICAL';
  if (eri >= 50) return 'HIGH';
  if (eri >= 25) return 'MEDIUM';
  return 'LOW';
}

export default function MapView() {
  const [riskIndex, setRiskIndex] = useState([]);
  const [districtStats, setDistrictStats] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterDistrict, setFilterDistrict] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [riRes, dsRes] = await Promise.all([
          axios.get(`${API}/geo/risk-index`),
          axios.get(`${API}/geo/districts`),
        ]);
        setRiskIndex(riRes.data.risk_index || []);
        setDistrictStats(dsRes.data.districts || []);
      } catch (e) {
        console.error('Map fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  const eriMap = {};
  riskIndex.forEach(r => { eriMap[r.district] = r; });

  const statsMap = {};
  districtStats.forEach(s => { statsMap[s.district] = s; });

  const selectedERI = selectedDistrict ? eriMap[selectedDistrict] : null;
  const selectedStats = selectedDistrict ? statsMap[selectedDistrict] : null;

  const filteredRisk = filterDistrict
    ? riskIndex.filter(r => r.district.toLowerCase().includes(filterDistrict.toLowerCase()))
    : riskIndex;

  return (
    <div style={{ padding: '1.5rem', background: 'var(--bg-main)', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-dark)', margin: 0 }}>
          🗺️ Gujarat Threat Map
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.3rem', fontSize: '0.9rem' }}>
          Escalation Risk Index per district — updated every 60s. Click a district for details.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem' }}>
        {/* Map area — SVG bubble map */}
        <div style={{
          background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
          padding: '1rem', position: 'relative', minHeight: '520px',
        }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '480px', color: 'var(--text-muted)' }}>
              ⏳ Loading risk data…
            </div>
          ) : (
            <svg width="100%" viewBox="0 0 520 520" style={{ display: 'block' }}>
              {/* Background */}
              <rect width="520" height="520" fill="transparent" />

              {/* District bubbles */}
              {Object.entries(DISTRICT_SVG_POSITIONS).map(([dist, pos]) => {
                const eri_data = eriMap[dist];
                const stat = statsMap[dist];
                const eri = eri_data?.eri ?? 0;
                const count = stat?.count ?? 0;
                const color = riskColor(eri);
                const r = Math.max(16, Math.min(40, 16 + count * 3));
                const isSelected = selectedDistrict === dist;

                return (
                  <g key={dist} style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedDistrict(isSelected ? null : dist)}>
                    {/* Pulse ring for high-risk */}
                    {eri >= 50 && (
                      <circle cx={pos.x} cy={pos.y} r={r + 8}
                        fill="none" stroke={color} strokeWidth={1.5} opacity={0.4}
                        style={{ animation: 'pulse 2s infinite' }} />
                    )}
                    {/* Selection ring */}
                    {isSelected && (
                      <circle cx={pos.x} cy={pos.y} r={r + 5}
                        fill="none" stroke="#fff" strokeWidth={2} />
                    )}
                    {/* Main bubble */}
                    <circle cx={pos.x} cy={pos.y} r={r}
                      fill={color} opacity={0.85}
                      stroke={isSelected ? '#fff' : 'rgba(0,0,0,0.2)'}
                      strokeWidth={isSelected ? 2 : 1}
                    />
                    {/* ERI label */}
                    <text x={pos.x} y={pos.y + 1} textAnchor="middle"
                      dominantBaseline="middle" fill="#fff"
                      fontSize={eri >= 10 ? 11 : 9} fontWeight={700}>
                      {eri > 0 ? Math.round(eri) : '—'}
                    </text>
                    {/* District name */}
                    <text x={pos.x} y={pos.y + r + 13} textAnchor="middle"
                      fill="var(--text-dark)" fontSize={9} opacity={0.8}>
                      {dist.length > 10 ? dist.slice(0, 10) + '…' : dist}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}

          {/* Legend */}
          <div style={{ position: 'absolute', bottom: '16px', left: '16px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {[
              { label: 'CRITICAL ≥75', color: '#ef4444' },
              { label: 'HIGH ≥50', color: '#f97316' },
              { label: 'MEDIUM ≥25', color: '#eab308' },
              { label: 'LOW <25', color: '#22c55e' },
            ].map(l => (
              <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <div style={{ width: 12, height: 12, borderRadius: '50%', background: l.color }} />
                {l.label}
              </div>
            ))}
          </div>

          <style>{`
            @keyframes pulse {
              0%, 100% { opacity: 0.4; transform-origin: center; transform: scale(1); }
              50% { opacity: 0.2; transform: scale(1.15); }
            }
          `}</style>
        </div>

        {/* Right Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* District Detail */}
          {selectedDistrict && selectedERI ? (
            <div style={{
              background: 'var(--card-bg)', borderRadius: '14px', border: `2px solid ${riskColor(selectedERI.eri)}`,
              padding: '1rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ margin: 0, color: 'var(--text-dark)', fontSize: '1.1rem' }}>📍 {selectedDistrict}</h3>
                <span style={{
                  background: `${riskColor(selectedERI.eri)}20`,
                  color: riskColor(selectedERI.eri),
                  borderRadius: '999px', padding: '0.2rem 0.8rem', fontSize: '0.8rem', fontWeight: 700,
                }}>
                  {riskLabel(selectedERI.eri)}
                </span>
              </div>

              {/* ERI Score */}
              <div style={{ textAlign: 'center', padding: '0.5rem 0', marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '3rem', fontWeight: 800, color: riskColor(selectedERI.eri) }}>
                  {selectedERI.eri}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Escalation Risk Index
                  {selectedERI.trend === 'rising' ? ' 📈' : selectedERI.trend === 'falling' ? ' 📉' : ' ➡️'}
                </div>
              </div>

              {/* Components breakdown */}
              {selectedERI.components && Object.entries(selectedERI.components)
                .filter(([k]) => k !== 'sensitivity_multiplier')
                .map(([key, val]) => (
                  <div key={key} style={{ marginBottom: '0.4rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                      <span>{key.replace(/_/g, ' ')}</span>
                      <span>{Math.round(val)}%</span>
                    </div>
                    <div style={{ height: 4, background: 'var(--border-color)', borderRadius: 4 }}>
                      <div style={{
                        height: 4, borderRadius: 4,
                        width: `${Math.min(val, 100)}%`,
                        background: val >= 70 ? '#ef4444' : val >= 40 ? '#f97316' : '#22c55e',
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                ))}

              {/* Post stats */}
              {selectedStats && (
                <div style={{ marginTop: '0.75rem', padding: '0.6rem', background: 'var(--bg-main)', borderRadius: '8px', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Total posts</span>
                    <span style={{ fontWeight: 700 }}>{selectedStats.count}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Avg threat</span>
                    <span style={{ fontWeight: 700, color: threatColor(selectedStats.avg_threat) }}>
                      {(selectedStats.avg_threat * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Critical alerts</span>
                    <span style={{ fontWeight: 700, color: '#ef4444' }}>{selectedStats.critical_count}</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{
              background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
              padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem',
            }}>
              🗺️ Click a district bubble to see its Escalation Risk Index breakdown
            </div>
          )}

          {/* District Risk Ranking */}
          <div style={{
            background: 'var(--card-bg)', borderRadius: '14px', border: '1px solid var(--border-color)',
            padding: '1rem', flex: 1, overflowY: 'auto', maxHeight: '320px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ margin: 0, color: 'var(--text-dark)', fontSize: '0.95rem' }}>📊 District Ranking</h3>
            </div>
            <input
              type="text" placeholder="Filter district…"
              value={filterDistrict}
              onChange={e => setFilterDistrict(e.target.value)}
              style={{
                width: '100%', padding: '0.4rem 0.6rem', marginBottom: '0.5rem',
                background: 'var(--bg-main)', border: '1px solid var(--border-color)',
                borderRadius: '6px', color: 'var(--text-dark)', fontSize: '0.82rem',
                boxSizing: 'border-box',
              }}
            />
            {filteredRisk.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No district data yet.</p>
            ) : filteredRisk.map((r, i) => (
              <div key={r.district}
                onClick={() => setSelectedDistrict(r.district)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  padding: '0.4rem 0.5rem', borderRadius: '6px', marginBottom: '2px',
                  cursor: 'pointer', background: selectedDistrict === r.district ? 'var(--bg-main)' : 'transparent',
                  transition: 'background 0.2s',
                }}>
                <span style={{ width: '18px', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                  {i + 1}
                </span>
                <div style={{ flex: 1, fontSize: '0.82rem', color: 'var(--text-dark)' }}>{r.district}</div>
                <div style={{ width: '50px', height: 4, background: 'var(--border-color)', borderRadius: 4 }}>
                  <div style={{
                    height: 4, borderRadius: 4,
                    width: `${r.eri}%`,
                    background: riskColor(r.eri),
                    transition: 'width 0.5s ease',
                  }} />
                </div>
                <span style={{ width: '30px', textAlign: 'right', fontSize: '0.8rem', fontWeight: 700, color: riskColor(r.eri) }}>
                  {Math.round(r.eri)}
                </span>
                <span style={{ fontSize: '0.65rem', color: r.trend === 'rising' ? '#ef4444' : r.trend === 'falling' ? '#22c55e' : 'var(--text-muted)' }}>
                  {r.trend === 'rising' ? '↑' : r.trend === 'falling' ? '↓' : '→'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function threatColor(score) {
  if (score >= 0.85) return '#ef4444';
  if (score >= 0.70) return '#f97316';
  if (score >= 0.50) return '#eab308';
  return '#22c55e';
}
