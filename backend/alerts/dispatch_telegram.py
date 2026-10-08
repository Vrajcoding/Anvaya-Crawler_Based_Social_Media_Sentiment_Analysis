"""
alerts/dispatch_telegram.py
Sends alert notifications via Telegram Bot API (not MTProto — simpler & safer).
Uses TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from environment.
"""

import os
import asyncio
from typing import Dict, Any, Optional

import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _format_alert_message(alert: Dict[str, Any]) -> str:
    """Format alert as a Telegram message (Markdown V2 safe)."""
    severity = alert.get("severity", "HIGH")
    emoji = "🚨" if severity == "CRITICAL" else "⚠️"
    platform = alert.get("platform", "unknown").upper()
    district = alert.get("district") or "Unknown district"
    score = alert.get("threat_score", 0.0)
    author = alert.get("author", "unknown")
    description = alert.get("description", "")[:200]
    reasons = ", ".join(alert.get("reason_codes", []))
    sla = alert.get("sla_due", "")[:16]

    msg = (
        f"{emoji} *SENTINEL AI ALERT — {severity}*\n\n"
        f"📍 District: {district}\n"
        f"🌐 Platform: {platform}\n"
        f"👤 Author: @{author}\n"
        f"📊 Threat Score: {score:.2f}\n"
        f"🔖 Reasons: {reasons}\n"
        f"⏰ SLA Due: {sla}\n\n"
        f"📝 Content:\n_{description}_\n\n"
        f"Alert ID: `{alert.get('id', '')[:8]}`"
    )
    return msg


async def send_telegram_alert(alert: Dict[str, Any]) -> bool:
    """
    Send an alert to the configured Telegram chat.
    Returns True on success, False on failure/not configured.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[dispatch_telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping.")
        return False

    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)
    message = _format_alert_message(alert)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            })
            if response.status_code == 200:
                print(f"[dispatch_telegram] Alert sent for {alert.get('id', '')[:8]}")
                return True
            else:
                print(f"[dispatch_telegram] Failed: {response.status_code} {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[dispatch_telegram] Exception: {e}")
        return False
