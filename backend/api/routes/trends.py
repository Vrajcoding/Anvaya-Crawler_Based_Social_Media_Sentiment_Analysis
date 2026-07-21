from fastapi import APIRouter
from analysis.trends import TrendAnalyzer

router = APIRouter(prefix="/trends", tags=["trends"])

@router.get("/hashtags")
def get_trending_hashtags():
    return TrendAnalyzer.get_trending_hashtags(top_n=15)

@router.get("/keywords")
def get_trending_keywords():
    return TrendAnalyzer.get_trending_keywords(top_n=15)
