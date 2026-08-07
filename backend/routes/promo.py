"""Auto-promotion endpoints — generate viral posts from battle results."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from promo_engine import generate_all, battle_to_result

router = APIRouter(prefix="/api/promo", tags=["promo"])


class PromoRequest(BaseModel):
    battle_id: str | None = None
    tournament_id: str | None = None
    pit_id: str | None = None
    debate_id: str | None = None


@router.post("/generate")
async def generate_promo(req: PromoRequest, request: Request):
    """Generate social media posts from any battle type."""
    arena = request.app.state.arena
    tournaments = request.app.state.tournaments

    battle_data = None

    if req.battle_id:
        b = arena.get_battle(req.battle_id)
        if b:
            battle_data = b.to_dict()

    elif req.tournament_id:
        t = tournaments.get_tournament(req.tournament_id)
        if t and t.status.value == "complete":
            battle_data = t.to_dict()

    elif req.pit_id:
        from trading_pit import pit_arena
        p = pit_arena.get_pit(req.pit_id)
        if p and p.status.value == "complete":
            battle_data = p.to_dict()

    elif req.debate_id:
        from debate_arena import debate_arena
        d = debate_arena.get_debate(req.debate_id)
        if d and d.status.value == "complete":
            battle_data = d.to_dict()

    if not battle_data:
        raise HTTPException(status_code=400, detail="No completed battle found with that ID")

    result = battle_to_result(battle_data)
    posts = generate_all(result)

    return {
        "result": {
            "title": result.title,
            "mode": result.mode,
            "winner": result.winner,
            "loser": result.loser,
            "score": result.score,
            "prize": result.prize,
            "pnl": result.pnl,
        },
        "posts": posts,
    }
