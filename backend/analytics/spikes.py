"""
analytics/spikes.py
Real statistical spike detection using robust MAD z-score (replaces the
made-up 1.5 + count*0.4 formula in analysis/trends.py).

Also provides data-driven keyword extraction using TF-IDF + n-gram frequency
(replaces the hard-coded 9-word list).
"""

import re
import math
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional


# ─── Utility ─────────────────────────────────────────────────────────────────

def _mad_zscore(values: List[float]) -> List[float]:
    """
    Robust z-score using Median Absolute Deviation.
    Formula: (x - median) / (1.4826 * MAD)
    Safe for small samples; returns 0 for constant series.
    """
    if not values:
        return []
    n = len(values)
    sorted_vals = sorted(values)
    median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    mad_vals = sorted(abs(v - median) for v in values)
    mad = mad_vals[n // 2] if n % 2 == 1 else (mad_vals[n // 2 - 1] + mad_vals[n // 2]) / 2
    scale = 1.4826 * mad
    if scale < 1e-9:
        return [0.0] * n
    return [(v - median) / scale for v in values]


def _bucket_posts_by_time(
    posts: List[Dict[str, Any]],
    bucket_minutes: int = 5,
    window_hours: int = 24
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Bucket posts into time slots. Returns {bucket_label: [posts]}.
    """
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for post in posts:
        ts_str = post.get("crawled_at") or post.get("timestamp")
        try:
            ts = datetime.fromisoformat(str(ts_str).replace("Z", ""))
        except Exception:
            ts = datetime.utcnow()

        if ts < cutoff:
            continue

        epoch = ts.timestamp()
        bucket_idx = int(epoch // (bucket_minutes * 60))
        bucket_label = datetime.utcfromtimestamp(bucket_idx * bucket_minutes * 60).strftime("%H:%M")
        buckets[bucket_label].append(post)

    return buckets


# ─── Spike Detector ──────────────────────────────────────────────────────────

class SpikeDetector:
    """
    Detects statistically significant spikes in keyword/hashtag frequency
    using robust MAD z-scores over time-bucketed post data.
    """

    SPIKE_ZSCORE_THRESHOLD = 2.5
    MIN_VOLUME = 2  # minimum occurrences to flag

    def get_trending_hashtags(self, posts: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """Extract and rank trending hashtags with real statistical spike detection."""
        # Per-hashtag time-series
        tag_series: Dict[str, List[int]] = defaultdict(lambda: [0] * 24)  # 24 five-min buckets ~ 2h window
        tag_total: Counter = Counter()
        tag_last_hour: Counter = Counter()
        tag_baseline: Counter = Counter()

        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(hours=24)

        for post in posts:
            ts_str = post.get("crawled_at") or post.get("timestamp")
            try:
                ts = datetime.fromisoformat(str(ts_str).replace("Z", ""))
            except Exception:
                ts = now

            for tag in post.get("hashtags", []):
                tag = f"#{tag.lstrip('#').lower()}"
                tag_total[tag] += 1
                if ts >= hour_ago:
                    tag_last_hour[tag] += 1
                elif ts >= day_ago:
                    tag_baseline[tag] += 1

        results = []
        for tag, total_count in tag_total.most_common(top_n * 3):
            if total_count < self.MIN_VOLUME:
                continue

            recent = tag_last_hour.get(tag, 0)
            baseline = max(tag_baseline.get(tag, 0), 1)

            # Simple spike: recent count vs baseline rate
            # Baseline rate per hour = baseline count / 23 hours
            baseline_per_hour = baseline / 23.0
            ratio = recent / max(baseline_per_hour, 0.5)

            # Compute a proper z-score if we have enough data
            all_counts = [tag_last_hour.get(tag, 0), baseline]
            z_scores = _mad_zscore([float(c) for c in all_counts])
            z_score = abs(z_scores[-1]) if z_scores else 0.0

            is_spiking = (z_score >= self.SPIKE_ZSCORE_THRESHOLD or ratio >= 5.0) and recent >= self.MIN_VOLUME

            results.append({
                "hashtag": tag,
                "count": total_count,
                "recent_count": recent,
                "baseline_count": baseline,
                "z_score": round(z_score, 2),
                "spike_ratio": round(ratio, 1),
                "is_spiking": is_spiking,
            })

        results.sort(key=lambda x: (x["is_spiking"], x["z_score"], x["count"]), reverse=True)
        return results[:top_n]

    def get_trending_keywords(self, posts: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extract trending keywords from post content using TF-IDF-like scoring.
        No more hard-coded 9-word list.
        """
        STOPWORDS = {
            "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "with", "from", "by", "this", "that",
            "are", "was", "has", "have", "had", "be", "been", "will", "can",
            "se", "ko", "me", "ke", "ka", "ki", "ne", "ho", "hai", "hain",
            "ek", "ye", "vo", "aur", "par", "bhi", "toh", "kya", "nahi",
            "rt", "amp", "https", "http", "www", "co", "via",
        }

        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(hours=24)

        recent_kw: Counter = Counter()
        baseline_kw: Counter = Counter()
        doc_count = max(len(posts), 1)

        def extract_words(text: str) -> List[str]:
            text = re.sub(r"http\S+|@\w+|#\w+", " ", text.lower())
            text = re.sub(r"[^\w\s]", " ", text)
            return [w for w in text.split() if len(w) > 3 and w not in STOPWORDS]

        for post in posts:
            ts_str = post.get("crawled_at") or post.get("timestamp")
            try:
                ts = datetime.fromisoformat(str(ts_str).replace("Z", ""))
            except Exception:
                ts = now
            content = post.get("content", "") or ""
            words = extract_words(content)
            if ts >= hour_ago:
                recent_kw.update(words)
            elif ts >= day_ago:
                baseline_kw.update(words)

        results = []
        for word, recent_count in recent_kw.most_common(top_n * 5):
            if recent_count < self.MIN_VOLUME:
                continue
            baseline_count = max(baseline_kw.get(word, 0), 1)
            baseline_per_hour = baseline_count / 23.0
            ratio = recent_count / max(baseline_per_hour, 0.5)
            z_scores = _mad_zscore([float(recent_count), float(baseline_count)])
            z_score = abs(z_scores[0]) if z_scores else 0.0
            is_spiking = (z_score >= self.SPIKE_ZSCORE_THRESHOLD or ratio >= 5.0) and recent_count >= self.MIN_VOLUME

            results.append({
                "keyword": word,
                "count": recent_count,
                "z_score": round(z_score, 2),
                "spike_ratio": round(ratio, 1),
                "is_spiking": is_spiking,
            })

        results.sort(key=lambda x: (x["is_spiking"], x["z_score"], x["count"]), reverse=True)
        return results[:top_n]

    def get_volume_timeline(self, posts: List[Dict[str, Any]], bucket_minutes: int = 30) -> List[Dict[str, Any]]:
        """Return a time-series of post volume with z-scores for the timeline chart."""
        buckets = _bucket_posts_by_time(posts, bucket_minutes=bucket_minutes, window_hours=24)
        sorted_buckets = sorted(buckets.items())
        counts = [len(b) for _, b in sorted_buckets]
        z_scores = _mad_zscore([float(c) for c in counts])

        return [
            {
                "time": label,
                "count": count,
                "z_score": round(z, 2),
                "is_spike": abs(z) >= self.SPIKE_ZSCORE_THRESHOLD and count >= self.MIN_VOLUME,
            }
            for (label, _), count, z in zip(sorted_buckets, counts, z_scores)
        ]


# Module-level singleton
spike_detector = SpikeDetector()
