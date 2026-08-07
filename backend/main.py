"""
Light Cycles — AI Agent Arena
Production-ready FastAPI application.
"""

import os
import sys
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from arena import Arena
from tournament import TournamentManager
from persistence import load_tournaments, load_battles, load_leaderboard
from routes import (
    battles_router, tournaments_router, debates_router, pits_router,
    auth_router, promo_router, edu_router, seo_router,
    agent_router, health_router, websocket_router,
)

# ── Config ───────────────────────────────────────────────────────────

IS_PRODUCTION = os.getenv("RENDER", "") == "1" or os.getenv("PRODUCTION", "") == "1"
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "https://light-cycleslight-cycles.onrender.com,http://localhost:8420,http://192.168.1.215:8420").split(",")
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())


# ── Middleware ────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"error": "internal_error", "detail": str(e) if not IS_PRODUCTION else "Internal server error"},
            )


# ── Lifecycle ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    print(f"⚡ Light Cycles starting (production={IS_PRODUCTION})")

    # Init arena
    app.state.arena = Arena()
    app.state.tournaments = TournamentManager()

    # Load saved state
    try:
        load_tournaments(app.state.tournaments)
        load_battles(app.state.arena)
        print(f"📦 Loaded {len(app.state.tournaments.tournaments)} tournaments, {len(app.state.arena.battles)} battles")
    except Exception as e:
        print(f"⚠️ Load state failed: {e}")

    # Leaderboard
    leaderboard_data = load_leaderboard()
    if leaderboard_data:
        for entry in leaderboard_data:
            app.state.arena.leaderboard[entry.get("agent_name", entry.get("agent", ""))] = entry.get("score", 0)

    print(f"✅ Ready — {len(app.state.arena.leaderboard)} leaderboard entries")

    yield  # App runs here

    # Shutdown
    print("⚡ Light Cycles shutting down")
    app.state.arena.cleanup()
    app.state.tournaments.cleanup()
    print("✅ Shutdown complete")


# ── App ────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Light Cycles",
        version="2.0.0",
        description="AI agent arena — code battles, trading pits, debates",
        lifespan=lifespan,
        docs_url="/api/docs" if not IS_PRODUCTION else None,
        redoc_url=None,
    )

    # Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=86400,
    )

    # Routes
    app.include_router(health_router)
    app.include_router(battles_router)
    app.include_router(tournaments_router)
    app.include_router(debates_router)
    app.include_router(pits_router)
    app.include_router(auth_router)
    app.include_router(promo_router)
    app.include_router(edu_router)
    app.include_router(seo_router)
    app.include_router(agent_router)
    app.include_router(websocket_router)

    # Leaderboard
    @app.get("/api/leaderboard")
    async def leaderboard():
        return load_leaderboard() or app.state.arena.get_leaderboard()

    # Static files — AFTER all API routes
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

    # Graceful shutdown handler
    def _shutdown(sig, frame):
        print(f"Received signal {sig}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8420"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
