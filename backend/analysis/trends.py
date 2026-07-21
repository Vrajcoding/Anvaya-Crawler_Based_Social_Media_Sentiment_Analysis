from collections import Counter
from typing import List, Dict, Any
import numpy as np
from storage.db_client import db

class TrendAnalyzer:
    """Spike and trend detector for regional keywords and hashtags."""
    
    @staticmethod
    def get_trending_hashtags(top_n: int = 10) -> List[Dict[str, Any]]:
        posts = db.get_posts(limit=200)["items"]
        hashtag_counts = Counter()
        
        for post in posts:
            for tag in post.get("hashtags", []):
                hashtag_counts[f"#{tag.lstrip('#')}"] += 1
                
        results = []
        for tag, count in hashtag_counts.most_common(top_n):
            # Calculate mock velocity & spike indicator
            z_score = round(1.5 + (count * 0.4), 2)
            results.append({
                "hashtag": tag,
                "count": count,
                "z_score": z_score,
                "is_spiking": z_score > 2.5
            })
            
        return results

    @staticmethod
    def get_trending_keywords(top_n: int = 10) -> List[Dict[str, Any]]:
        posts = db.get_posts(limit=200)["items"]
        keywords = ["પથ્થરમારો", "દંગા", "જહર", "ચોક બજાર", "पानी", "अफ़वाह", "police", "attack", "riots"]
        
        results = []
        for kw in keywords:
            count = sum(1 for p in posts if kw.lower() in p.get("content", "").lower())
            if count > 0:
                z_score = round(1.2 + (count * 0.5), 2)
                results.append({
                    "keyword": kw,
                    "count": count,
                    "z_score": z_score,
                    "is_spiking": z_score > 2.5
                })
        results.sort(key=lambda x: x["count"], reverse=True)
        return results[:top_n]
