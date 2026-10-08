"""
coordination/sync.py
Detects synchronized posting behaviour: multiple accounts posting similar
content within a short time window (coordination signal).
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class SyncDetector:
    """
    Detects when multiple accounts post near-identical content within a
    configurable time window — a strong signal of coordinated inauthentic
    behaviour.

    Algorithm:
    1. Posts are bucketed into Δt-second windows.
    2. Within each bucket, pairs of posts with the same cluster_id are counted.
    3. Authors with ≥ MIN_ACCOUNTS_IN_WINDOW co-posting events get a high sync score.
    """

    # Time window in seconds for synchronization detection
    TIME_WINDOW_SECONDS = 120  # 2 minutes
    MIN_POSTS_FOR_FLAG = 3

    def __init__(self):
        # bucket_key -> list of (post_id, author, cluster_id, ts)
        self._buckets: Dict[str, List[tuple]] = defaultdict(list)
        # author -> sync_score
        self._author_scores: Dict[str, float] = {}
        # coordination_group per post
        self._post_groups: Dict[str, Optional[str]] = {}

    def _bucket_key(self, ts: datetime) -> str:
        """Round timestamp to TIME_WINDOW_SECONDS bucket."""
        epoch = ts.timestamp()
        bucket = int(epoch // self.TIME_WINDOW_SECONDS)
        return str(bucket)

    def _parse_ts(self, ts_str: Optional[str]) -> datetime:
        if not ts_str:
            return datetime.utcnow()
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(ts_str[:19], fmt[:len(fmt)])
            except Exception:
                pass
        return datetime.utcnow()

    def process_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single post and compute its sync/coordination score.
        Returns enriched post with:
        - sync_score: float [0.0-1.0]
        - coordination_group: str or None  (real, not random)
        """
        post_id = str(post.get("id") or post.get("post_id", ""))
        author = str(post.get("author_username", "unknown"))
        cluster_id = post.get("duplicate_cluster_id")  # set by DuplicateDetector
        ts = self._parse_ts(post.get("crawled_at") or post.get("timestamp"))

        bucket_key = self._bucket_key(ts)
        prev_bucket_key = str(int(bucket_key) - 1)

        # Store entry
        self._buckets[bucket_key].append((post_id, author, cluster_id, ts))

        # Look across current and previous bucket for co-posting
        combined_entries = self._buckets.get(bucket_key, []) + self._buckets.get(prev_bucket_key, [])

        # Only consider entries with a known cluster_id
        if cluster_id:
            matching = [e for e in combined_entries if e[2] == cluster_id and e[1] != author]
            unique_authors_in_cluster = len({e[1] for e in matching})
        else:
            unique_authors_in_cluster = 0

        # Sync score: how many different authors posted the same cluster in this window
        sync_score = min(unique_authors_in_cluster / 10.0, 1.0)

        # Coordination group: if ≥ MIN_POSTS_FOR_FLAG unique authors, it's a campaign
        if cluster_id and unique_authors_in_cluster >= self.MIN_POSTS_FOR_FLAG:
            coord_group = cluster_id  # reuse cluster as coordination group ID
        else:
            coord_group = None

        post["sync_score"] = round(sync_score, 3)
        post["coordination_group"] = coord_group  # REAL value, no random()

        # Update author score
        self._author_scores[author] = max(self._author_scores.get(author, 0.0), sync_score)
        self._post_groups[post_id] = coord_group

        # Prune old buckets (keep last 10 windows)
        current_bucket = int(bucket_key)
        to_delete = [k for k in self._buckets if int(k) < current_bucket - 10]
        for k in to_delete:
            del self._buckets[k]

        return post

    def get_author_sync_score(self, author: str) -> float:
        return self._author_scores.get(author, 0.0)

    def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """Return all active coordination groups across current windows."""
        # Aggregate by coordination group across all buckets
        groups: Dict[str, set] = defaultdict(set)
        all_entries = [e for entries in self._buckets.values() for e in entries]
        for pid, author, cluster_id, ts in all_entries:
            cg = self._post_groups.get(pid)
            if cg:
                groups[cg].add(author)
        result = []
        for group_id, authors in groups.items():
            if len(authors) >= self.MIN_POSTS_FOR_FLAG:
                result.append({
                    "coordination_group": group_id,
                    "unique_authors": len(authors),
                    "accounts": list(authors),
                })
        result.sort(key=lambda x: x["unique_authors"], reverse=True)
        return result


# Module-level singleton
sync_detector = SyncDetector()
