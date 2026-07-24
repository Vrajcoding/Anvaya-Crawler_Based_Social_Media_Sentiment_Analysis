import time
from typing import Dict, Any, List
from agents.base_agent import SentinelAgent
from analysis.network import network_analyzer

class NetworkAgent(SentinelAgent):
    """Hermes Agent mapping account relationships, detecting coordinated amplification, and bot clusters."""
    
    def __init__(self):
        super().__init__("network_agent", "Graph & Network Analyst")
        self.register_tool(
            name="detect_bot_clusters",
            func=network_analyzer.detect_bot_clusters,
            description="Analyzes graph edges to identify coordinated botnet amplification rings"
        )
        self.register_tool(
            name="get_network_graph",
            func=network_analyzer.get_graph_data,
            description="Extracts force-directed graph links and nodes of active threat entities"
        )
        self.register_tool(
            name="analyze_author_node",
            func=self._analyze_author_node,
            description="Evaluates degree centrality and bot likelihood for a given author account"
        )

    def _analyze_author_node(self, author_username: str) -> Dict[str, Any]:
        graph_data = network_analyzer.get_graph_data()
        nodes = graph_data.get("nodes", [])
        author_node = next((n for n in nodes if n["id"] == author_username), None)
        if author_node:
            return author_node
        return {
            "id": author_username,
            "label": author_username,
            "type": "account",
            "is_bot": False,
            "threat_level": "Neutral",
            "val": 5
        }

    def process(self, post: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.time()
        author = post.get("author_username", "unknown")
        self.set_status("RUNNING", f"Mapping network connections for {author}")
        
        bot_clusters = self.invoke_tool("detect_bot_clusters")
        author_info = self._analyze_author_node(author)
        
        is_coordinated = bool(post.get("coordination_group"))
        is_bot = bool(post.get("is_bot") or author_info.get("is_bot"))
        
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += 1
        self.set_status("COMPLETED", f"Analyzed {author} (Bot: {is_bot}, Clusters: {len(bot_clusters)})")
        
        self.log_memory({
            "action": "analyzed_network",
            "post_id": post.get("id"),
            "author": author,
            "is_coordinated": is_coordinated,
            "is_bot": is_bot,
            "bot_clusters_count": len(bot_clusters),
            "duration_ms": self.last_execution_time_ms
        })
        
        return {
            **post,
            "is_bot": is_bot,
            "network_analysis": {
                "author_id": author,
                "is_coordinated": is_coordinated,
                "is_bot": is_bot,
                "coordination_group": post.get("coordination_group"),
                "bot_clusters_active": len(bot_clusters)
            }
        }


