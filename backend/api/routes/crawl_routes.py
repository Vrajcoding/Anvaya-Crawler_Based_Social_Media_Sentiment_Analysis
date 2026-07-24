"""
crawl_routes.py — FastAPI router for SentinelAI v2.1 Prompt Crawler endpoints.

4 new endpoints:
  POST /api/v1/crawl/prompt              — Multi-platform prompt crawl
  POST /api/v1/crawl/single/{platform}   — Single-platform test
  POST /api/v1/crawl/watchlist/add       — Add to continuous watchlist
  GET  /api/v1/crawl/status              — Crawler health & stats
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from crawlers.hybrid_crawler import get_hybrid_crawler, ALL_PLATFORMS

router = APIRouter(prefix="/crawl", tags=["Prompt Crawler v2.1"])


# ── Request / Response models ─────────────────────────────────────────────────

class PromptCrawlRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, example="india protest news")
    platforms: Optional[List[str]] = Field(
        default=None,
        example=["X", "YouTube", "GoogleSuggest", "Web"],
        description="Platforms to crawl. Defaults to all 5 if omitted.",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results per platform")
    fetch_comments: bool = Field(
        default=False,
        description="Fetch top comments from YouTube/X (adds ~30-45s per video)",
    )


class SinglePlatformRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)
    fetch_comments: bool = False


class WatchlistAddRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, example="covid updates")
    platforms: List[str] = Field(default=["X", "YouTube"])
    frequency_minutes: int = Field(default=15, ge=1, le=1440)
    priority: str = Field(default="normal", pattern="^(high|normal|low)$")


# ── Background Kafka publish helper (no-op if Kafka not configured) ──────────

async def _publish_to_kafka(crawl_results: Dict[str, Any]) -> None:
    """
    Best-effort background task: flatten crawl results and send to raw-posts topic.
    Silently skipped if Kafka broker is not available (demo mode).
    """
    try:
        from utils.config import settings
        broker = getattr(settings, "KAFKA_BROKER", None)
        if not broker:
            return

        from aiokafka import AIOKafkaProducer  # type: ignore
        import json

        producer = AIOKafkaProducer(bootstrap_servers=broker)
        await producer.start()
        try:
            for platform_data in crawl_results.get("results", {}).values():
                for post in platform_data.get("posts", []):
                    value = json.dumps(post).encode("utf-8")
                    await producer.send_and_wait("raw-posts", value=value)
        finally:
            await producer.stop()
    except Exception as e:
        print(f"[crawl_routes] Kafka publish skipped: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/prompt", summary="Multi-platform prompt crawl")
async def crawl_by_prompt(
    request: PromptCrawlRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    **Main endpoint** — crawl all selected platforms in parallel with one prompt
    and process all harvested posts through the 6-agent Hermes pipeline.
    """
    from agents.orchestrator import orchestrator
    platforms = request.platforms or ALL_PLATFORMS
    crawler = get_hybrid_crawler()

    result = await crawler.crawl_multi_platform(
        queries=[request.prompt],
        platforms=platforms,
        limit=request.limit,
        fetch_comments=request.fetch_comments,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Run all harvested posts through 6-agent Hermes pipeline
    flattened_posts = []
    for platform_res in result.get("results", {}).values():
        if isinstance(platform_res, dict) and "posts" in platform_res:
            flattened_posts.extend(platform_res.get("posts", []))
            
    if flattened_posts:
        orchestrator.process_crawled_posts(flattened_posts)

    # Publish to Kafka asynchronously (non-blocking)
    background_tasks.add_task(_publish_to_kafka, result)

    return result


@router.post("/single/{platform}", summary="Single-platform test crawl")
async def crawl_single_platform(
    platform: str,
    request: SinglePlatformRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Crawl a single platform for quick testing or targeted queries and run through Hermes pipeline.
    Platform must be one of: X, YouTube, Instagram, GoogleSuggest, Web
    """
    from agents.orchestrator import orchestrator
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
    )

    # Wrap in same shape as multi-platform for UI consistency
    wrapped = {
        "query": request.prompt,
        "platforms_crawled": 1,
        "total_posts": result.get("count", 0),
        "duration_s": result.get("duration_s", 0),
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "results": {platform: result},
    }

    if result.get("posts"):
        orchestrator.process_crawled_posts(result["posts"])

    background_tasks.add_task(_publish_to_kafka, wrapped)
    return wrapped



@router.post("/watchlist/add", summary="Add query to continuous watchlist")
async def add_to_watchlist(request: WatchlistAddRequest) -> Dict[str, Any]:
    """
    Register a query for continuous background monitoring.
    Returns a `watchlist_id` that can be used to track/cancel the job.
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
    Returns real-time health information for the HybridCrawler v2.0:
    - Active watchlist count
    - Total posts crawled this session
    - Uptime and last crawl timestamp
    - Platform availability
    """
    crawler = get_hybrid_crawler()
    return crawler.get_status()
