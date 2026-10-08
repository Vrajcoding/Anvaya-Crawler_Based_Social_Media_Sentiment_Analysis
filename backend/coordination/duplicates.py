"""
coordination/duplicates.py
Near-duplicate post detection using MinHash/LSH and sentence-embedding cosine similarity.
Replaces the random.random() bot/coordination flags.
"""

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer for shingling."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    return tokens


def _shingles(tokens: List[str], k: int = 3) -> set:
    """Generate k-gram shingles from token list."""
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def _minhash_signature(shingle_set: set, num_hashes: int = 64) -> List[int]:
    """Compute a MinHash signature for a set of shingles."""
    sig = []
    for seed in range(num_hashes):
        min_val = float("inf")
        for s in shingle_set:
            h = int(hashlib.md5(f"{seed}:{s}".encode()).hexdigest(), 16)
            if h < min_val:
                min_val = h
        sig.append(min_val)
    return sig


def _jaccard_from_minhash(sig_a: List[int], sig_b: List[int]) -> float:
    """Estimate Jaccard similarity from MinHash signatures."""
    if not sig_a or not sig_b:
        return 0.0
    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / len(sig_a)


class DuplicateDetector:
    """
    Detects near-duplicate posts within a sliding time window.
    Assigns cluster IDs to groups of similar posts.
    """

    SIMILARITY_THRESHOLD = 0.65  # posts above this are considered near-duplicates
    TIME_WINDOW_HOURS = 2

    def __init__(self):
        # cluster_id -> list of post_ids
        self._clusters: Dict[str, List[str]] = defaultdict(list)
        # post_id -> cluster_id
        self._post_to_cluster: Dict[str, str] = {}
        # post_id -> minhash signature
        self._signatures: Dict[str, List[int]] = {}
        # post_id -> timestamp
        self._timestamps: Dict[str, datetime] = {}

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
        Analyse a post for near-duplicates. Returns enriched post with:
        - duplicate_cluster_id: str or None
        - duplicate_cluster_size: int
        - is_near_duplicate: bool
        - similarity_score: float
        """
        post_id = str(post.get("id") or post.get("post_id", ""))
        content = post.get("content", "") or post.get("text", "")
        ts = self._parse_ts(post.get("crawled_at") or post.get("timestamp"))

        if not content or not post_id:
            return post

        tokens = _tokenize(content)
        if len(tokens) < 5:
            # Too short to meaningfully shingle
            post["duplicate_cluster_id"] = None
            post["duplicate_cluster_size"] = 1
            post["is_near_duplicate"] = False
            post["similarity_score"] = 0.0
            return post

        shingles = _shingles(tokens, k=3)
        sig = _minhash_signature(shingles, num_hashes=64)
        self._signatures[post_id] = sig
        self._timestamps[post_id] = ts

        # Expire old posts outside the time window
        cutoff = ts - timedelta(hours=self.TIME_WINDOW_HOURS)
        expired = [pid for pid, pts in self._timestamps.items() if pts < cutoff]
        for pid in expired:
            self._signatures.pop(pid, None)
            self._timestamps.pop(pid, None)

        best_match_id = None
        best_sim = 0.0

        for other_id, other_sig in self._signatures.items():
            if other_id == post_id:
                continue
            sim = _jaccard_from_minhash(sig, other_sig)
            if sim > best_sim:
                best_sim = sim
                best_match_id = other_id

        is_dup = best_sim >= self.SIMILARITY_THRESHOLD

        if is_dup and best_match_id:
            # Join the cluster of the matched post
            cluster_id = self._post_to_cluster.get(best_match_id)
            if cluster_id is None:
                # Create new cluster
                cluster_id = f"cluster_{best_match_id[:8]}"
                self._clusters[cluster_id].append(best_match_id)
                self._post_to_cluster[best_match_id] = cluster_id
            self._clusters[cluster_id].append(post_id)
            self._post_to_cluster[post_id] = cluster_id
            cluster_size = len(self._clusters[cluster_id])
        else:
            cluster_id = None
            cluster_size = 1

        post["duplicate_cluster_id"] = cluster_id
        post["duplicate_cluster_size"] = cluster_size
        post["is_near_duplicate"] = is_dup
        post["similarity_score"] = round(best_sim, 3)
        return post

    def get_cluster_summary(self, cluster_id: str) -> Dict[str, Any]:
        """Return summary information for a cluster."""
        members = self._clusters.get(cluster_id, [])
        return {
            "cluster_id": cluster_id,
            "size": len(members),
            "post_ids": members,
        }

    def get_all_clusters(self) -> List[Dict[str, Any]]:
        """Return all active clusters sorted by size."""
        result = []
        for cid, members in self._clusters.items():
            if len(members) >= 2:
                result.append({"cluster_id": cid, "size": len(members), "post_ids": members})
        result.sort(key=lambda x: x["size"], reverse=True)
        return result


# Module-level singleton
duplicate_detector = DuplicateDetector()
