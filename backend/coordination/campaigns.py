"""
coordination/campaigns.py
Aggregates duplicate clusters + sync events into Campaign objects.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from coordination.duplicates import duplicate_detector
from coordination.sync import sync_detector


class CampaignTracker:
    """
    A Campaign is a group of coordinated posts sharing a narrative,
    posted by multiple accounts in a suspicious synchronized manner.
    """

    def __init__(self):
        # campaign_id -> Campaign dict
        self._campaigns: Dict[str, Dict[str, Any]] = {}

    def update_from_post(self, post: Dict[str, Any]):
        """Update campaign tracker after a post has been through dup + sync detection."""
        cluster_id = post.get("duplicate_cluster_id")
        coord_group = post.get("coordination_group")

        if not cluster_id:
            return

        campaign_id = coord_group or cluster_id

        if campaign_id not in self._campaigns:
            self._campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "narrative_summary": post.get("content", "")[:200],
                "accounts": set(),
                "post_ids": [],
                "platforms": set(),
                "first_seen": post.get("crawled_at", datetime.utcnow().isoformat()),
                "last_seen": post.get("crawled_at", datetime.utcnow().isoformat()),
                "growth_rate": 0.0,
                "confidence": 0.0,
            }

        campaign = self._campaigns[campaign_id]
        author = post.get("author_username", "unknown")
        campaign["accounts"].add(author)
        campaign["post_ids"].append(str(post.get("id", "")))
        campaign["platforms"].add(post.get("platform", "unknown"))
        campaign["last_seen"] = post.get("crawled_at", datetime.utcnow().isoformat())

        # Compute confidence based on cluster size and sync score
        cluster_size = post.get("duplicate_cluster_size", 1)
        sync_score = post.get("sync_score", 0.0)
        unique_accounts = len(campaign["accounts"])
        confidence = min(
            0.3 * min(cluster_size / 10.0, 1.0) +
            0.4 * sync_score +
            0.3 * min(unique_accounts / 5.0, 1.0),
            1.0
        )
        campaign["confidence"] = round(confidence, 3)

        # Growth rate: posts per hour
        try:
            first = datetime.fromisoformat(campaign["first_seen"].replace("Z", ""))
            last = datetime.fromisoformat(campaign["last_seen"].replace("Z", ""))
            hours = max((last - first).total_seconds() / 3600.0, 0.01)
            campaign["growth_rate"] = round(len(campaign["post_ids"]) / hours, 2)
        except Exception:
            campaign["growth_rate"] = 0.0

    def get_all_campaigns(self) -> List[Dict[str, Any]]:
        """Return serialisable list of all campaigns."""
        result = []
        for cid, c in self._campaigns.items():
            if len(c["accounts"]) >= 2:
                result.append({
                    "campaign_id": cid,
                    "narrative_summary": c["narrative_summary"],
                    "accounts": list(c["accounts"]),
                    "post_ids": c["post_ids"][-50:],  # cap for API response
                    "platforms": list(c["platforms"]),
                    "first_seen": c["first_seen"],
                    "last_seen": c["last_seen"],
                    "growth_rate": c["growth_rate"],
                    "confidence": c["confidence"],
                    "unique_accounts": len(c["accounts"]),
                    "total_posts": len(c["post_ids"]),
                })
        result.sort(key=lambda x: x["confidence"], reverse=True)
        return result


# Module-level singleton
campaign_tracker = CampaignTracker()
