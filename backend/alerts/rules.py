"""
alerts/rules.py
Auto-generates alerts when post composite threat score crosses thresholds.
Replaces the missing `db.add_alert()` caller gap.
De-duplicates: same campaign within 15 minutes → update, don't re-alert.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from storage.db_client import db
from utils.config import settings


# Alert de-duplicate window in minutes
DEDUP_WINDOW_MINUTES = 15


def _recent_campaign_alert(campaign_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Check if we already sent an alert for this campaign in the last DEDUP_WINDOW_MINUTES."""
    if not campaign_id:
        return None
    cutoff = datetime.utcnow() - timedelta(minutes=DEDUP_WINDOW_MINUTES)
    for alert in db.get_alerts():
        if alert.get("campaign_id") == campaign_id:
            try:
                created = datetime.fromisoformat(alert["created_at"].replace("Z", ""))
                if created >= cutoff:
                    return alert
            except Exception:
                pass
    return None


def build_reason_codes(post: Dict[str, Any]) -> List[str]:
    """Build a list of human-readable reason codes for why this post was flagged."""
    reasons = []
    threat_level = post.get("threat_level", "Neutral")
    if threat_level in ("Incitement", "Inflammatory"):
        reasons.append(f"threat:{threat_level}")
    if post.get("is_hate_speech"):
        reasons.append("hate_speech")
    if post.get("coordination_group"):
        reasons.append(f"coordinated:{post['coordination_group'][:12]}")
    if float(post.get("bot_likelihood", 0)) > 0.5:
        reasons.append("bot_suspected")
    if post.get("is_near_duplicate"):
        reasons.append(f"near_duplicate_cluster:{post.get('duplicate_cluster_id', '')[:8]}")
    score = float(post.get("threat_score", 0))
    if score >= settings.THRESHOLD_CRITICAL:
        reasons.append("score:CRITICAL")
    elif score >= settings.THRESHOLD_HIGH:
        reasons.append("score:HIGH")
    return reasons


def maybe_create_alert(post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Evaluate a post and create an alert if it crosses thresholds.
    Returns the created alert dict, or None if not triggered.
    """
    score = float(post.get("threat_score", 0.0))

    # Only alert on HIGH or CRITICAL posts
    if score < settings.THRESHOLD_HIGH:
        return None

    campaign_id = post.get("coordination_group") or post.get("duplicate_cluster_id")

    # De-duplicate
    existing = _recent_campaign_alert(campaign_id)
    if existing:
        # Update severity if this post is worse
        if score > float(existing.get("threat_score", 0)):
            existing["threat_score"] = score
            existing["updated_at"] = datetime.utcnow().isoformat()
        return None  # Don't re-create

    # Severity label
    if score >= settings.THRESHOLD_CRITICAL:
        severity = "CRITICAL"
    else:
        severity = "HIGH"

    reason_codes = build_reason_codes(post)
    sla_minutes = 15 if severity == "CRITICAL" else 60
    sla_due = (datetime.utcnow() + timedelta(minutes=sla_minutes)).isoformat()

    alert = {
        "id": str(uuid.uuid4()),
        "post_id": str(post.get("id", "")),
        "campaign_id": campaign_id,
        "title": f"{severity} Threat Detected — {post.get('platform', 'unknown').upper()}",
        "description": (post.get("content", "")[:300] + "…") if len(post.get("content", "")) > 300 else post.get("content", ""),
        "severity": severity,
        "threat_score": score,
        "reason_codes": reason_codes,
        "platform": post.get("platform", "unknown"),
        "author": post.get("author_username", "unknown"),
        "district": post.get("district"),
        "language": post.get("language", "unknown"),
        "geo_confidence": post.get("geo_confidence", 0.0),
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
        "sla_due": sla_due,
        "post_url": post.get("url", ""),
    }

    created = db.add_alert(alert)
    return created


async def maybe_dispatch_alert(alert: Dict[str, Any]):
    """
    Attempt to dispatch the alert via available channels.
    Fails silently so it doesn't block the main crawler loop.
    """
    try:
        from alerts.dispatch_telegram import send_telegram_alert
        await send_telegram_alert(alert)
    except Exception as e:
        print(f"[alerts/rules] Telegram dispatch skipped: {e}")
