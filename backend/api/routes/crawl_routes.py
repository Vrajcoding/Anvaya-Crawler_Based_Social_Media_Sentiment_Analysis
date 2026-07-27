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
    Reddit posts are scored by the Hermes multi-signal engine (0-100) and
    returned sorted by score descending.
    """
    from agents.orchestrator import orchestrator
    import re, datetime as _dt

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

    # ── Hermes multi-signal scorer for Reddit ────────────────────────────────
    if "Reddit" in result.get("results", {}):
        reddit_result = result["results"]["Reddit"]
        reddit_posts  = reddit_result.get("posts", [])

        if reddit_posts:
            scored_posts = []
            for post in reddit_posts:
                try:
                    score_data = _hermes_score_reddit_post(post, request.prompt)
                    post.update(score_data)
                    scored_posts.append(post)
                except Exception as e:
                    print(f"[HermesReddit] Scoring error for {post.get('id')}: {e}")
                    post["hermes_score"] = 0
                    post["hermes_severity"] = "LOW"
                    scored_posts.append(post)

            # Sort highest score first
            scored_posts.sort(key=lambda p: p.get("hermes_score", 0), reverse=True)
            result["results"]["Reddit"]["posts"] = scored_posts
            result["results"]["Reddit"]["hermes_scored"] = True

    # Run all harvested posts through full 6-agent pipeline (background store)
    flattened_posts = []
    for platform_res in result.get("results", {}).values():
        if isinstance(platform_res, dict) and "posts" in platform_res:
            flattened_posts.extend(platform_res.get("posts", []))

    if flattened_posts:
        orchestrator.process_crawled_posts(flattened_posts)

    background_tasks.add_task(_publish_to_kafka, result)
    return result


def _hermes_score_reddit_post(post: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    Proper multi-signal Hermes scoring for a Reddit post (0-100).

    Six independent signals, each scored 0.0–1.0, then weighted:
      Signal 1 – Negative Sentiment     (weight 0.20)
      Signal 2 – Threat Classification  (weight 0.30)
      Signal 3 – Hate Speech            (weight 0.20)
      Signal 4 – Engagement Velocity    (weight 0.15)
      Signal 5 – Query Relevance        (weight 0.10)
      Signal 6 – Recency                (weight 0.05)
    """
    import re, datetime as _dt, math

    text = (post.get("content") or "").lower()
    raw_text = (post.get("content") or "")

    # ── Signal 1: Sentiment (negative polarity detection) ────────────────────
    # Rich English + Hindi + Gujarati lexicons
    NEGATIVE_WORDS = {
        # English — threat/violence/hate
        "attack", "attacked", "violence", "violent", "riot", "riots", "burn", "burned",
        "burning", "kill", "killed", "murder", "hate", "hatred", "threat", "threaten",
        "threatening", "dangerous", "danger", "terror", "terrorist", "bomb", "explosion",
        "injured", "injury", "arrested", "clash", "clashes", "mob", "rampage", "loot",
        "looting", "destroy", "destroyed", "arson", "fire", "shot", "shooting",
        # English — inflammatory
        "puke", "disgusting", "filth", "filthy", "ugly", "ugliness", "vile", "traitor",
        "criminal", "corrupt", "corruption", "scam", "fraud", "fake", "liar", "lie",
        "mislead", "misleading", "propaganda", "conspiracy", "extremist", "radical",
        "illegal", "arrested", "detained", "abuse", "abused", "abusive", "harass",
        "harassment", "discrimination", "racist", "communal", "communalism",
        "incite", "incitement", "provocative", "inflammatory", "outrage", "outraging",
        "condemn", "condemning", "protest", "opposition", "agitation", "revolt",
        "insult", "insulting", "derogatory", "offensive", "appalling",
        # Hindi/Urdu transliterated
        "danga", "dangai", "aatank", "aatanki", "naxal", "naxali", "bhagao",
        "maar", "maaro", "jalao", "loot", "desh drohi", "gaddar", "bahari",
        # Gujarati transliterated
        "pathrav", "hungamo", "tofan", "danga", "hatyakand",
    }
    POSITIVE_WORDS = {
        "peace", "peaceful", "harmony", "unity", "help", "support", "relief",
        "development", "progress", "good", "great", "excellent", "safe", "safety",
        "rescue", "aid", "assistance", "care", "forgive", "forgiveness", "healing",
        "hope", "celebrate", "celebration", "success", "victory", "achievement",
        "resolve", "resolution", "dialogue", "cooperation", "solidarity",
    }

    words = re.findall(r'\b\w+\b', text)
    neg_hits = sum(1 for w in words if w in NEGATIVE_WORDS)
    pos_hits = sum(1 for w in words if w in POSITIVE_WORDS)
    total_words = max(len(words), 1)

    # Net negative density (capped at 0.0–1.0)
    neg_density = min(neg_hits / max(total_words * 0.15, 1), 1.0)
    pos_offset  = min(pos_hits / max(total_words * 0.15, 1), 0.5)
    sentiment_score = max(0.0, neg_density - pos_offset * 0.5)
    sentiment_score = min(sentiment_score, 1.0)

    # ── Signal 2: Threat classification (4-tier) ─────────────────────────────
    INCITEMENT_PATTERNS = [
        r'\battack\b', r'\bkill\b', r'\bmurder\b', r'\bviolence\b', r'\briot[s]?\b',
        r'\bbomb\b', r'\bburn\b', r'\bterror\b', r'\bblood\b', r'\bshot\b',
        r'\bpetrol bomb\b', r'\bpath[a]rav\b', r'\bjal[a]o\b', r'\bmaar[o]?\b',
        r'\bda[n]ga\b', r'\bhatyak[a]nd\b',
    ]
    INFLAMMATORY_PATTERNS = [
        r'\btraitor\b', r'\bgaddar\b', r'\binflammatory\b', r'\bprovocative\b',
        r'\boutrage\b', r'\bcommunal\b', r'\bextremist\b', r'\bradical\b',
        r'\bpuke[\-\s]inducing\b', r'\bdisgusting\b', r'\bfilth\b', r'\buglin\w+\b',
        r'\binsult\b', r'\bderogatory\b', r'\bappalling\b', r'\bcondemn\b',
        r'\bprotest\b', r'\bagitation\b', r'\bopposition\b',
    ]
    FAKE_NEWS_PATTERNS = [
        r'\bfake\b', r'\bbreaking news\b', r'\bviral\b', r'\bmisinform\w*\b',
        r'\bpropaganda\b', r'\bconspiracy\b', r'\bmisleading\b', r'\bfact check\b',
        r'\bfalse\b', r'\bhoax\b', r'\bdisinform\w*\b',
    ]

    incitement_hits  = sum(1 for p in INCITEMENT_PATTERNS  if re.search(p, text))
    inflammatory_hits = sum(1 for p in INFLAMMATORY_PATTERNS if re.search(p, text))
    fake_news_hits   = sum(1 for p in FAKE_NEWS_PATTERNS   if re.search(p, text))

    if incitement_hits >= 1:
        threat_level = "Incitement to Violence"
        threat_score = min(0.75 + incitement_hits * 0.05, 0.98)
    elif inflammatory_hits >= 2:
        threat_level = "Inflammatory"
        threat_score = min(0.55 + inflammatory_hits * 0.04, 0.85)
    elif inflammatory_hits == 1:
        threat_level = "Inflammatory"
        threat_score = 0.50
    elif fake_news_hits >= 1:
        threat_level = "Fake News"
        threat_score = min(0.50 + fake_news_hits * 0.06, 0.80)
    else:
        threat_level = "Neutral"
        threat_score = max(0.0, sentiment_score * 0.25)   # mild risk from sentiment

    # ── Signal 3: Hate speech ─────────────────────────────────────────────────
    HATE_PATTERNS = [
        r'\btraitor[s]?\b', r'\bgaddar\b', r'\bhateful\b', r'\bhate speech\b',
        r'\bslur[s]?\b', r'\bderogatory\b', r'\bracisl[t]?\b', r'\bxenophob\w*\b',
        r'\bcommunal hate\b', r'\banti[\-\s]muslim\b', r'\banti[\-\s]hindu\b',
        r'\bcommunal\b', r'\bsectarian\b', r'\bdiscrim\w+\b',
    ]
    hate_hits   = sum(1 for p in HATE_PATTERNS if re.search(p, text))
    hate_score  = min(hate_hits * 0.30, 1.0)
    is_hate     = hate_hits > 0

    # ── Signal 4: Engagement velocity ────────────────────────────────────────
    eng     = post.get("engagement") or {}
    upvotes = int(eng.get("likes") or 0)
    coms    = int(eng.get("comments") or 0)

    # Log-scale normalisation: 1000 upvotes → ~0.75, 100 → ~0.50, 10 → ~0.25
    upvote_vel = min(math.log10(upvotes + 1) / 4.0, 1.0) if upvotes > 0 else 0.0
    comment_vel = min(math.log10(coms + 1) / 3.0, 1.0)  if coms    > 0 else 0.0
    velocity    = (upvote_vel * 0.6) + (comment_vel * 0.4)

    # ── Signal 5: Query relevance ─────────────────────────────────────────────
    query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
    text_words  = set(re.findall(r'\b\w{3,}\b', text))
    if query_words:
        relevance = len(query_words & text_words) / len(query_words)
        relevance = min(relevance, 1.0)
    else:
        relevance = 0.5

    # ── Signal 6: Recency (within last 24 h) ─────────────────────────────────
    recency = 0.5   # default mid
    try:
        created = post.get("created_at") or ""
        if created:
            created_dt = _dt.datetime.fromisoformat(created.replace("Z", ""))
            age_hours  = (_dt.datetime.utcnow() - created_dt).total_seconds() / 3600
            recency    = max(0.0, 1.0 - (age_hours / 24.0))   # 0h → 1.0, 24h → 0.0
    except Exception:
        pass

    # ── Weighted composite ────────────────────────────────────────────────────
    W_SENTIMENT  = 0.20
    W_THREAT     = 0.30
    W_HATE       = 0.20
    W_VELOCITY   = 0.15
    W_RELEVANCE  = 0.10
    W_RECENCY    = 0.05

    composite = (
        W_SENTIMENT * sentiment_score +
        W_THREAT    * threat_score    +
        W_HATE      * hate_score      +
        W_VELOCITY  * velocity        +
        W_RELEVANCE * relevance       +
        W_RECENCY   * recency
    )
    composite = round(min(max(composite, 0.0), 1.0), 4)

    # ── Severity mapping ──────────────────────────────────────────────────────
    if composite >= 0.70:
        severity = "CRITICAL"
    elif composite >= 0.50:
        severity = "HIGH"
    elif composite >= 0.30:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    hermes_score = round(composite * 100)

    return {
        "hermes_score":    hermes_score,
        "hermes_severity": severity,
        "hermes_reason":   f"{threat_level} content | neg_density={round(neg_density,2)}, neg_hits={neg_hits}, pos_hits={pos_hits}",
        "hermes_breakdown": {
            "sentiment":  round(W_SENTIMENT * sentiment_score, 3),
            "threat":     round(W_THREAT    * threat_score,    3),
            "hate":       round(W_HATE      * hate_score,      3),
            "velocity":   round(W_VELOCITY  * velocity,        3),
            "relevance":  round(W_RELEVANCE * relevance,       3),
            "recency":    round(W_RECENCY   * recency,         3),
        },
        "threat_level":    threat_level,
        "is_hate_speech":  is_hate,
    }





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

class AccountCrawlRequest(BaseModel):
    account_handle: str = Field(..., min_length=1, max_length=100, example="@target_user")
    platform: Optional[str] = Field(default="all", example="x")
    limit: int = Field(default=20, ge=1, le=100)


@router.post("/account", summary="Targeted account handle/ID crawl")
async def crawl_by_account(request: AccountCrawlRequest) -> Dict[str, Any]:
    """
    **Targeted Account Endpoint** — crawl posts, tweets, photos, or videos directly from
    a specified user account handle/ID across X, Instagram, Facebook, or YouTube.
    """
    from agents.orchestrator import orchestrator
    return orchestrator.process_account_crawl(
        account_handle=request.account_handle,
        platform=request.platform or "all",
        limit=request.limit
    )




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
