"""
ingest/geo_tagger.py
Extracts district/city location from post content and profile metadata
using the Gujarat gazetteer, text matching, and NER-like patterns.
"""

import json
import os
import re
from typing import Dict, Any, Optional, Tuple, List

# Load gazetteer once at import time
_GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), "gazetteer_gu.json")

def _load_gazetteer():
    with open(_GAZETTEER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_GAZETTEER = _load_gazetteer()

# Pre-build a flat lookup: term (lower) -> district
_TERM_TO_DISTRICT: Dict[str, Dict[str, Any]] = {}
for _dist in _GAZETTEER["districts"]:
    for _term in [
        _dist["name"],
        _dist["name_gu"],
        _dist["name_hi"],
        *_dist.get("aliases", []),
        *_dist.get("cities", []),
    ]:
        if _term:
            _TERM_TO_DISTRICT[_term.lower()] = _dist


class GeoTagger:
    """
    Tags posts with district/city location from Gujarat.
    Priority order:
    1. Platform-provided geotag
    2. Author's profile location string
    3. Named-entity gazetteer match in post content
    4. Fallback: unknown
    """

    def tag_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich post with geo fields:
        - district: str
        - city: str
        - lat: float
        - lon: float
        - geo_confidence: float (0.0 = unknown, 1.0 = certain)
        - geo_source: str ('geotag' | 'profile' | 'content' | 'unknown')
        """
        # 1. Platform geotag (highest confidence)
        geotag = post.get("geotag") or post.get("place") or post.get("location_data")
        if geotag and isinstance(geotag, dict):
            loc = self._match_location(str(geotag.get("full_name", "") or geotag.get("name", "")))
            if loc:
                return self._apply_geo(post, loc, source="geotag", confidence=0.95)

        # 2. Profile location string
        profile_loc = (
            post.get("author_location") or
            post.get("user_location") or
            post.get("author_bio", "")
        )
        if profile_loc:
            loc = self._match_location(str(profile_loc))
            if loc:
                return self._apply_geo(post, loc, source="profile", confidence=0.75)

        # 3. Content text gazetteer scan
        content = post.get("content", "") or post.get("text", "")
        if content:
            loc = self._match_location(content)
            if loc:
                return self._apply_geo(post, loc, source="content", confidence=0.55)

        # 4. Unknown
        post.setdefault("district", None)
        post.setdefault("city", None)
        post.setdefault("lat", None)
        post.setdefault("lon", None)
        post.setdefault("geo_confidence", 0.0)
        post.setdefault("geo_source", "unknown")
        return post

    def _match_location(self, text: str) -> Optional[Dict[str, Any]]:
        """Find the best matching district from text."""
        text_lower = text.lower()

        # Longest match wins (avoids "Surat" matching inside "Surendranagar")
        best_match = None
        best_len = 0

        for term, district in _TERM_TO_DISTRICT.items():
            # Use word-boundary matching
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, text_lower):
                if len(term) > best_len:
                    best_match = district
                    best_len = len(term)

        return best_match

    def _apply_geo(
        self,
        post: Dict[str, Any],
        district: Dict[str, Any],
        source: str,
        confidence: float
    ) -> Dict[str, Any]:
        post["district"] = district["name"]
        post["city"] = district.get("cities", [None])[0]
        post["lat"] = district.get("lat")
        post["lon"] = district.get("lon")
        post["geo_confidence"] = confidence
        post["geo_source"] = source
        return post

    def get_district_stats(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregate posts by district for map heat-map rendering.
        Returns list of {district, lat, lon, count, avg_threat, critical_count}.
        """
        stats: Dict[str, Dict[str, Any]] = {}

        for post in posts:
            dist = post.get("district")
            if not dist:
                continue
            if dist not in stats:
                stats[dist] = {
                    "district": dist,
                    "lat": post.get("lat"),
                    "lon": post.get("lon"),
                    "count": 0,
                    "total_threat": 0.0,
                    "critical_count": 0,
                    "high_count": 0,
                }
            entry = stats[dist]
            entry["count"] += 1
            ts = float(post.get("threat_score", 0.0))
            entry["total_threat"] += ts
            if ts >= 0.85:
                entry["critical_count"] += 1
            elif ts >= 0.70:
                entry["high_count"] += 1

        result = []
        for dist, s in stats.items():
            result.append({
                "district": s["district"],
                "lat": s["lat"],
                "lon": s["lon"],
                "count": s["count"],
                "avg_threat": round(s["total_threat"] / max(s["count"], 1), 3),
                "critical_count": s["critical_count"],
                "high_count": s["high_count"],
            })

        result.sort(key=lambda x: x["avg_threat"], reverse=True)
        return result


# Module-level singleton
geo_tagger = GeoTagger()
