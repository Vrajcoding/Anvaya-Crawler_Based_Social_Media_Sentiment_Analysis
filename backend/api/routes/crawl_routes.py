"""
crawl_routes.py — FastAPI router for SentinelAI Prompt Crawler endpoints.

Endpoints:
  POST /api/v1/crawl/prompt              — Multi-platform prompt crawl
  POST /api/v1/crawl/single/{platform}   — Single-platform test
  POST /api/v1/crawl/account             — Target user handle crawl
  POST /api/v1/crawl/watchlist/add       — Add to continuous watchlist
  GET  /api/v1/crawl/status              — Crawler health & stats
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from crawlers.hybrid_crawler import get_hybrid_crawler, ALL_PLATFORMS
from nlp_service.models.inference import run_nlp_pipeline
from storage.db_client import db_client

router = APIRouter(prefix="/crawl", tags=["Prompt Crawler"])


# ── Request / Response models ─────────────────────────────────────────────────

class PromptCrawlRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, example="india protest news")
    platforms: Optional[List[str]] = Field(
        default=None,
        example=["X", "YouTube", "Telegram", "Instagram"],
        description="Platforms to crawl. Defaults to all available if omitted.",
    )
    limit: int = Field(default=20, ge=1, le=5000, description="Max results per platform")
    time_filter: str = Field(default="any", description="Time filter: any, 24h, 48h, 1week, 1month")
    fetch_comments: bool = Field(
        default=False,
        description="Fetch top comments from YouTube/X",
    )


class SinglePlatformRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=5000)
    time_filter: str = "any"
    fetch_comments: bool = False


class AccountCrawlRequest(BaseModel):
    account_handle: str = Field(..., min_length=1, max_length=100, example="@target_user")
    platform: Optional[str] = Field(default="all", example="x")
    limit: int = Field(default=20, ge=1, le=5000)
    time_filter: str = "any"


class WatchlistAddRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, example="covid updates")
    platforms: List[str] = Field(default=["X", "YouTube"])
    frequency_minutes: int = Field(default=15, ge=1, le=1440)
    priority: str = Field(default="normal", pattern="^(high|normal|low)$")


# ── Helper for processing harvested posts via buildspec NLP ───────────────────

def _enrich_and_store_crawled_posts(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    for post in posts:
        post_id = str(post.get("id") or post.get("post_id") or f"crawled_{datetime.datetime.utcnow().timestamp()}")
        content = post.get("content") or post.get("text") or ""
        
        if content:
            nlp_res = run_nlp_pipeline(post_id=post_id, text=content)
            post["nlp_analysis"] = nlp_res
            post["threat_level"] = nlp_res.get("threat_category", {}).get("label", "Neutral")
            post["sentiment"] = nlp_res.get("sentiment", {}).get("label", "neutral")
            post["is_hate_speech"] = nlp_res.get("hate_speech", {}).get("flag", False)
            post["requires_review"] = nlp_res.get("requires_human_review", False)
        
        db_client.save_post(post)
        enriched.append(post)
    return enriched


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/prompt", summary="Multi-platform prompt crawl")
async def crawl_by_prompt(
    request: PromptCrawlRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Crawl selected platforms in parallel with query prompt
    and process all harvested posts through buildspec NLP threat/sentiment pipeline.
    """
    platforms = request.platforms or ALL_PLATFORMS
    crawler = get_hybrid_crawler()

    result = await crawler.crawl_multi_platform(
        queries=[request.prompt],
        platforms=platforms,
        limit=request.limit,
        fetch_comments=request.fetch_comments,
        time_filter=request.time_filter,
    )

    if "error" in result and not result.get("results"):
        raise HTTPException(status_code=400, detail=result["error"])

    # Enrich all harvested posts with real NLP inference & store centrally
    for plat, plat_res in result.get("results", {}).items():
        if isinstance(plat_res, dict) and "posts" in plat_res:
            raw_posts = plat_res.get("posts", [])
            if raw_posts:
                enriched = _enrich_and_store_crawled_posts(raw_posts)
                result["results"][plat]["posts"] = enriched

    return result


@router.post("/single/{platform}", summary="Single-platform test crawl")
async def crawl_single_platform(
    platform: str,
    request: SinglePlatformRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Crawl a single platform for targeted queries and process through buildspec NLP pipeline.
    """
    if platform not in ALL_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform '{platform}'. Valid: {ALL_PLATFORMS}",
        )

    crawler = get_hybrid_crawler()
    result = await crawler.crawl_platform(
        query=request.prompt,
        platform=platform,
        limit=request.limit,
        fetch_comments=request.fetch_comments,
        time_filter=request.time_filter,
    )

    if result.get("posts"):
        result["posts"] = _enrich_and_store_crawled_posts(result["posts"])

    return {
        "query": request.prompt,
        "platforms_crawled": 1,
        "total_posts": result.get("count", 0),
        "duration_s": result.get("duration_s", 0),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "results": {platform: result},
    }


@router.post("/account", summary="Targeted account handle/ID crawl")
async def crawl_by_account(request: AccountCrawlRequest) -> Dict[str, Any]:
    """
    Targeted Account Endpoint — crawl user posts from X, Instagram, Facebook, Telegram, or YouTube.
    """
    crawler = get_hybrid_crawler()
    target_platform = request.platform if request.platform and request.platform != "all" else "X"
    
    result = await crawler.crawl_platform(
        query=request.account_handle,
        platform=target_platform,
        limit=request.limit,
        time_filter=request.time_filter,
    )

    if result.get("posts"):
        result["posts"] = _enrich_and_store_crawled_posts(result["posts"])

    return {
        "account": request.account_handle,
        "platform": target_platform,
        "count": result.get("count", 0),
        "posts": result.get("posts", []),
        "status": result.get("status", "success"),
    }


@router.post("/watchlist/add", summary="Add query to continuous watchlist")
async def add_to_watchlist(request: WatchlistAddRequest) -> Dict[str, Any]:
    """
    Register a query for continuous background monitoring.
    """
    invalid = [p for p in request.platforms if p not in ALL_PLATFORMS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platforms: {invalid}. Valid: {ALL_PLATFORMS}",
        )

    crawler = get_hybrid_crawler()
    return crawler.add_to_watchlist(
        query=request.query,
        platforms=request.platforms,
        frequency_minutes=request.frequency_minutes,
        priority=request.priority,
    )


@router.get("/status", summary="Crawler health & statistics")
async def get_crawler_status() -> Dict[str, Any]:
    """
    Returns real-time health information for the HybridCrawler.
    """
    crawler = get_hybrid_crawler()
    return crawler.get_status()
