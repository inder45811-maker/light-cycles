"""
Light Cycles — AI Agent Arena
FastAPI backend with WebSocket, tournaments, Stripe payments.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from arena import Arena, BattleStatus
from tournament import TournamentManager, TournamentStatus, MatchStatus
from persistence import load_tournaments, load_battles, load_leaderboard, save_tournament, save_battle, update_leaderboard
from ai_competitor import ai_competitor
from debate_arena import debate_arena, DebateStatus

app = FastAPI(title="Light Cycles — AI Arena", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

arena = Arena()
tournaments = TournamentManager(
    stripe_secret=os.getenv("STRIPE_SECRET_KEY"),
    stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
)

# ── Load persisted state on startup ─────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Load persisted tournaments, battles, and leaderboard."""
    try:
        load_tournaments(tournaments)
        load_battles(arena)
        print(f"📦 Loaded {len(tournaments.tournaments)} tournaments, {len(arena.battles)} battles")
    except Exception as e:
        print(f"⚠️ Failed to load persisted state: {e}")

# ── WebSocket connection manager ──────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, event: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)

ws_manager = ConnectionManager()


# ── Models ────────────────────────────────────────────────────────────────

class TestCase(BaseModel):
    name: str
    input: str
    expected: str


class AgentConfig(BaseModel):
    name: str
    model: str = "default"


class CreateBattleRequest(BaseModel):
    title: str
    description: str
    test_cases: list[TestCase]
    agents: list[AgentConfig]


class SubmitCodeRequest(BaseModel):
    battle_id: str
    agent_name: str
    code: str


class CreateTournamentRequest(BaseModel):
    title: str
    description: str
    problem_statement: str
    test_cases: list[TestCase]
    entry_fee_cents: int
    player_cap: int = 8
    scheduled_at: float | None = None


class RegisterPlayerRequest(BaseModel):
    player_name: str


class TournamentMatchSubmit(BaseModel):
    tournament_id: str
    match_id: str
    agent_name: str
    code: str


# ── Battle Endpoints ──────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "online", "name": "Light Cycles", "version": "0.2.0"}


@app.post("/api/battles")
async def create_battle(req: CreateBattleRequest):
    battle = arena.create_battle(
        title=req.title,
        description=req.description,
        test_cases=[tc.model_dump() for tc in req.test_cases],
        agents=[a.model_dump() for a in req.agents],
    )

    await ws_manager.broadcast({
        "type": "battle_created",
        "battle": battle.to_dict(),
    })

    save_battle(battle)
    return battle.to_dict()


@app.get("/api/battles")
async def list_battles():
    return arena.list_battles()


@app.get("/api/battles/{battle_id}")
async def get_battle(battle_id: str):
    battle = arena.get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    return battle.to_dict()


