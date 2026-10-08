"""
coordination/account_signals.py
Computes a bot likelihood score for accounts based on observable heuristics.
Replaces the random.random() bot flag with real computed signals.
"""

import re
import math
from datetime import datetime
from typing import Dict, Any, Optional


class AccountSignalAnalyzer:
    """
    Computes bot likelihood [0.0 – 1.0] from crawled account metadata.
    Each signal contributes a partial score; they are combined with weights.
    """

    # Signal weights (must sum to 1.0)
    WEIGHTS = {
        "username_entropy": 0.15,    # random-looking usernames
        "default_avatar": 0.12,      # no profile picture
        "account_age": 0.18,         # very new accounts
        "follower_ratio": 0.20,      # follows many, followed by few
        "post_frequency": 0.15,      # posts per day suspiciously high
        "reply_only": 0.10,          # only replies, never original
        "name_digit_ratio": 0.10,    # lots of digits in name
    }

    def compute_bot_likelihood(self, post: Dict[str, Any]) -> float:
        """
        Compute bot likelihood score [0.0-1.0] for the author of a post.
        Returns 0.0 when insufficient metadata is available (safe default).
        """
        scores: Dict[str, float] = {}

        # 1. Username character entropy (random strings score high)
        username = post.get("author_username", "") or ""
        scores["username_entropy"] = self._username_entropy_score(username)

        # 2. Default / no avatar
        avatar = post.get("author_avatar") or post.get("profile_image_url")
        scores["default_avatar"] = 1.0 if (avatar is None or "default" in str(avatar).lower()) else 0.0

        # 3. Account age (days since created_at)
        account_age_days = self._account_age_days(post)
        if account_age_days is None:
            scores["account_age"] = 0.2  # unknown — give mild suspicion
        elif account_age_days < 7:
            scores["account_age"] = 1.0
        elif account_age_days < 30:
            scores["account_age"] = 0.7
        elif account_age_days < 90:
            scores["account_age"] = 0.3
        else:
            scores["account_age"] = 0.0

        # 4. Follower / following ratio
        followers = post.get("author_followers") or post.get("followers_count") or 0
        following = post.get("author_following") or post.get("following_count") or 0
        scores["follower_ratio"] = self._follower_ratio_score(followers, following)

        # 5. Post frequency (posts per day — if metadata available)
        posts_total = post.get("author_posts_count") or post.get("statuses_count")
        if posts_total and account_age_days and account_age_days > 0:
            posts_per_day = posts_total / account_age_days
            # >50 posts/day is very suspicious
            scores["post_frequency"] = min(posts_per_day / 50.0, 1.0)
        else:
            scores["post_frequency"] = 0.1  # neutral default

        # 6. Reply-only behaviour (no original posts, only replies)
        is_reply = post.get("is_reply", False) or bool(post.get("reply_to"))
        has_original = post.get("author_has_original_posts", True)
        scores["reply_only"] = 0.8 if (is_reply and not has_original) else 0.0

        # 7. Name digit ratio (e.g., "user398471892")
        scores["name_digit_ratio"] = self._digit_ratio_score(username)

        # Weighted composite
        composite = sum(
            self.WEIGHTS[key] * scores.get(key, 0.0)
            for key in self.WEIGHTS
        )
        return round(min(max(composite, 0.0), 1.0), 3)

    def _username_entropy_score(self, username: str) -> float:
        """Higher entropy => more likely auto-generated."""
        clean = re.sub(r"[@_\-\.]", "", username.lower())
        if len(clean) < 4:
            return 0.1
        # Shannon entropy
        freq = {}
        for ch in clean:
            freq[ch] = freq.get(ch, 0) + 1
        entropy = -sum((c / len(clean)) * math.log2(c / len(clean)) for c in freq.values())
        # Typical human usernames have entropy < 3.5; random strings often > 4.0
        return min(max((entropy - 3.0) / 2.0, 0.0), 1.0)

    def _digit_ratio_score(self, username: str) -> float:
        if not username:
            return 0.0
        digits = sum(1 for c in username if c.isdigit())
        ratio = digits / max(len(username), 1)
        return min(ratio * 2.0, 1.0)

    def _account_age_days(self, post: Dict[str, Any]) -> Optional[float]:
        created = post.get("author_created_at") or post.get("account_created_at")
        if not created:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%a %b %d %H:%M:%S +0000 %Y"):
            try:
                dt = datetime.strptime(str(created)[:19], fmt[:len(fmt)])
                return max((datetime.utcnow() - dt).days, 0)
            except Exception:
                pass
        return None

    def _follower_ratio_score(self, followers: int, following: int) -> float:
        if following == 0:
            return 0.0
        ratio = followers / following  # < 0.1 means follows many but nobody follows back
        if ratio < 0.05:
            return 1.0
        elif ratio < 0.2:
            return 0.7
        elif ratio < 0.5:
            return 0.3
        else:
            return 0.0


# Module-level singleton
account_analyzer = AccountSignalAnalyzer()
