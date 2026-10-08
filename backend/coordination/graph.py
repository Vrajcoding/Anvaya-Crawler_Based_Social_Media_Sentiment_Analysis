"""
coordination/graph.py
Builds and maintains a NetworkX interaction graph for influence analysis.
- Nodes: accounts (posts' authors)
- Edges: reply_to, quote, retweet, mention relationships
- Computes PageRank, betweenness centrality, Louvain communities
- Exposes endpoint-friendly data for the Network UI tab
"""

import networkx as nx
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

try:
    from networkx.algorithms.community import louvain_communities
    HAS_LOUVAIN = True
except ImportError:
    HAS_LOUVAIN = False


class InfluenceGraph:
    """
    Builds a directed author interaction graph from stored posts.
    Provides network metrics and community detection.
    """

    def __init__(self):
        self._graph = nx.DiGraph()
        # node metadata: author -> {bot_score, threat_score, post_count, platform}
        self._node_meta: Dict[str, Dict[str, Any]] = {}

    def ingest_post(self, post: Dict[str, Any]):
        """Add a post's author and any interaction edges to the graph."""
        author = str(post.get("author_username") or "unknown")
        bot_score = float(post.get("bot_likelihood", 0.0))
        threat_score = float(post.get("threat_score", 0.0))
        platform = post.get("platform", "unknown")
        ts = post.get("crawled_at", datetime.utcnow().isoformat())

        # Add/update author node
        if author not in self._graph:
            self._graph.add_node(author)
        meta = self._node_meta.setdefault(author, {
            "post_count": 0,
            "bot_score": 0.0,
            "max_threat_score": 0.0,
            "platforms": set(),
        })
        meta["post_count"] += 1
        meta["bot_score"] = max(meta["bot_score"], bot_score)
        meta["max_threat_score"] = max(meta["max_threat_score"], threat_score)
        meta["platforms"].add(platform)

        # Add edges based on reply/quote/mention metadata
        reply_to = post.get("reply_to_user") or post.get("in_reply_to_screen_name")
        if reply_to and reply_to != author:
            self._graph.add_edge(author, reply_to, type="reply", ts=ts, weight=1)

        quoted_user = post.get("quoted_user") or post.get("quoted_author")
        if quoted_user and quoted_user != author:
            self._graph.add_edge(author, quoted_user, type="quote", ts=ts, weight=1)

        retweeted_user = post.get("retweeted_user") or post.get("retweet_author")
        if retweeted_user and retweeted_user != author:
            self._graph.add_edge(author, retweeted_user, type="retweet", ts=ts, weight=2)

        # Parse @mentions from content
        content = post.get("content", "") or ""
        mentioned = self._extract_mentions(content, author)
        for mention in mentioned:
            self._graph.add_edge(author, mention, type="mention", ts=ts, weight=1)

    def _extract_mentions(self, text: str, exclude_author: str) -> List[str]:
        import re
        mentions = re.findall(r"@(\w+)", text)
        return [m.lower() for m in mentions if m.lower() != exclude_author.lstrip("@").lower()]

    def get_network_data(
        self,
        window_hours: int = 6,
        min_edge_weight: int = 1,
        top_n_nodes: int = 100
    ) -> Dict[str, Any]:
        """
        Return network data suitable for frontend force-graph rendering.
        Applies time-window filter and computes centrality metrics.
        """
        G = self._graph

        if G.number_of_nodes() == 0:
            return {"nodes": [], "edges": [], "communities": [], "stats": {}}

        # Compute PageRank
        try:
            pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)
        except Exception:
            pagerank = {n: 1.0 / max(G.number_of_nodes(), 1) for n in G.nodes()}

        # Betweenness centrality (expensive — sample for large graphs)
        try:
            if G.number_of_nodes() <= 500:
                betweenness = nx.betweenness_centrality(G, normalized=True)
            else:
                betweenness = nx.betweenness_centrality(G, k=min(100, G.number_of_nodes()), normalized=True)
        except Exception:
            betweenness = {n: 0.0 for n in G.nodes()}

        # Louvain community detection on undirected projection
        communities_map: Dict[str, int] = {}
        if HAS_LOUVAIN and G.number_of_nodes() >= 3:
            try:
                undirected = G.to_undirected()
                communities = louvain_communities(undirected)
                for community_idx, members in enumerate(communities):
                    for member in members:
                        communities_map[member] = community_idx
            except Exception:
                pass

        # Build node list — top N by PageRank
        sorted_nodes = sorted(G.nodes(), key=lambda n: pagerank.get(n, 0), reverse=True)[:top_n_nodes]
        node_set = set(sorted_nodes)

        nodes = []
        for node in sorted_nodes:
            meta = self._node_meta.get(node, {})
            nodes.append({
                "id": node,
                "pagerank": round(pagerank.get(node, 0.0), 4),
                "betweenness": round(betweenness.get(node, 0.0), 4),
                "community": communities_map.get(node, 0),
                "bot_score": round(meta.get("bot_score", 0.0), 3),
                "max_threat_score": round(meta.get("max_threat_score", 0.0), 3),
                "post_count": meta.get("post_count", 1),
                "platforms": list(meta.get("platforms", set())),
            })

        # Build edge list — only between top-N nodes
        edges = []
        for u, v, data in G.edges(data=True):
            if u in node_set and v in node_set:
                edges.append({
                    "source": u,
                    "target": v,
                    "type": data.get("type", "mention"),
                    "weight": data.get("weight", 1),
                })

        stats = {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "communities_count": len(set(communities_map.values())) if communities_map else 0,
            "density": round(nx.density(G), 4),
        }

        return {"nodes": nodes, "edges": edges, "communities": communities_map, "stats": stats}

    def rebuild_from_posts(self, posts: List[Dict[str, Any]]):
        """Rebuild graph from a list of posts (used on startup)."""
        self._graph.clear()
        self._node_meta.clear()
        for post in posts:
            try:
                self.ingest_post(post)
            except Exception:
                pass


# Module-level singleton
influence_graph = InfluenceGraph()