@app.post("/api/submit")
async def submit_code(req: SubmitCodeRequest):
    arena.submit_code(req.battle_id, req.agent_name, req.code)

    battle = arena.get_battle(req.battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    all_done = all(a.status == "submitted" for a in battle.agents)
    if all_done:
        battle = arena.run_judging(req.battle_id)
        save_battle(battle)
        update_leaderboard(arena)
        await ws_manager.broadcast({
            "type": "battle_complete",
            "battle": battle.to_dict(),
        })

    await ws_manager.broadcast({
        "type": "agent_submitted",
        "battle_id": req.battle_id,
        "agent_name": req.agent_name,
    })

    return {"ok": True}


@app.post("/api/battles/{battle_id}/judge")
async def force_judge(battle_id: str):
    battle = arena.run_judging(battle_id)
    await ws_manager.broadcast({
        "type": "battle_complete",
        "battle": battle.to_dict(),
    })
    return battle.to_dict()


@app.get("/api/leaderboard")
async def leaderboard():
    """Get the global leaderboard (from persisted DB)."""
    return load_leaderboard() or arena.get_leaderboard()


# ── Tournament Endpoints ──────────────────────────────────────────────────

@app.post("/api/tournaments")
async def create_tournament(req: CreateTournamentRequest):
    """Create a new tournament with entry fee."""
    tournament = tournaments.create_tournament(
        title=req.title,
        description=req.description,
        problem_statement=req.problem_statement,
        test_cases=[tc.model_dump() for tc in req.test_cases],
        entry_fee_cents=req.entry_fee_cents,
        player_cap=req.player_cap,
        scheduled_at=req.scheduled_at,
    )

    await ws_manager.broadcast({
        "type": "tournament_created",
        "tournament": tournament.to_dict(),
    })

    save_tournament(tournament)
    return tournament.to_dict()


@app.get("/api/tournaments")
async def list_tournaments(status: str | None = None):
    """List tournaments, optionally filtered by status."""
    return tournaments.list_tournaments(status=status)


@app.get("/api/tournaments/{tournament_id}")
async def get_tournament(tournament_id: str):
    tournament = tournaments.get_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament.to_dict()


@app.post("/api/tournaments/{tournament_id}/register")
async def register_for_tournament(tournament_id: str, req: RegisterPlayerRequest):
    """Register a player for a tournament. Returns Stripe checkout URL if fee > 0."""
    tournament = tournaments.get_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.status not in (TournamentStatus.UPCOMING, TournamentStatus.REGISTERING):
        raise HTTPException(status_code=400, detail="Tournament is not open for registration")

    player = tournament.add_player(req.player_name)

    # If free entry, skip payment
    if tournament.entry_fee_cents == 0:
        tournament.confirm_payment(player.id, "free_entry")
        save_tournament(tournament)
        await ws_manager.broadcast({
            "type": "player_registered",
            "tournament_id": tournament_id,
            "player": {"id": player.id, "name": player.name},
        })
        return {"player": {"id": player.id, "name": player.name}, "payment_required": False}

    # Create Stripe checkout session
    base_url = os.getenv("BASE_URL", "http://localhost:8420")
    result = tournaments.create_stripe_checkout_session(
        tournament_id=tournament_id,
        player_id=player.id,
        success_url=f"{base_url}/payment-success",
        cancel_url=f"{base_url}/?tournament={tournament_id}",
    )

    if not result:
        # Fallback: mark as paid if no Stripe configured (dev mode)
        tournament.confirm_payment(player.id, f"dev_{player.id}")
        save_tournament(tournament)
        return {"player": {"id": player.id, "name": player.name}, "payment_required": False}

    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Stripe error: {result['error']}")

    return {"player": {"id": player.id, "name": player.name}, "payment_required": True, "checkout_url": result["url"]}


@app.post("/api/tournaments/{tournament_id}/start")
async def start_tournament(tournament_id: str):
    """Admin: start tournament — generate bracket and begin."""
    tournament = tournaments.start_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=400, detail="Cannot start tournament (need 2+ paid players)")

    await ws_manager.broadcast({
        "type": "tournament_started",
        "tournament": tournament.to_dict(),
    })

    save_tournament(tournament)

    # Auto-compete: spawn AI agents for each match
    for match in tournament.get_current_matches():
        if match.status == MatchStatus.PENDING:
            p1_name = tournament.players[match.player1_id].name
            p2_name = tournament.players[match.player2_id].name
            ai_competitor.start_competition(
                tournament_id=tournament.id,
                match_id=match.id,
                player1=p1_name,
                player2=p2_name,
                problem=tournament.problem_statement,
                test_cases=tournament.test_cases,
            )

    return tournament.to_dict()


