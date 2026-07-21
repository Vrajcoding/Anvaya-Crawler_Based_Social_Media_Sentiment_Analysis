import time
from typing import Dict, Any
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

    def process(self, post: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.time()
        self.set_status("RUNNING", f"Mapping connections for {post.get('author_username', 'unknown')}")
        
        bot_clusters = network_analyzer.detect_bot_clusters()
        is_coordinated = bool(post.get("coordination_group"))
        
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += 1
        self.set_status("COMPLETED", f"Found {len(bot_clusters)} bot clusters active")
        
        self.log_memory({
            "action": "analyzed_network",
            "post_id": post.get("id"),
            "is_coordinated": is_coordinated,
            "bot_clusters_count": len(bot_clusters),
            "duration_ms": self.last_execution_time_ms
        })
        
        return {
            **post,
            "network_analysis": {
                "is_coordinated": is_coordinated,
                "bot_clusters_active": len(bot_clusters)
            }
        }

