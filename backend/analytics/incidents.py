"""
analytics/incidents.py
Clusters high-threat posts into distinct Incidents based on time, location, and text similarity.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
import numpy as np

class IncidentClusterer:
    """Groups high-threat posts into cohesive incidents for reporting."""

    def __init__(self):
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def build_incidents(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster posts with threat_score >= 0.70 into incidents.
        Returns a list of Incident dictionaries.
        """
        # Filter high threat posts
        high_threat = [p for p in posts if float(p.get("threat_score", 0.0)) >= 0.70]
        
        if not high_threat:
            return []

        # If very few posts, just group them all or make singletons
        if len(high_threat) < 3:
            return self._fallback_clustering(high_threat)

        texts = [p.get("content", "") for p in high_threat]
        
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            X = vectorizer.fit_transform(texts)
            
            # Use Agglomerative Clustering (cosine distance)
            clusterer = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=0.8, # Threshold for cosine distance equivalent
                metric='cosine',
                linkage='average'
            )
            labels = clusterer.fit_predict(X.toarray())
            
            # Group by label
            clusters = {}
            for idx, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(high_threat[idx])
                
            result = []
            for label, group in clusters.items():
                incident = self._create_incident_obj(group)
                result.append(incident)
                self.incidents[incident["id"]] = incident
                
            return sorted(result, key=lambda x: x["severity_score"], reverse=True)
            
        except Exception as e:
            print(f"[incidents] Clustering failed, using fallback: {e}")
            return self._fallback_clustering(high_threat)

    def _fallback_clustering(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple fallback: one incident per post if clustering fails."""
        result = []
        for p in posts:
            incident = self._create_incident_obj([p])
            result.append(incident)
            self.incidents[incident["id"]] = incident
        return sorted(result, key=lambda x: x["severity_score"], reverse=True)

    def _create_incident_obj(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate a group of posts into an Incident object."""
        # Find earliest and latest post
        times = []
        for p in group:
            ts = p.get("crawled_at") or p.get("timestamp")
            if ts:
                times.append(ts)
        times.sort()
        first_seen = times[0] if times else datetime.utcnow().isoformat()
        last_seen = times[-1] if times else datetime.utcnow().isoformat()
        
        # Get dominant district
        districts = [p.get("district") for p in group if p.get("district")]
        main_district = max(set(districts), key=districts.count) if districts else "Unknown"
        
        # Get top platforms
        platforms = list({p.get("platform", "unknown") for p in group})
        
        # Calculate severity (max threat score in group)
        max_threat = max((float(p.get("threat_score", 0.0)) for p in group), default=0.0)
        
        # Narrative summary (take longest text or highest threat)
        top_post = max(group, key=lambda x: float(x.get("threat_score", 0.0)))
        summary = top_post.get("content", "")[:250] + "..."
        
        # Extract accounts
        accounts = list({p.get("author_username", "unknown") for p in group})
        
        return {
            "id": f"inc_{str(uuid.uuid4())[:8]}",
            "title": f"Threat Incident in {main_district}",
            "narrative": summary,
            "district": main_district,
            "platforms": platforms,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "post_count": len(group),
            "severity_score": round(max_threat, 3),
            "severity_label": "CRITICAL" if max_threat >= 0.85 else "HIGH",
            "accounts": accounts[:10], # Top 10 accounts
            "evidence_posts": [p.get("id") for p in group[:5]], # Store IDs of top 5 evidence posts
            "created_at": datetime.utcnow().isoformat()
        }

# Singleton
incident_clusterer = IncidentClusterer()
