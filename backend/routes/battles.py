"""Battle endpoints — create, list, submit code, judge."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from arena import BattleStatus
from persistence import save_battle, update_leaderboard
from routes.websocket import ws_manager

router = APIRouter(prefix="/api", tags=["battles"])


class TestCase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    input: str = Field(..., max_length=5000)
    expected: str = Field(..., max_length=5000)


class AgentConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    model: str = "default"


class CreateBattleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    test_cases: list[TestCase] = Field(..., min_length=1, max_length=20)
    agents: list[AgentConfig] = Field(..., min_length=2, max_length=4)


class SubmitCodeRequest(BaseModel):
    battle_id: str
    agent_name: str
    code: str = Field(..., max_length=50000)


@router.post("/battles")
async def create_battle(req: CreateBattleRequest, request: Request):
    arena = request.app.state.arena
    battle = arena.create_battle(
        title=req.title,
        description=req.description,
        test_cases=[tc.model_dump() for tc in req.test_cases],
        agents=[a.model_dump() for a in req.agents],
    )
    await ws_manager.broadcast({"type": "battle_created", "battle": battle.to_dict()})
    save_battle(battle)
    return battle.to_dict()


@router.get("/battles")
async def list_battles(request: Request):
    return request.app.state.arena.list_battles()


@router.get("/battles/{battle_id}")
async def get_battle(battle_id: str, request: Request):
    battle = request.app.state.arena.get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    return battle.to_dict()


@router.post("/submit")
async def submit_code(req: SubmitCodeRequest, request: Request):
    arena = request.app.state.arena
    arena.submit_code(req.battle_id, req.agent_name, req.code)

    battle = arena.get_battle(req.battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    all_done = all(a.status == "submitted" for a in battle.agents)
    if all_done:
        battle = arena.run_judging(req.battle_id)
        save_battle(battle)
        update_leaderboard(arena)
        await ws_manager.broadcast({"type": "battle_complete", "battle": battle.to_dict()})
        # Auto-generate social post
        try:
            from post_engine import queue_post
            queue_post(battle.id, battle.to_dict())
        except Exception:
            pass

    await ws_manager.broadcast({
        "type": "agent_submitted",
        "battle_id": req.battle_id,
        "agent_name": req.agent_name,
    })

    return {"ok": True}


@router.post("/battles/{battle_id}/judge")
async def force_judge(battle_id: str, request: Request):
    arena = request.app.state.arena
    battle = arena.run_judging(battle_id)
    save_battle(battle)
    update_leaderboard(arena)
    await ws_manager.broadcast({"type": "battle_complete", "battle": battle.to_dict()})
    return battle.to_dict()
