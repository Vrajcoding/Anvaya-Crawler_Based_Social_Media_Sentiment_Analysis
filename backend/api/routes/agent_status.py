from fastapi import APIRouter
from typing import Dict, Any
import datetime
from storage.db_client import db_client
from crawlers.hybrid_crawler import get_hybrid_crawler

router = APIRouter(prefix="/agents", tags=["NLP Service & System Telemetry"])

@router.get("/status", summary="Get status of NLP threat/sentiment classification service")
async def get_agents_status() -> Dict[str, Any]:
    crawler = get_hybrid_crawler()
    status_info = crawler.get_status()
    total_posts = len(db_client.get_posts())
    
    return {
        "status": "success",
        "service": "Buildspec NLP Threat & Sentiment Classification Engine",
        "models": {
            "sentiment_classifier": "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
            "zero_shot_threat_classifier": "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
            "claim_matcher_embedder": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "fine_tuned_weights": "backend/models/best_model.pt"
        },
        "total_posts_stored": total_posts,
        "crawler_status": status_info,
        "active": True
    }
