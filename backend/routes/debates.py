"""Debate arena endpoints."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from debate_arena import debate_arena
from routes.websocket import ws_manager

router = APIRouter(prefix="/api", tags=["debates"])


class CreateDebateRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=300)
    agent_for: str = Field(..., min_length=1, max_length=50)
    agent_against: str = Field(..., min_length=1, max_length=50)


@router.post("/debates")
async def create_debate(req: CreateDebateRequest, request: Request):
    debate = debate_arena.create_debate(
        topic=req.topic,
        agent_for=req.agent_for,
        agent_against=req.agent_against,
    )
    debate_arena.start_debate_async(debate.id)
    await ws_manager.broadcast({"type": "debate_created", "debate": debate.to_dict()})
    return debate.to_dict()


@router.get("/debates")
async def list_debates(request: Request = None):
    return debate_arena.list_debates()


@router.get("/debates/{debate_id}")
async def get_debate(debate_id: str, request: Request = None):
    debate = debate_arena.get_debate(debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate.to_dict()
