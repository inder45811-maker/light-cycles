"""Trading Pit API endpoints."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from trading_pit import pit_arena
from routes.websocket import ws_manager

router = APIRouter(prefix="/api", tags=["pits"])


class CreatePitRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    asset_name: str = Field(default="SYNTH", min_length=1, max_length=20)
    agents: list[str] = Field(..., min_length=2, max_length=8)
    starting_capital: float = Field(default=10000, ge=100, le=1000000)
    total_turns: int = Field(default=60, ge=10, le=500)
    volatility: float = Field(default=0.02, ge=0.001, le=0.5)
    drift: float = Field(default=0.0, ge=-0.1, le=0.1)


@router.post("/pits")
async def create_pit(req: CreatePitRequest, request: Request):
    pit = pit_arena.create_pit(
        title=req.title,
        asset_name=req.asset_name,
        agents=req.agents,
        starting_capital=req.starting_capital,
        total_turns=req.total_turns,
        volatility=req.volatility,
        drift=req.drift,
    )

    # Run in background, broadcasting each turn
    pit_arena.run_pit(pit.id, on_turn=lambda event: None)  # WebSocket broadcast handled below

    await ws_manager.broadcast({"type": "pit_created", "pit": pit.to_dict()})

    # Start a background broadcast loop
    import asyncio
    asyncio.create_task(_broadcast_pit_turns(pit.id))

    return pit.to_dict()


async def _broadcast_pit_turns(pit_id: str):
    """Poll pit state and broadcast turns via WebSocket."""
    import asyncio
    last_turn = 0
    for _ in range(600):  # max 10 minutes
        await asyncio.sleep(1)
        pit = pit_arena.get_pit(pit_id)
        if not pit:
            break
        if pit.current_turn > last_turn:
            last_turn = pit.current_turn
            await ws_manager.broadcast({
                "type": "pit_turn",
                "pit_id": pit_id,
                "turn": pit.current_turn,
                "total_turns": pit.total_turns,
                "price": pit.price_history[-1] if pit.price_history else 0,
                "positions": pit.get_pit_state()["positions"],
                "recent_trades": pit.get_pit_state()["recent_trades"],
            })
        if pit.status.value == "complete":
            await ws_manager.broadcast({
                "type": "pit_complete",
                "pit": pit.to_dict(),
            })
            break


@router.get("/pits")
async def list_pits(request: Request = None):
    return pit_arena.list_pits()


@router.get("/pits/{pit_id}")
async def get_pit(pit_id: str, request: Request = None):
    pit = pit_arena.get_pit(pit_id)
    if not pit:
        raise HTTPException(status_code=404, detail="Pit not found")
    return pit.to_dict()
