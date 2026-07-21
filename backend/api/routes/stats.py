from fastapi import APIRouter
from storage.db_client import db

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/overview")
def get_overview_stats():
    posts = db.get_posts(limit=500)["items"]
    alerts = db.get_alerts()
    
    total_posts = len(posts)
    critical_threats = sum(1 for p in posts if p.get("threat_score", 0) >= 0.70)
    incitement_count = sum(1 for p in posts if p.get("threat_level") == "Incitement to Violence")
    fake_news_count = sum(1 for p in posts if p.get("threat_level") == "Fake News")
    inflammatory_count = sum(1 for p in posts if p.get("threat_level") == "Inflammatory")
    neutral_count = sum(1 for p in posts if p.get("threat_level") == "Neutral")
    
    bot_posts = sum(1 for p in posts if p.get("is_bot"))
    
    platform_dist = {
        "x": sum(1 for p in posts if p.get("platform") == "x"),
        "instagram": sum(1 for p in posts if p.get("platform") == "instagram"),
        "facebook": sum(1 for p in posts if p.get("platform") == "facebook"),
        "youtube": sum(1 for p in posts if p.get("platform") == "youtube")
    }
    
    lang_dist = {
        "gu": sum(1 for p in posts if p.get("language") == "gu"),
        "hi": sum(1 for p in posts if p.get("language") == "hi"),
        "hinglish": sum(1 for p in posts if p.get("language") == "hinglish"),
        "en": sum(1 for p in posts if p.get("language") == "en")
    }
    
    # Calculate overall threat index score (0.0 - 100.0)
    avg_threat_score = (sum(p.get("threat_score", 0) for p in posts) / max(total_posts, 1)) * 100
    
    return {
        "total_monitored_posts": total_posts,
        "critical_threats": critical_threats,
        "active_alerts": len([a for a in alerts if a.get("status") == "open"]),
        "threat_index_score": round(avg_threat_score, 1),
        "threat_distribution": {
            "Incitement to Violence": incitement_count,
            "Fake News": fake_news_count,
            "Inflammatory": inflammatory_count,
            "Neutral": neutral_count
        },
        "bot_amplification_count": bot_posts,
        "platform_distribution": platform_dist,
        "language_distribution": lang_dist
    }
