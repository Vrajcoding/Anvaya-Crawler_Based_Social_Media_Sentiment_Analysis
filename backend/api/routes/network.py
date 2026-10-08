"""
api/routes/network.py
Network graph API endpoint for the frontend Network tab.
Returns nodes, edges, community data for force-directed graph rendering.
"""

from fastapi import APIRouter, Query
from typing import Optional
from coordination.graph import influence_graph
from coordination.campaigns import campaign_tracker
from storage.db_client import db

router = APIRouter(prefix="/network", tags=["network"])


@router.get("")
def get_network(
    window_hours: int = Query(6, description="Time window in hours"),
    min_edge: int = Query(1, description="Minimum edge weight to include"),
    top_n: int = Query(100, description="Maximum nodes to return"),
):
    """
    Returns network graph data for force-directed visualization.
    Nodes = accounts, Edges = interactions (reply/quote/retweet/mention).
    """
    # Ensure graph is up to date
    all_posts = db.get_posts(limit=500)["items"]
    influence_graph.rebuild_from_posts(all_posts)

    network_data = influence_graph.get_network_data(
        window_hours=window_hours,
        min_edge_weight=min_edge,
        top_n_nodes=top_n,
    )
    return network_data


@router.get("/campaigns")
def get_campaigns():
    """Return all detected coordination campaigns."""
    return {
        "campaigns": campaign_tracker.get_all_campaigns(),
        "total": len(campaign_tracker.get_all_campaigns()),
    }


@router.get("/stats")
def get_network_stats():
    """Return quick network statistics for the dashboard."""
    all_posts = db.get_posts(limit=500)["items"]
    influence_graph.rebuild_from_posts(all_posts)
    data = influence_graph.get_network_data(top_n_nodes=200)
    return {
        "total_nodes": data["stats"].get("total_nodes", 0),
        "total_edges": data["stats"].get("total_edges", 0),
        "communities_count": data["stats"].get("communities_count", 0),
        "density": data["stats"].get("density", 0),
        "campaigns_count": len(campaign_tracker.get_all_campaigns()),
    }
