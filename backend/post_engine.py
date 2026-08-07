"""
Auto-Post Engine — detects completed battles and queues social media posts.
Posts to Twitter/X and Reddit when API keys are configured.
"""

import time
import json
import secrets
import sqlite3
from pathlib import Path

from promo_engine import generate_all, battle_to_result, BattleResult

DB_PATH = Path(__file__).parent / "light_cycles.db"


def get_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    return db


def init_post_queue():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS post_queue (
            id TEXT PRIMARY KEY,
            battle_id TEXT,
            title TEXT NOT NULL,
            mode TEXT NOT NULL,
            winner TEXT NOT NULL,
            loser TEXT,
            posts_json TEXT NOT NULL,
            status TEXT DEFAULT 'pending',  -- pending, approved, posted
            posted_to TEXT DEFAULT '',       -- comma-sep: twitter,reddit
            created_at REAL NOT NULL,
            approved_at REAL,
            posted_at REAL
        );
    """)
    db.commit()
    db.close()


def queue_post(battle_id: str, battle_data: dict) -> dict:
    """Generate posts and add to queue."""
    result = battle_to_result(battle_data)
    posts = generate_all(result)

    db = get_db()
    pid = f"post-{secrets.token_hex(6)}"
    db.execute("""
        INSERT INTO post_queue (id, battle_id, title, mode, winner, loser, posts_json, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'approved', ?)
    """, (pid, battle_id, result.title, result.mode, result.winner,
          result.loser or '', json.dumps(posts), time.time()))
    db.commit()
    db.close()
    return {"id": pid, "title": result.title, "mode": result.mode,
            "winner": result.winner, "posts": posts}


def get_pending_posts(limit: int = 20) -> list[dict]:
    """Get posts waiting for review."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM post_queue ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    result = []
    for row in rows:
        r = dict(row)
        r["posts"] = json.loads(r["posts_json"])
        result.append(r)
    db.close()
    return result


def mark_posted(post_id: str, platform: str) -> bool:
    """Mark a post as posted to a platform."""
    db = get_db()
    post = db.execute("SELECT * FROM post_queue WHERE id = ?", (post_id,)).fetchone()
    if not post:
        db.close()
        return False

    current = post["posted_to"].split(",") if post["posted_to"] else []
    if platform not in current:
        current.append(platform)

    db.execute(
        "UPDATE post_queue SET posted_to = ?, posted_at = ?, status = 'posted' WHERE id = ?",
        (",".join(current), time.time(), post_id)
    )
    db.commit()
    db.close()
    return True


def delete_post(post_id: str) -> bool:
    db = get_db()
    db.execute("DELETE FROM post_queue WHERE id = ?", (post_id,))
    db.commit()
    db.close()
    return True


def get_post_count() -> dict:
    """Get queue stats."""
    db = get_db()
    pending = db.execute("SELECT COUNT(*) FROM post_queue WHERE status = 'pending'").fetchone()[0]
    approved = db.execute("SELECT COUNT(*) FROM post_queue WHERE status = 'approved'").fetchone()[0]
    posted = db.execute("SELECT COUNT(*) FROM post_queue WHERE status = 'posted'").fetchone()[0]
    db.close()
    return {"pending": pending, "approved": approved, "posted": posted}


# ── Auto-post watcher ──────────────────────────────────────────────

_completed_battle_ids = set()


def check_and_queue(app_state) -> list[dict]:
    """
    Check all arenas for newly completed battles and queue posts.
    Call this from the WebSocket event loop or a cron job.
    """
    new_posts = []
    arena = app_state.get("arena")
    tournaments = app_state.get("tournaments")
    pit_arena_module = app_state.get("pits")
    debate_arena_module = app_state.get("debates")

    if arena:
        for battle in arena.battles.values():
            if battle.status.value == "complete" and battle.id not in _completed_battle_ids:
                _completed_battle_ids.add(battle.id)
                data = battle.to_dict()
                data["title"] = getattr(battle, "title", "Battle")
                new_posts.append(queue_post(battle.id, data))

    if tournaments:
        for t in tournaments.tournaments.values():
            if hasattr(t, 'status') and t.status.value == "complete" and t.id not in _completed_battle_ids:
                _completed_battle_ids.add(t.id)
                new_posts.append(queue_post(t.id, t.to_dict()))

    return new_posts


# Initialize on import
init_post_queue()
