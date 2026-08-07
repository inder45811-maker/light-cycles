from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    import sqlite3
    from pathlib import Path
    from api_resolver import get_free_api_status

    db_path = Path(__file__).parent.parent / "light_cycles.db"
    db_ok = False
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    # Check which free APIs are available
    free_apis = get_free_api_status()
    has_free_api = any(a["configured"] for a in free_apis)
    has_paid_api = bool(__import__("os").getenv("DEEPSEEK_API_KEY") or __import__("os").getenv("OPENAI_API_KEY"))

    return {
        "status": "healthy" if db_ok else "degraded",
        "name": "Light Cycles",
        "version": "1.3.0",
        "database": "connected" if db_ok else "disconnected",
        "ai_mode": "paid" if has_paid_api else "free" if has_free_api else "mock",
        "free_apis": free_apis,
    }
