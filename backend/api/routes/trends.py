from fastapi import APIRouter, Query
from analysis.trends import TrendAnalyzer

router = APIRouter(prefix="/trends", tags=["trends"])

@router.get("/hashtags")
def get_trending_hashtags(top_n: int = Query(15)):
    return TrendAnalyzer.get_trending_hashtags(top_n=top_n)

@router.get("/keywords")
def get_trending_keywords(top_n: int = Query(15)):
    return TrendAnalyzer.get_trending_keywords(top_n=top_n)

@router.get("/volume")
def get_volume_timeline(bucket_minutes: int = Query(30)):
    """Returns time-series post volume with MAD z-score spike flags."""
    return TrendAnalyzer.get_volume_timeline(bucket_minutes=bucket_minutes)
