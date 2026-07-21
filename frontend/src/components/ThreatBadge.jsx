import React from 'react';
import { AlertTriangle, ShieldCheck, Flame, HelpCircle } from 'lucide-react';

export default function ThreatBadge({ level }) {
  switch (level) {
    case 'Incitement to Violence':
      return (
        <span className="badge-threat badge-incitement">
          <AlertTriangle size={14} /> Incitement to Violence
        </span>
      );
    case 'Fake News':
      return (
        <span className="badge-threat badge-fake-news">
          <HelpCircle size={14} /> Fake News
        </span>
      );
    case 'Inflammatory':
      return (
        <span className="badge-threat badge-inflammatory">
          <Flame size={14} /> Inflammatory
        </span>
      );
    case 'Neutral':
    default:
      return (
        <span className="badge-threat badge-neutral">
          <ShieldCheck size={14} /> Neutral
        </span>
      );
  }
}
