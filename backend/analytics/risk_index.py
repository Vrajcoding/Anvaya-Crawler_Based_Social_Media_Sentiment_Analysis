"""
analytics/risk_index.py
⭐ Flagship Feature 4.1: "Rumour-to-Riot Early-Warning Escalation Risk Index"

Computes a per-district Escalation Risk Index (ERI) 0–100.
Components:
  - Threat-language volume (normalized post count with high threat scores)
  - Growth rate (recent hour vs baseline)
  - Bot/coordination share (% of posts from bot/coordinated accounts)
  - Cross-platform echo (same narrative on multiple platforms)
  - Call-to-action density (posts with time+place+action phrases)
  - Historical sensitivity (district sensitivity weight — manual calibration)

Updated every crawl cycle and exposed via /api/v1/risk-index endpoint.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# Historical sensitivity weights for Gujarat districts (1.0 = average)
DISTRICT_SENSITIVITY = {
    "Ahmedabad": 1.3,
    "Surat": 1.2,
    "Vadodara": 1.1,
    "Rajkot": 1.0,
    "Bhavnagar": 1.0,
    "Jamnagar": 0.9,
    "Gandhinagar": 1.1,
    "Kutch": 0.8,
    "Mehsana": 0.95,
    "Anand": 1.0,
    "Panchmahal": 1.4,  # historically sensitive
    "Navsari": 0.9,
    "Surendranagar": 0.85,
    "Valsad": 0.9,
    "Bharuch": 1.0,
}

# Call-to-action keywords (multi-lingual)
CTA_PATTERNS = [
    # Hindi/Hinglish
    r"\baa?j\b.{0,30}\b(baj[ae]?|raat|shaam|subah)\b",
    r"\bkal\b.{0,30}\b(baj[ae]?|raat|shaam|subah)\b",
    r"\bchalo\b",
    r"\bnikal[oo]?\b",
    r"\bjam[ao]\b",
    r"\bpathr[aā]v\b",
    r"\blathi\b",
    r"\bghero\b",
    r"\bghera[oo]?\b",
    # Gujarati transliteration
    r"\babhiyan\b",
    r"\bsabhā?\b",
    r"\bmahas[ab]ha\b",
    r"\bjuloos\b",
    r"\bjaloos\b",
    # Generic
    r"\bgather\b",
    r"\bprotest\b.{0,20}\b(tonight|today|now)\b",
    r"\b(come|join)\b.{0,30}\b(tonight|today|tomorrow)\b",
]

import re
_CTA_COMPILED = [re.compile(p, re.IGNORECASE) for p in CTA_PATTERNS]


def _has_cta(text: str) -> bool:
    for pattern in _CTA_COMPILED:
        if pattern.search(text):
            return True
    return False


class EscalationRiskIndex:
    """
    Computes and caches the per-district Escalation Risk Index.
    Call .update(posts) after each crawl cycle.
    """

    def __init__(self):
        # district -> ERI data
        self._index: Dict[str, Dict[str, Any]] = {}
        self._last_updated: Optional[str] = None

    def update(self, posts: List[Dict[str, Any]]):
        """Recompute the ERI from the current post list."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(hours=24)

        # Per-district accumulators
        dist_recent: Dict[str, List[Dict]] = defaultdict(list)   # last 1h
        dist_baseline: Dict[str, List[Dict]] = defaultdict(list)  # last 24h

        for post in posts:
            district = post.get("district")
            if not district:
                continue
            ts_str = post.get("crawled_at") or post.get("timestamp")
            try:
                ts = datetime.fromisoformat(str(ts_str).replace("Z", ""))
            except Exception:
                ts = now

            if ts >= hour_ago:
                dist_recent[district].append(post)
            elif ts >= day_ago:
                dist_baseline[district].append(post)

        all_districts = set(list(dist_recent.keys()) + list(dist_baseline.keys()))
        new_index: Dict[str, Dict[str, Any]] = {}

        for district in all_districts:
            recent = dist_recent.get(district, [])
            baseline = dist_baseline.get(district, [])
            sensitivity = DISTRICT_SENSITIVITY.get(district, 1.0)

            eri, components = self._compute_eri(recent, baseline, sensitivity)

            # Trend direction
            previous_eri = self._index.get(district, {}).get("eri", 0)
            if eri > previous_eri + 5:
                trend = "rising"
            elif eri < previous_eri - 5:
                trend = "falling"
            else:
                trend = "stable"

            new_index[district] = {
                "district": district,
                "eri": eri,
                "trend": trend,
                "previous_eri": previous_eri,
                "components": components,
                "recent_post_count": len(recent),
                "baseline_post_count": len(baseline),
                "updated_at": now.isoformat(),
            }

        self._index = new_index
        self._last_updated = now.isoformat()

    def _compute_eri(
        self,
        recent: List[Dict],
        baseline: List[Dict],
        sensitivity: float
    ) -> tuple:
        """
        Compute ERI (0–100) and breakdown dict.
        """
        def avg_threat(posts):
            if not posts:
                return 0.0
            return sum(float(p.get("threat_score", 0)) for p in posts) / len(posts)

        def bot_coord_ratio(posts):
            if not posts:
                return 0.0
            flagged = sum(
                1 for p in posts
                if float(p.get("bot_likelihood", 0)) > 0.5 or p.get("coordination_group")
            )
            return flagged / len(posts)

        def cta_ratio(posts):
            if not posts:
                return 0.0
            count = sum(1 for p in posts if _has_cta(p.get("content", "")))
            return count / len(posts)

        def platform_diversity(posts):
            platforms = {p.get("platform", "unknown") for p in posts}
            return min(len(platforms) / 3.0, 1.0)

        recent_count = len(recent)
        baseline_count = len(baseline)

        # 1. Volume score (normalized — 10 posts/hour in a district = suspicious)
        volume_score = min(recent_count / 10.0, 1.0)

        # 2. Growth rate score
        baseline_per_hour = baseline_count / 23.0 if baseline_count > 0 else 0.0
        growth_ratio = recent_count / max(baseline_per_hour, 0.5)
        growth_score = min((growth_ratio - 1.0) / 10.0, 1.0) if growth_ratio > 1 else 0.0

        # 3. Threat language score
        threat_score = avg_threat(recent)

        # 4. Bot/coordination share
        botcoord_score = bot_coord_ratio(recent)

        # 5. Cross-platform echo
        crossplat_score = platform_diversity(recent)

        # 6. CTA density
        cta_score = cta_ratio(recent)

        # Weighted composite (weights sum to 1.0)
        composite = (
            0.20 * volume_score +
            0.15 * growth_score +
            0.25 * threat_score +
            0.15 * botcoord_score +
            0.10 * crossplat_score +
            0.15 * cta_score
        )

        # Apply district sensitivity multiplier and scale to 0–100
        eri = round(min(composite * sensitivity * 100.0, 100.0), 1)

        components = {
            "volume": round(volume_score * 100, 1),
            "growth": round(growth_score * 100, 1),
            "threat_language": round(threat_score * 100, 1),
            "bot_coordination": round(botcoord_score * 100, 1),
            "cross_platform": round(crossplat_score * 100, 1),
            "call_to_action": round(cta_score * 100, 1),
            "sensitivity_multiplier": sensitivity,
        }

        return eri, components

    def get_index(self) -> List[Dict[str, Any]]:
        """Return current ERI for all districts, sorted by ERI descending."""
        result = sorted(self._index.values(), key=lambda x: x["eri"], reverse=True)
        return result

    def get_district_eri(self, district: str) -> Optional[Dict[str, Any]]:
        return self._index.get(district)


# Module-level singleton
risk_index = EscalationRiskIndex()
