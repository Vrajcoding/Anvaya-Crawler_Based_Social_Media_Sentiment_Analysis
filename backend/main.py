from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import datetime
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from storage.seed_data import initialize_seed_data
from utils.config import settings
from api.routes import posts, alerts, trends, watchlist, feedback, reports, stats, settings_router, agent_status, escalation
from api.routes.crawl_routes import router as crawl_router
from api.routes.network import router as network_router
from api.routes.geo import router as geo_router
from api.websocket import ws_manager
from crawlers.spiders.real_social_spider import RealSocialCrawler
from nlp_service.models.inference import run_nlp_pipeline
from storage.db_client import db_client

# ── Coordination & Analytics modules ──────────────────────────────────────────
from coordination.duplicates import duplicate_detector
from coordination.account_signals import account_analyzer
from coordination.sync import sync_detector
from coordination.campaigns import campaign_tracker
from coordination.graph import influence_graph
from ingest.geo_tagger import geo_tagger
from analytics.risk_index import risk_index
from alerts.rules import maybe_create_alert, maybe_dispatch_alert

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs"
)

# Enable CORS for frontend Vite app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(posts.router, prefix=settings.API_PREFIX)
app.include_router(alerts.router, prefix=settings.API_PREFIX)
app.include_router(trends.router, prefix=settings.API_PREFIX)
app.include_router(watchlist.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(stats.router, prefix=settings.API_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_PREFIX)
app.include_router(agent_status.router, prefix=settings.API_PREFIX)
app.include_router(crawl_router, prefix=settings.API_PREFIX)
app.include_router(network_router, prefix=settings.API_PREFIX)
app.include_router(geo_router, prefix=settings.API_PREFIX)
app.include_router(escalation.router, prefix=settings.API_PREFIX)


def _run_coordination_pipeline(post: dict) -> dict:
    """
    Run the full real coordination analysis on a post.
    Replaces all random.random() flags with real computed values.
    """
    # 1. Geo-tag
    post = geo_tagger.tag_post(post)

    # 2. Near-duplicate detection (assigns cluster_id)
    post = duplicate_detector.process_post(post)

    # 3. Bot likelihood (real heuristics, no random())
    bot_score = account_analyzer.compute_bot_likelihood(post)
    post["bot_likelihood"] = bot_score
    post["is_bot"] = bot_score >= 0.6

    # 4. Synchronized posting detection (real coordination_group)
    post = sync_detector.process_post(post)

    # 5. Update campaign tracker
    campaign_tracker.update_from_post(post)

    # 6. Update influence graph
    influence_graph.ingest_post(post)

    # 7. Recompute threat score with REAL bot/coord values
    from scoring.threat_scorer import ThreatScorer
    nlp = post.get("nlp_analysis", {})
    s_dict = nlp.get("sentiment", {})
    t_dict = nlp.get("threat_category", {})
    h_dict = nlp.get("hate_speech", {})

    neg_prob = s_dict.get("probabilities", {}).get("negative", 0.8 if s_dict.get("label") == "negative" else 0.05)
    threat_cls_score = t_dict.get("confidence", 0.2) if t_dict.get("label", "Neutral") != "Neutral" else 0.05
    hate_score = h_dict.get("confidence", 0.0) if h_dict.get("flag") else 0.0

    # REAL values (no more constants 0.3, 0.7, 0.8)
    coord_score = post.get("sync_score", 0.0)
    bot_score_val = post.get("bot_likelihood", 0.0)
    # Engagement velocity: use duplicate cluster size as proxy
    cluster_size = post.get("duplicate_cluster_size", 1)
    engagement_velocity = min(cluster_size / 20.0, 1.0)

    scoring = ThreatScorer.calculate_score(
        sentiment_neg=neg_prob,
        threat_class_score=threat_cls_score,
        hate_speech_score=hate_score,
        engagement_velocity=engagement_velocity,
        coordination_score=coord_score,
        bot_likelihood=bot_score_val
    )
    post["threat_score"] = scoring["composite_score"]
    post["scoring_breakdown"] = {
        "sentiment": neg_prob,
        "classification": threat_cls_score,
        "hate_speech": hate_score,
        "velocity": engagement_velocity,
        "coordination": coord_score,
        "bot": bot_score_val,
    }

    # Mark data provenance
    post["data_source"] = post.get("data_source", "live")

    return post


@app.on_event("startup")
async def startup_event():
    # Initialize seed database
    initialize_seed_data()
    # Rebuild graph from stored posts
    try:
        all_posts = db_client.get_posts(limit=500)["items"]
        influence_graph.rebuild_from_posts(all_posts)
        risk_index.update(all_posts)
        print(f"[startup] Loaded {len(all_posts)} posts into graph and risk index.")
    except Exception as e:
        print(f"[startup] Warning: {e}")
    # Start background crawler task loop
    asyncio.create_task(background_crawler_loop())


async def background_crawler_loop():
    """Background task: continuous social media harvesting + real NLP + real coordination analysis."""
    cycle = 0
    while True:
        await asyncio.sleep(15)
        cycle += 1
        try:
            if settings.USE_REAL_CRAWLER:
                crawled_list = await RealSocialCrawler.fetch_live_web_posts()
                for post in (crawled_list or [])[:3]:
                    post_id = str(post.get("id") or f"bg_post_{cycle}")
                    content = post.get("content") or ""
                    if content:
                        # NLP pipeline
                        nlp_res = await asyncio.to_thread(run_nlp_pipeline, post_id=post_id, text=content)
                        post["nlp_analysis"] = nlp_res
                        post["threat_level"] = nlp_res.get("threat_category", {}).get("label", "Neutral")
                        post["sentiment"] = nlp_res.get("sentiment", {}).get("label", "neutral")
                        post["is_hate_speech"] = nlp_res.get("hate_speech", {}).get("flag", False)
                        post["language"] = nlp_res.get("language_detected", "en")

                        # ── REAL coordination pipeline (no random()) ──────────────
                        post = _run_coordination_pipeline(post)

                        # Save to DB
                        db_client.save_post(post)

                        # Auto-generate alerts from REAL threat scores
                        alert = maybe_create_alert(post)
                        if alert:
                            await maybe_dispatch_alert(alert)
                            await ws_manager.broadcast({
                                "type": "NEW_ALERT",
                                "data": alert
                            })

                        # Broadcast new post to frontend
                        await ws_manager.broadcast({
                            "type": "NEW_POST",
                            "data": post
                        })

            # Update risk index every cycle
            if cycle % 4 == 0:  # Every ~60s
                try:
                    all_posts = db_client.get_posts(limit=500)["items"]
                    risk_index.update(all_posts)
                except Exception as e:
                    print(f"[bg] Risk index update error: {e}")

        except Exception as e:
            print(f"[bg] Error in background crawler loop: {e}")


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "status": "online",
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "new_endpoints": [
            "/api/v1/network",
            "/api/v1/network/campaigns",
            "/api/v1/geo/districts",
            "/api/v1/geo/risk-index",
            "/api/v1/trends/volume",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
