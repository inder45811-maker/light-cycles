"""Post queue API — review and manage auto-generated social media posts."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import post_engine

router = APIRouter(prefix="/api/posts", tags=["posts"])


class MarkPostedRequest(BaseModel):
    platform: str  # twitter, reddit, discord


@router.get("/queue")
async def get_queue(limit: int = 20):
    return {
        "posts": post_engine.get_pending_posts(limit),
        "stats": post_engine.get_post_count(),
    }


@router.post("/{post_id}/mark")
async def mark_posted(post_id: str, req: MarkPostedRequest):
    ok = post_engine.mark_posted(post_id, req.platform)
    if not ok:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"marked": True, "platform": req.platform}


@router.delete("/{post_id}")
async def delete_post(post_id: str):
    post_engine.delete_post(post_id)
    return {"deleted": True}


@router.post("/generate/{battle_id}")
async def generate_for_battle(battle_id: str):
    """Manually trigger post generation for a specific battle."""
    # Try each type
    from routes.battles import _get_arena
    arena = _get_arena()
    battle = arena.get_battle(battle_id)
    if battle:
        return post_engine.queue_post(battle_id, battle.to_dict())
    raise HTTPException(status_code=404, detail="Battle not found")
