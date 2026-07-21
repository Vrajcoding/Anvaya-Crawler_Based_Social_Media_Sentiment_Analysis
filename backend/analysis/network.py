import networkx as nx
from typing import List, Dict, Any, Tuple
from storage.db_client import db

class NetworkAnalyzer:
    """Network graph analysis engine for bot detection, coordination mapping, and viral spread tracing."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_graph_from_db()

    def _build_graph_from_db(self):
        """Construct graph nodes and edges from stored posts."""
        self.graph.clear()
        posts = db.get_posts(limit=200)["items"]
        
        for post in posts:
            author = post.get("author_username")
            post_id = post.get("id")
            platform = post.get("platform")
            is_bot = post.get("is_bot", False)
            threat_level = post.get("threat_level")
            coord_group = post.get("coordination_group")
            
            if not author or not post_id:
                continue
                
            # Add author account node
            self.graph.add_node(
                author,
                type="account",
                platform=platform,
                is_bot=is_bot,
                coord_group=coord_group
            )
            
            # Add post node
            self.graph.add_node(
                post_id,
                type="post",
                platform=platform,
                threat_level=threat_level,
                content_preview=post.get("content", "")[:40]
            )
            
            # Add POSTED edge
            self.graph.add_edge(author, post_id, relation="POSTED")
            
            # Add coordination edges between accounts sharing same group
            if coord_group:
                other_accounts = [
                    p.get("author_username") for p in posts 
                    if p.get("coordination_group") == coord_group and p.get("author_username") != author
                ]
                for other in other_accounts:
                    if other:
                        self.graph.add_node(other, type="account", platform=platform, is_bot=True, coord_group=coord_group)
                        self.graph.add_edge(author, other, relation="COORDINATED_WITH", weight=0.9)

    def get_graph_data(self) -> Dict[str, Any]:
        """Format graph for React-Force-Graph component."""
        self._build_graph_from_db()
        nodes = []
        links = []
        
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": node_id,
                "type": attrs.get("type", "account"),
                "is_bot": attrs.get("is_bot", False),
                "threat_level": attrs.get("threat_level", "Neutral"),
                "platform": attrs.get("platform", "x"),
                "val": 10 if attrs.get("is_bot") else (15 if attrs.get("type") == "post" else 5)
            })
            
        for u, v, attrs in self.graph.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "relation": attrs.get("relation", "LINKED"),
                "weight": attrs.get("weight", 1.0)
            })
            
        return {
            "nodes": nodes,
            "links": links
        }

    def detect_bot_clusters(self) -> List[Dict[str, Any]]:
        """Identify automated bot network clusters."""
        posts = db.get_posts(limit=200)["items"]
        bots = [p for p in posts if p.get("is_bot")]
        
        clusters = {}
        for b in bots:
            group = b.get("coordination_group") or "unknown_botnet"
            if group not in clusters:
                clusters[group] = {
                    "cluster_id": group,
                    "account_count": 0,
                    "accounts": set(),
                    "threat_level": b.get("threat_level"),
                    "high_velocity": True
                }
            clusters[group]["accounts"].add(b.get("author_username"))
            clusters[group]["account_count"] = len(clusters[group]["accounts"])
            
        result = []
        for c in clusters.values():
            c["accounts"] = list(c["accounts"])
            result.append(c)
            
        return result

# Singleton
network_analyzer = NetworkAnalyzer()