@app.post("/api/tournaments/submit")
async def submit_tournament_code(req: TournamentMatchSubmit):
    """Submit code for a tournament match."""
    tournament = tournaments.get_tournament(req.tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Create a battle in the arena for this match
    match_test_cases = tournament.test_cases
    problem = tournament.problem_statement

    # Find the match
    match = None
    for m in tournament.matches:
        if m.id == req.match_id:
            match = m
            break
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    p1_name = tournament.players[match.player1_id].name
    p2_name = tournament.players[match.player2_id].name

    # Create or find battle for this match (reuse if already created for this match)
    if match.battle_id:
        battle = arena.get_battle(match.battle_id)
        if not battle:
            raise HTTPException(status_code=500, detail="Linked battle not found")
    else:
        battle_title = f"{tournament.title} — {tournament.get_round_name()} — {p1_name} vs {p2_name}"
        battle = arena.create_battle(
            title=battle_title,
            description=problem,
            test_cases=match_test_cases,
            agents=[{"name": p1_name, "model": "default"}, {"name": p2_name, "model": "default"}],
        )
        match.battle_id = battle.id

    # Submit the agent's code
    arena.submit_code(battle.id, req.agent_name, req.code)

    # Check if both submitted
    all_done = all(a.status == "submitted" for a in battle.agents)
    if all_done:
        battle = arena.run_judging(battle.id)
        winner = battle.winner

        # Report result to tournament bracket
        if winner:
            winner_player_id = match.player1_id if tournament.players[match.player1_id].name == winner else match.player2_id
            tournament.report_match_result(req.match_id, winner_player_id, battle.id)

        save_battle(battle)
        save_tournament(tournament)
        update_leaderboard(arena)

        await ws_manager.broadcast({
            "type": "tournament_match_complete",
            "tournament_id": req.tournament_id,
            "match_id": req.match_id,
            "battle": battle.to_dict(),
            "tournament": tournament.to_dict(),
        })

    await ws_manager.broadcast({
        "type": "tournament_code_submitted",
        "tournament_id": req.tournament_id,
        "match_id": req.match_id,
        "agent_name": req.agent_name,
    })

    return {"ok": True, "battle_id": battle.id}


# ── Stripe Webhook ────────────────────────────────────────────────────────

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for payment confirmations."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    event = tournaments.verify_stripe_webhook(payload, sig_header)
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        tournament_id = metadata.get("tournament_id")
        player_id = metadata.get("player_id")

        if tournament_id and player_id:
            tournaments.handle_payment_success(tournament_id, player_id, session["id"])

            await ws_manager.broadcast({
                "type": "player_paid",
                "tournament_id": tournament_id,
                "player_id": player_id,
                "paid_count": tournaments.get_tournament(tournament_id).paid_count if tournaments.get_tournament(tournament_id) else 0,
            })

    return {"received": True}


# ── Payment success page ──────────────────────────────────────────────────

@app.get("/payment-success")
async def payment_success():
    """Return a simple success page after Stripe checkout."""
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html"))


# ── WebSocket ─────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            event_type = data.get("type")

            if event_type == "ping":
                await ws.send_json({"type": "pong"})

            elif event_type == "subscribe_tournament":
                # Client subscribes to a specific tournament's updates
                # (broadcast already covers this, but we could filter)
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


# ── Debate Arena Endpoints ────────────────────────────────────────────────

class CreateDebateRequest(BaseModel):
    topic: str
    agent_for: str
    agent_against: str


@app.post("/api/debates")
async def create_debate(req: CreateDebateRequest):
    """Create and start a new debate."""
    debate = debate_arena.create_debate(
        topic=req.topic,
        agent_for=req.agent_for,
        agent_against=req.agent_against,
    )

    # Run the debate in background
    debate_arena.start_debate_async(debate.id)

    await ws_manager.broadcast({
        "type": "debate_created",
        "debate": debate.to_dict(),
    })

    return debate.to_dict()


@app.get("/api/debates")
async def list_debates():
    return debate_arena.list_debates()


@app.get("/api/debates/{debate_id}")
async def get_debate(debate_id: str):
    debate = debate_arena.get_debate(debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate.to_dict()


# ── Static files (frontend) ───────────────────────────────────────────────

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


# ── Entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8420"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
