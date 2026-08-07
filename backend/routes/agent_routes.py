"""Agent API endpoints — create, manage, and run custom agents."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import agents
from routes.auth import _get_user

router = APIRouter(prefix="/api/agents", tags=["agents"])


class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="")
    personality: str = Field(default="balanced")
    mode: str = Field(default="ai")
    webhook_url: str = Field(default="")
    api_provider: str = Field(default="gemini")
    model: str = Field(default="gemini-2.0-flash")
    custom_prompt: str = Field(default="")
    is_public: bool = Field(default=False)


class UpdateAgentRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    personality: str | None = None
    mode: str | None = None
    webhook_url: str | None = None
    api_provider: str | None = None
    model: str | None = None
    custom_prompt: str | None = None
    is_public: bool | None = None


class RunAgentRequest(BaseModel):
    agent_id: str
    competition_type: str  # code, trade, debate
    problem: str
    test_cases: list | None = None
    market_state: dict | None = None
    opponent_argument: str = ""


# ── CRUD ──────────────────────────────────────────────────────────

@router.post("")
async def create_agent(req: CreateAgentRequest, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return agents.create_agent(
        owner_id=user["id"], name=req.name, description=req.description,
        personality=req.personality, mode=req.mode, webhook_url=req.webhook_url,
        api_provider=req.api_provider, model=req.model,
        custom_prompt=req.custom_prompt, is_public=req.is_public,
    )


@router.get("/mine")
async def my_agents(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return agents.list_user_agents(user["id"])


@router.get("/marketplace")
async def marketplace(limit: int = 50):
    return agents.list_public_agents(limit)


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agent = agents.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}")
async def update_agent(agent_id: str, req: UpdateAgentRequest, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ag = agents.get_agent(agent_id)
    if not ag or ag["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your agent")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return agents.update_agent(agent_id, **updates)


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ag = agents.get_agent(agent_id)
    if not ag or ag["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your agent")
    agents.delete_agent(agent_id)
    return {"deleted": True}


# ── Run ───────────────────────────────────────────────────────────

@router.post("/run")
async def run_agent(req: RunAgentRequest):
    """Run a custom agent for a competition and get its response."""
    response = agents.run_agent(
        req.agent_id, req.competition_type, req.problem,
        req.test_cases, req.market_state, req.opponent_argument,
    )
    return {"response": response}
