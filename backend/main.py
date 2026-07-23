from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from storage.seed_data import initialize_seed_data
from utils.config import settings
from api.routes import posts, alerts, trends, network, watchlist, feedback, reports, stats, settings_router, agent_status
from api.routes.crawl_routes import router as crawl_router
from api.websocket import ws_manager
from agents.orchestrator import orchestrator
from crawlers.spiders.real_social_spider import RealSocialCrawler

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs"
)

# Enable CORS for frontend Vite app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(posts.router, prefix=settings.API_PREFIX)
app.include_router(alerts.router, prefix=settings.API_PREFIX)
app.include_router(trends.router, prefix=settings.API_PREFIX)
app.include_router(network.router, prefix=settings.API_PREFIX)
app.include_router(watchlist.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(stats.router, prefix=settings.API_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_PREFIX)
app.include_router(agent_status.router, prefix=settings.API_PREFIX)
app.include_router(crawl_router, prefix=settings.API_PREFIX)


@app.on_event("startup")
async def startup_event():
    # Initialize seed database
    initialize_seed_data()
    # Start background crawler task loop
    asyncio.create_task(background_crawler_loop())

async def background_crawler_loop():
    """Background task running continuous live social media harvesting, Scapy packet capture, and multi-agent processing."""
    cycle = 0
    platforms = ["x", "instagram", "facebook", "youtube"]
    while True:
        await asyncio.sleep(10)  # Crawl new post every 10 seconds
        cycle += 1
        try:
            if settings.USE_REAL_CRAWLER and cycle % 4 == 1:
                # Refresh live RSS/web feeds every 40 seconds
                await RealSocialCrawler.fetch_live_web_posts()
                
            platform = platforms[cycle % len(platforms)]
            res = orchestrator.trigger_live_crawl_step(platform=platform)
            post = res.get("post")
            alert = res.get("alert")
            
            # Broadcast to WebSocket clients
            await ws_manager.broadcast({
                "type": "NEW_POST",
                "data": post
            })
            
            if alert:
                await ws_manager.broadcast({
                    "type": "NEW_ALERT",
                    "data": alert
                })
        except Exception as e:
            print(f"Error in background crawler loop: {e}")


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep alive loop
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
