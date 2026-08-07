"""
Agent System — users can create custom agents with their own configs.
Agents can be private, shared with a class, or published to the marketplace.
"""

import time
import secrets
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "light_cycles.db"


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_agents_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            personality TEXT DEFAULT 'balanced',  -- aggressive, balanced, conservative, creative
            mode TEXT DEFAULT 'ai',               -- ai, webhook, mock
            webhook_url TEXT,
            api_key TEXT,
            api_provider TEXT DEFAULT 'gemini',
            model TEXT DEFAULT 'gemini-2.0-flash',
            custom_prompt TEXT,
            is_public INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            win_count INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL
        );

        CREATE TABLE IF NOT EXISTS agent_stats (
            agent_id TEXT PRIMARY KEY REFERENCES agents(id),
            battles INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            tournaments INTEGER DEFAULT 0,
            tournament_wins INTEGER DEFAULT 0,
            pits INTEGER DEFAULT 0,
            pit_wins INTEGER DEFAULT 0,
            debates INTEGER DEFAULT 0,
            debate_wins INTEGER DEFAULT 0,
            total_earnings_cents INTEGER DEFAULT 0
        );
    """)
    db.commit()
    db.close()


# ── Agent CRUD ──────────────────────────────────────────────────────

def create_agent(owner_id: str, name: str, description: str = "", personality: str = "balanced",
                 mode: str = "ai", webhook_url: str = "", api_provider: str = "gemini",
                 model: str = "gemini-2.0-flash", custom_prompt: str = "",
                 is_public: bool = False) -> dict:
    db = get_db()
    agent_id = f"agent-{secrets.token_hex(6)}"

    db.execute("""
        INSERT INTO agents (id, owner_id, name, description, personality, mode,
            webhook_url, api_provider, model, custom_prompt, is_public, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (agent_id, owner_id, name, description, personality, mode,
          webhook_url, api_provider, model, custom_prompt, int(is_public), time.time()))

    # Init stats
    db.execute("INSERT INTO agent_stats (agent_id) VALUES (?)", (agent_id,))
    db.commit()
    db.close()
    return get_agent(agent_id)


def get_agent(agent_id: str) -> dict | None:
    db = get_db()
    agent = db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not agent:
        db.close()
        return None
    stats = db.execute("SELECT * FROM agent_stats WHERE agent_id = ?", (agent_id,)).fetchone()
    db.close()
    result = dict(agent)
    result["stats"] = dict(stats) if stats else {}
    return result


def update_agent(agent_id: str, **kwargs) -> dict | None:
    db = get_db()
    agent = db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not agent:
        db.close()
        return None

    allowed = ["name", "description", "personality", "mode", "webhook_url",
               "api_provider", "model", "custom_prompt", "is_public"]
    updates = {k: kwargs[k] for k in allowed if k in kwargs}
    if updates:
        updates["updated_at"] = time.time()
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE agents SET {sets} WHERE id = ?", (*updates.values(), agent_id))
    db.commit()
    db.close()
    return get_agent(agent_id)


def delete_agent(agent_id: str) -> bool:
    db = get_db()
    db.execute("DELETE FROM agent_stats WHERE agent_id = ?", (agent_id,))
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    db.commit()
    db.close()
    return True


def list_user_agents(owner_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM agents WHERE owner_id = ? ORDER BY created_at DESC",
        (owner_id,)
    ).fetchall()
    result = []
    for row in rows:
        agent = dict(row)
        stats = db.execute("SELECT * FROM agent_stats WHERE agent_id = ?", (row["id"],)).fetchone()
        agent["stats"] = dict(stats) if stats else {}
        result.append(agent)
    db.close()
    return result


def list_public_agents(limit: int = 50) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM agents WHERE is_public = 1 ORDER BY usage_count DESC LIMIT ?",
        (limit,)
    ).fetchall()
    result = []
    for row in rows:
        agent = dict(row)
        stats = db.execute("SELECT * FROM agent_stats WHERE agent_id = ?", (row["id"],)).fetchone()
        agent["stats"] = dict(stats) if stats else {}
        result.append(agent)
    db.close()
    return result


