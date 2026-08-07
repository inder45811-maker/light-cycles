"""
Light Cycles — AI Agent Arena
FastAPI application with WebSocket, tournaments, Stripe payments, debates.
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from arena import Arena
from tournament import TournamentManager
from persistence import load_tournaments, load_battles, load_leaderboard
from routes import battles_router, tournaments_router, debates_router, pits_router, auth_router, promo_router, edu_router, seo_router, agent_router, health_router, websocket_router


def create_app() -> FastAPI:
    app = FastAPI(title="Light Cycles — AI Arena", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared state
    app.state.arena = Arena()
    app.state.tournaments = TournamentManager(
        stripe_secret=os.getenv("STRIPE_SECRET_KEY"),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
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

    # Stripe webhook
    @app.post("/api/stripe/webhook")
    async def stripe_webhook(request: __import__("fastapi").Request):
        from fastapi import HTTPException
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")
        event = app.state.tournaments.verify_stripe_webhook(payload, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid signature")
        if event.get("type") == "checkout.session.completed":
            session = event["data"]["object"]
            meta = session.get("metadata", {})
            tid, pid = meta.get("tournament_id"), meta.get("player_id")
            if tid and pid:
                app.state.tournaments.handle_payment_success(tid, pid, session["id"])
        return {"received": True}

    # Startup
    @app.on_event("startup")
    async def startup():
        try:
            load_tournaments(app.state.tournaments)
            load_battles(app.state.arena)
            print(f"📦 Loaded {len(app.state.tournaments.tournaments)} tournaments, {len(app.state.arena.battles)} battles")
        except Exception as e:
            print(f"⚠️ Load state failed: {e}")

    # Static files — AFTER all API routes so they take priority
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8420"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
