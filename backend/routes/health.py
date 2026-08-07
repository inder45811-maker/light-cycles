from fastapi import APIRouter
from api_resolver import get_free_api_status, get_api_config
import os, time, sqlite3, psutil
from pathlib import Path

router = APIRouter(tags=["health"])

START_TIME = time.time()


@router.get("/api/health")
async def health():
    import os as _os
    db_path = Path(__file__).parent.parent / "light_cycles.db"
    db_ok = False
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    free_apis = get_free_api_status()
    has_free_api = any(a["configured"] for a in free_apis)
    has_paid = bool(_os.getenv("DEEPSEEK_API_KEY") or _os.getenv("OPENAI_API_KEY"))
    config = get_api_config()

    uptime = int(time.time() - START_TIME)
    mem = psutil.Process().memory_info().rss / 1024 / 1024

    return {
        "status": "healthy" if db_ok else "degraded",
        "name": "Light Cycles",
        "version": "2.0.0",
        "production": _os.getenv("RENDER", "") == "1" or _os.getenv("PRODUCTION", "") == "1",
        "database": "connected" if db_ok else "disconnected",
        "ai_mode": "paid" if has_paid else "free" if has_free_api else "mock",
        "ai_provider": config["provider"],
        "uptime_seconds": uptime,
        "memory_mb": round(mem, 1),
        "free_apis": free_apis,
    }


@router.get("/api/health/live")
async def liveness():
    """Kubernetes liveness probe — just returns 200."""
    return {"status": "alive"}


@router.get("/api/health/ready")
async def readiness():
    """Kubernetes readiness probe — checks DB connectivity."""
    try:
        db_path = Path(__file__).parent.parent / "light_cycles.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
