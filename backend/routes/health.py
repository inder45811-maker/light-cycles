from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent / "light_cycles.db"
    db_ok = False
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "name": "Light Cycles",
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
    }
