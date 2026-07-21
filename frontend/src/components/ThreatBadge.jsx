import React from 'react';
import { AlertTriangle, HelpCircle, ShieldCheck, Flame } from 'lucide-react';

export default function ThreatBadge({ level }) {
  switch (level) {
    case 'Incitement to Violence':
      return (
        <span className="gov-badge gov-badge-critical">
          <AlertTriangle size={16} /> हिंसा भड़काना / Incitement to Violence
        </span>
      );
    case 'Fake News':
      return (
        <span className="gov-badge gov-badge-fake">
          <HelpCircle size={16} /> झूठी खबर / Fake News / અફવા
        </span>
      );
    case 'Inflammatory':
      return (
        <span className="gov-badge gov-badge-inflammatory">
          <Flame size={16} /> भड़काऊ संदेश / Inflammatory
        </span>
      );
    case 'Neutral':
    default:
      return (
        <span className="gov-badge gov-badge-safe">
          <ShieldCheck size={16} /> सामान्य संदेश / Safe & Neutral
        </span>
      );
  }
}
