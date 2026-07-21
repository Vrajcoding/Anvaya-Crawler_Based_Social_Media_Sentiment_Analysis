import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import { fetchWatchlist, addWatchlistItem, deleteWatchlistItem } from '../services/api';
import { Eye, Plus, Trash2, Tag, User, MapPin } from 'lucide-react';

export default function Watchlist() {
  const [items, setItems] = useState([]);
  const [value, setValue] = useState('');
  const [type, setType] = useState('keyword');
  const [platform, setPlatform] = useState('all');
  const [geo, setGeo] = useState('Gujarat');
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
    <div>
      <Header 
        title="Watchlist Manager" 
        subtitle="Manage targeted keywords, regional hashtags, and flagged profiles for continuous crawling"
        onRefresh={loadWatchlist}
      />

      {/* ADD NEW WATCHLIST ENTRY */}
      <div className="card-glass" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus color="var(--accent-cyan)" size={20} /> Add New Monitoring Target
        </h3>

        <form onSubmit={handleAdd} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr auto', gap: '0.75rem', alignItems: 'center' }}>
          <input 
            type="text" 
            placeholder="Keyword, #hashtag, or @profile"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            style={{ background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.6rem 0.85rem', borderRadius: '6px', outline: 'none' }}
          />

          <select value={type} onChange={(e) => setType(e.target.value)} style={{ background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.6rem 0.85rem', borderRadius: '6px' }}>
            <option value="keyword">Keyword</option>
            <option value="hashtag">Hashtag</option>
            <option value="profile">Profile</option>
          </select>

          <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.6rem 0.85rem', borderRadius: '6px' }}>
            <option value="all">All Platforms</option>
            <option value="x">X (Twitter)</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="youtube">YouTube</option>
          </select>

          <input 
            type="text" 
            placeholder="Geo Location"
            value={geo}
            onChange={(e) => setGeo(e.target.value)}
            style={{ background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.6rem 0.85rem', borderRadius: '6px' }}
          />

          <select value={priority} onChange={(e) => setPriority(e.target.value)} style={{ background: '#090d16', border: '1px solid var(--border-color)', color: '#fff', padding: '0.6rem 0.85rem', borderRadius: '6px' }}>
            <option value="high">High Priority</option>
            <option value="normal">Normal</option>
            <option value="low">Low Priority</option>
          </select>

          <button type="submit" className="btn-primary">
            <Plus size={16} /> Add Target
          </button>
        </form>
      </div>

      {/* WATCHLIST ITEMS TABLE */}
      <div className="card-glass">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Active Watchlist Targets ({items.length})</h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {items.map((item) => (
            <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1e293b', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid var(--accent-cyan)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1.05rem', color: '#fff' }}>{item.value}</span>
                <span className="badge-lang" style={{ textTransform: 'uppercase' }}>{item.type}</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Platform: {item.platform.toUpperCase()}</span>
                {item.geo_target && (
                  <span style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                    <MapPin size={14} /> {item.geo_target}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ background: item.priority === 'high' ? 'rgba(239,68,68,0.2)' : 'rgba(59,130,246,0.2)', color: item.priority === 'high' ? '#ef4444' : '#3b82f6', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
                  {item.priority.toUpperCase()} PRIORITY
                </span>

                <button className="btn-secondary" style={{ color: '#ef4444', borderColor: 'rgba(239,68,68,0.4)', padding: '0.4rem 0.75rem' }} onClick={() => handleDelete(item.id)}>
                  <Trash2 size={14} /> Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
