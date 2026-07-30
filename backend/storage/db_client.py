import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DATA_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crawled_posts_store.json")

class InMemoryDatabase:
    """High-performance thread-safe storage engine for SentinelAI CTI Platform with JSON disk persistence."""
    
    def __init__(self):
        self.posts: Dict[str, Dict[str, Any]] = {}
        self.watchlist: Dict[str, Dict[str, Any]] = {}
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.feedback: Dict[str, Dict[str, Any]] = {}
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self.logs: List[Dict[str, Any]] = []
        self._load_from_disk()
        
    def _load_from_disk(self):
        try:
            if os.path.exists(DATA_STORE_PATH):
                with open(DATA_STORE_PATH, "r", encoding="utf-8") as f:
                    stored_posts = json.load(f)
                    for post in stored_posts:
                        p_id = str(post.get("id") or post.get("post_id") or uuid.uuid4())
                        self.posts[p_id] = post
        except Exception as e:
            print(f"[db_client] Load from disk warning: {e}")

    def _persist_to_disk(self):
        try:
            os.makedirs(os.path.dirname(DATA_STORE_PATH), exist_ok=True)
            with open(DATA_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(list(self.posts.values()), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[db_client] Persist to disk error: {e}")

    def add_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        post_id = str(post.get("id") or post.get("post_id") or uuid.uuid4())
        post["id"] = post_id
        if "crawled_at" not in post:
            post["crawled_at"] = datetime.utcnow().isoformat()
        self.posts[post_id] = post
        self._persist_to_disk()
        return post

    def save_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        return self.add_post(post)

    def get_posts(
        self,
        platform: Optional[str] = None,
        threat_level: Optional[str] = None,
        language: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        results = list(self.posts.values())
        
        if platform and platform != "all":
            results = [p for p in results if p.get("platform", "").lower() == platform.lower()]
            
        if threat_level and threat_level != "all":
            results = [p for p in results if p.get("threat_level", "").lower() == threat_level.lower()]
            
        if language and language != "all":
            results = [p for p in results if p.get("language", "").lower() == language.lower()]
            
        if query:
            q = query.lower()
            results = [
                p for p in results 
                if q in p.get("content", "").lower() 
                or q in p.get("author_username", "").lower()
                or any(q in h.lower() for h in p.get("hashtags", []))
            ]
            
        # Sort by crawled_at desc
        results.sort(key=lambda x: x.get("crawled_at", ""), reverse=True)
        
        total = len(results)
        paginated = results[offset: offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": paginated
        }

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self.posts.get(post_id)

    # Watchlist operations
    def get_watchlist(self) -> List[Dict[str, Any]]:
        return list(self.watchlist.values())

    def add_watchlist_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        item_id = item.get("id") or str(uuid.uuid4())
        item["id"] = item_id
        item["created_at"] = datetime.utcnow().isoformat()
        item["active"] = item.get("active", True)
        self.watchlist[item_id] = item
        return item

    def delete_watchlist_item(self, item_id: str) -> bool:
        if item_id in self.watchlist:
            del self.watchlist[item_id]
            return True
        return False

    # Alert operations
    def add_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        alert_id = alert.get("id") or str(uuid.uuid4())
        alert["id"] = alert_id
        alert["created_at"] = alert.get("created_at") or datetime.utcnow().isoformat()
        alert["status"] = alert.get("status", "open")
        self.alerts[alert_id] = alert
        return alert

    def get_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        alerts_list = list(self.alerts.values())
        if status and status != "all":
            alerts_list = [a for a in alerts_list if a.get("status") == status]
        alerts_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return alerts_list

    def update_alert_status(self, alert_id: str, status: str) -> Optional[Dict[str, Any]]:
        if alert_id in self.alerts:
            self.alerts[alert_id]["status"] = status
            if status == "acknowledged":
                self.alerts[alert_id]["acknowledged_at"] = datetime.utcnow().isoformat()
            elif status == "resolved":
                self.alerts[alert_id]["resolved_at"] = datetime.utcnow().isoformat()
            return self.alerts[alert_id]
        return None

    # Feedback
    def add_feedback(self, fb: Dict[str, Any]) -> Dict[str, Any]:
        fb_id = str(uuid.uuid4())
        fb["id"] = fb_id
        fb["created_at"] = datetime.utcnow().isoformat()
        self.feedback[fb_id] = fb
        
        # Update post threat level if provided
        post_id = fb.get("post_id")
        if post_id and post_id in self.posts:
            self.posts[post_id]["threat_level"] = fb.get("corrected_label")
            self.posts[post_id]["analyst_corrected"] = True
            
        return fb

    def get_feedback(self) -> List[Dict[str, Any]]:
        return list(self.feedback.values())

    # Incidents / Reports
    def add_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        inc_id = incident.get("id") or str(uuid.uuid4())
        incident["id"] = inc_id
        incident["created_at"] = datetime.datetime.utcnow().isoformat() if hasattr(datetime, "datetime") else datetime.utcnow().isoformat()
        self.incidents[inc_id] = incident
        return incident

    def get_incidents(self) -> List[Dict[str, Any]]:
        return list(self.incidents.values())

# Global db & db_client singletons
db = InMemoryDatabase()
db_client = db
