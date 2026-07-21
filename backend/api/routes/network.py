from fastapi import APIRouter
from analysis.network import network_analyzer

router = APIRouter(prefix="/network", tags=["network"])

@router.get("/graph")
def get_network_graph():
    return network_analyzer.get_graph_data()

@router.get("/bots")
def get_bot_clusters():
    return network_analyzer.detect_bot_clusters()
