import React, { useEffect, useState } from 'react';
import { fetchWatchlist, addWatchlistItem, deleteWatchlistItem } from '../services/api';
import { Plus, Trash2, MapPin, Eye } from 'lucide-react';

export default function Watchlist() {
  const [items, setItems] = useState([]);
  const [value, setValue] = useState('');
  const [type, setType] = useState('keyword');
  const [platform, setPlatform] = useState('all');
  const [geo, setGeo] = useState('Surat, Gujarat');
  const [priority, setPriority] = useState('high');

  const loadWatchlist = async () => {
    try {
      const data = await fetchWatchlist();
      setItems(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    await addWatchlistItem({
      value,
      type,
      platform,
      geo_target: geo,
      priority,
      active: true
    });
    setValue('');
    loadWatchlist();
  };

  const handleDelete = async (id) => {
    await deleteWatchlistItem(id);
    loadWatchlist();
  };

  return (
    <div className="gov-container">
      <div className="page-title-banner">
        <div>
          <h2>🎯 निगरानी सूची प्रबंधक (Target Watchlist Manager)</h2>
          <p>विशेष निगरानी हेतु संवेदनशील कीवर्ड, हैशटैग एवं संदिग्ध सोशल प्रोफाइल जोड़ें</p>
        </div>
      </div>

      {/* ADD NEW FORM */}
      <div className="gov-card" style={{ border: '2px solid var(--gov-navy)' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus size={20} color="var(--gov-navy)" /> नया निगरानी लक्ष्य जोड़ें (Add New Watchlist Target)
        </h3>

        <form onSubmit={handleAdd} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr auto', gap: '0.85rem', alignItems: 'center' }}>
          <input 
            type="text" 
            placeholder="कीवर्ड, #हैशटैग, या @प्रोफाइल नाम दर्ज करें"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            style={{ border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem', outline: 'none' }}
          />

          <select value={type} onChange={(e) => setType(e.target.value)} style={{ border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem', fontWeight: 600 }}>
            <option value="keyword">कीवर्ड (Keyword)</option>
            <option value="hashtag">हैशटैग (#Hashtag)</option>
            <option value="profile">प्रोफाइल (@Profile)</option>
          </select>

          <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem', fontWeight: 600 }}>
            <option value="all">सभी प्लेटफ़ॉर्म (All)</option>
            <option value="x">X (Twitter)</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="youtube">YouTube</option>
          </select>

          <input 
            type="text" 
            placeholder="स्थान (Location)"
            value={geo}
            onChange={(e) => setGeo(e.target.value)}
            style={{ border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem' }}
          />

          <select value={priority} onChange={(e) => setPriority(e.target.value)} style={{ border: '2px solid var(--border-gov)', padding: '0.75rem', borderRadius: '6px', fontSize: '1rem', fontWeight: 600 }}>
            <option value="high">उच्च प्राथमिकता (High)</option>
            <option value="normal">सामान्य (Normal)</option>
          </select>

          <button type="submit" className="btn-gov-primary">
            <Plus size={18} /> जोड़ें (Add)
          </button>
        </form>
      </div>

      {/* WATCHLIST LIST */}
      <div className="gov-card">
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--gov-navy-dark)', marginBottom: '1rem' }}>
          वर्तमान निगरानी सूची ({items.length} Targets Active)
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {items.map((item) => (
            <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '1.25rem', borderRadius: '8px', borderLeft: '6px solid var(--gov-navy)', border: '1px solid var(--border-gov)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <span style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--gov-navy-dark)' }}>{item.value}</span>
                <span style={{ background: '#e2e8f0', color: '#1e293b', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 800 }}>{item.type.toUpperCase()}</span>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 600 }}>प्लेटफ़ॉर्म: {item.platform.toUpperCase()}</span>
                {item.geo_target && (
                  <span style={{ fontSize: '0.9rem', color: 'var(--gov-navy)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={16} /> {item.geo_target}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ background: item.priority === 'high' ? '#fef2f2' : '#eff6ff', color: item.priority === 'high' ? '#dc2626' : '#1e3a8a', padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 800, border: `1px solid ${item.priority === 'high' ? '#f87171' : '#93c5fd'}` }}>
                  {item.priority.toUpperCase()} PRIORITY
                </span>

                <button className="btn-gov-secondary" style={{ color: '#dc2626', borderColor: '#f87171', padding: '0.4rem 0.8rem' }} onClick={() => handleDelete(item.id)}>
                  <Trash2 size={16} /> हटाएं (Remove)
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
