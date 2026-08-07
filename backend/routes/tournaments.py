"""Tournament endpoints — create, register, start, submit matches."""
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from tournament import TournamentStatus, MatchStatus
from persistence import save_tournament, save_battle, update_leaderboard
from ai_competitor import ai_competitor
from routes.websocket import ws_manager

router = APIRouter(prefix="/api", tags=["tournaments"])


class TestCase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    input: str = Field(..., max_length=5000)
    expected: str = Field(..., max_length=5000)


class CreateTournamentRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(default="", max_length=500)
    problem_statement: str = Field(..., min_length=10, max_length=2000)
    test_cases: list[TestCase] = Field(..., min_length=1, max_length=20)
    entry_fee_cents: int = Field(default=0, ge=0, le=100000)
    player_cap: int = Field(default=8, ge=2, le=64)
    agent_names: list[str] = Field(default_factory=list)
    scheduled_at: float | None = None


class RegisterPlayerRequest(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=50)


class TournamentMatchSubmit(BaseModel):
    tournament_id: str
    match_id: str
    agent_name: str
    code: str = Field(..., max_length=50000)


@router.post("/tournaments")
async def create_tournament(req: CreateTournamentRequest, request: Request):
    tournaments = request.app.state.tournaments
    tournament = tournaments.create_tournament(
        title=req.title,
        description=req.description,
        problem_statement=req.problem_statement,
        test_cases=[tc.model_dump() for tc in req.test_cases],
        entry_fee_cents=req.entry_fee_cents,
        player_cap=req.player_cap,
        scheduled_at=req.scheduled_at,
    )
    await ws_manager.broadcast({"type": "tournament_created", "tournament": tournament.to_dict()})
    save_tournament(tournament)
    return tournament.to_dict()


@router.get("/tournaments")
async def list_tournaments(status: str | None = None, request: Request = None):
    return request.app.state.tournaments.list_tournaments(status=status)


@router.get("/tournaments/{tournament_id}")
async def get_tournament(tournament_id: str, request: Request):
    tournament = request.app.state.tournaments.get_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament.to_dict()


@router.post("/tournaments/{tournament_id}/register")
async def register_for_tournament(tournament_id: str, req: RegisterPlayerRequest, request: Request):
    tournaments = request.app.state.tournaments
    tournament = tournaments.get_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.status not in (TournamentStatus.UPCOMING, TournamentStatus.REGISTERING):
        raise HTTPException(status_code=400, detail="Tournament not open for registration")

    player = tournament.add_player(req.player_name)

    if tournament.entry_fee_cents == 0:
        tournament.confirm_payment(player.id, "free_entry")
        save_tournament(tournament)
        await ws_manager.broadcast({
            "type": "player_registered",
            "tournament_id": tournament_id,
            "player": {"id": player.id, "name": player.name},
        })
        return {"player": {"id": player.id, "name": player.name}, "payment_required": False}

    base_url = os.getenv("BASE_URL", "http://localhost:8420")
    result = tournaments.create_stripe_checkout_session(
        tournament_id=tournament_id,
        player_id=player.id,
        success_url=f"{base_url}/payment-success",
        cancel_url=f"{base_url}/?tournament={tournament_id}",
    )

    if not result:
        tournament.confirm_payment(player.id, f"dev_{player.id}")
        save_tournament(tournament)
        return {"player": {"id": player.id, "name": player.name}, "payment_required": False}

    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Stripe error: {result['error']}")

    return {"player": {"id": player.id, "name": player.name}, "payment_required": True, "checkout_url": result["url"]}


@router.post("/tournaments/{tournament_id}/start")
async def start_tournament(tournament_id: str, request: Request):
    tournaments = request.app.state.tournaments
    arena = request.app.state.arena

    tournament = tournaments.start_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=400, detail="Cannot start tournament (need 2+ paid players)")

    await ws_manager.broadcast({"type": "tournament_started", "tournament": tournament.to_dict()})
    save_tournament(tournament)

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


@router.post("/tournaments/submit")
async def submit_tournament_code(req: TournamentMatchSubmit, request: Request):
    tournaments = request.app.state.tournaments
    arena = request.app.state.arena

    tournament = tournaments.get_tournament(req.tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    match = None
    for m in tournament.matches:
        if m.id == req.match_id:
            match = m
            break
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    p1_name = tournament.players[match.player1_id].name
    p2_name = tournament.players[match.player2_id].name

    if match.battle_id:
        battle = arena.get_battle(match.battle_id)
        if not battle:
            raise HTTPException(status_code=500, detail="Linked battle not found")
    else:
        battle = arena.create_battle(
            title=f"{tournament.title} — {tournament.get_round_name()} — {p1_name} vs {p2_name}",
            description=tournament.problem_statement,
            test_cases=tournament.test_cases,
            agents=[{"name": p1_name, "model": "default"}, {"name": p2_name, "model": "default"}],
        )
        match.battle_id = battle.id

    arena.submit_code(battle.id, req.agent_name, req.code)

    all_done = all(a.status == "submitted" for a in battle.agents)
    if all_done:
        battle = arena.run_judging(battle.id)
        winner = battle.winner

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

        # Auto-generate social post if tournament is complete
        if tournament.status.value == "complete":
            try:
                from post_engine import queue_post
                queue_post(tournament.id, tournament.to_dict())
            except Exception:
                pass

    await ws_manager.broadcast({
        "type": "tournament_code_submitted",
        "tournament_id": req.tournament_id,
        "match_id": req.match_id,
        "agent_name": req.agent_name,
    })

    return {"ok": True, "battle_id": battle.id}