def increment_agent_stat(agent_id: str, stat: str, count: int = 1):
    """Increment a stat for an agent (battles, wins, etc)."""
    valid_stats = ["battles", "wins", "tournaments", "tournament_wins",
                   "pits", "pit_wins", "debates", "debate_wins"]
    if stat not in valid_stats:
        return

    db = get_db()
    db.execute(f"UPDATE agent_stats SET {stat} = {stat} + ? WHERE agent_id = ?", (count, agent_id))
    db.execute("UPDATE agents SET usage_count = usage_count + ? WHERE id = ?", (count, agent_id))
    if "win" in stat:
        db.execute("UPDATE agents SET win_count = win_count + ? WHERE id = ?", (count, agent_id))
    db.commit()
    db.close()


# ── Agent Runner ────────────────────────────────────────────────────

def run_agent(agent_id: str, competition_type: str, problem: str, test_cases: list = None,
              market_state: dict = None, opponent_argument: str = "") -> str:
    """
    Run a custom agent for a competition.
    Returns the agent's response (code, trade decision, or argument).
    """
    agent = get_agent(agent_id)
    if not agent:
        return "Agent not found"

    if agent["mode"] == "webhook" and agent["webhook_url"]:
        return _call_webhook(agent, competition_type, problem, test_cases, market_state, opponent_argument)

    if agent["mode"] == "mock":
        return _run_mock_agent(agent, competition_type, problem)

    # AI mode — use the agent's configured API
    return _call_ai_agent(agent, competition_type, problem, test_cases, market_state, opponent_argument)


def _call_webhook(agent: dict, comp_type: str, problem: str, test_cases=None,
                  market_state=None, opponent=None) -> str:
    """Call an external webhook for agent decisions."""
    import urllib.request

    payload = json.dumps({
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "competition_type": comp_type,
        "problem": problem,
        "test_cases": test_cases,
        "market_state": market_state,
        "opponent_argument": opponent,
    }).encode()

    try:
        req = urllib.request.Request(agent["webhook_url"], data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return resp.get("response", resp.get("code", str(resp)))
    except Exception as e:
        return f"Webhook error: {e}"


def _run_mock_agent(agent: dict, comp_type: str, problem: str) -> str:
    """Run a mock agent with the configured personality."""
    if comp_type == "code":
        return f"# {agent['name']} — {agent['personality']} strategy\ndef solution(x):\n    return x * 2  # placeholder"
    elif comp_type == "trade":
        return json.dumps({"action": "hold", "amount": 0, "reasoning": f"{agent['name']} observes the market"})
    else:
        return f"As {agent['name']}, I believe the evidence speaks for itself."


def _call_ai_agent(agent: dict, comp_type: str, problem: str, test_cases=None,
                   market_state=None, opponent=None) -> str:
    """Call AI for an agent using its configured provider."""
    from api_resolver import call_llm

    personality_prompts = {
        "aggressive": "You are bold and take risks. Act decisively.",
        "balanced": "You are measured and analytical. Weigh options carefully.",
        "conservative": "You are cautious and defensive. Prioritize safety.",
        "creative": "You think outside the box. Use unconventional approaches.",
    }

    persona = personality_prompts.get(agent.get("personality", "balanced"), "")

    if comp_type == "code":
        system = f"""You are {agent['name']}. {persona}
{custom_prompt}

Write ONLY valid Python code that solves this problem. Output nothing but the code."""
        
        tc_str = "\n".join(f"  {tc['name']}: input={tc['input']} → expected={tc['expected']}"
                          for tc in (test_cases or []))
        user = f"PROBLEM:\n{problem}\n\nTEST CASES:\n{tc_str}\n\nYour code:"

    elif comp_type == "trade":
        system = f"""You are {agent['name']}, an AI trader. {persona}
{custom_prompt}

Respond with ONLY a JSON object: {{"action": "buy"|"sell"|"hold", "amount": number, "reasoning": "one sentence"}}"""

        user = f"Market: {json.dumps(market_state or {})}\nProblem: {problem}\nYour decision:"

    else:  # debate
        system = f"""You are {agent['name']}, a debater. {persona}
{custom_prompt}

Write a compelling argument. 150-250 words."""

        user = f"Topic: {problem}\nYour position: {problem}\nOpponent: {opponent or ''}\nYour argument:"

    try:
        custom_prompt = agent.get("custom_prompt", "")
        if custom_prompt:
            system = system.replace("{custom_prompt}", f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}")
        else:
            system = system.replace("{custom_prompt}\n\n", "").replace("{custom_prompt}", "")

        return call_llm(system, user, model_override=agent.get("model"))
    except Exception:
        return _run_mock_agent(agent, comp_type, problem)


# Initialize on import
init_agents_db()
