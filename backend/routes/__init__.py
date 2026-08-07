from .battles import router as battles_router
from .tournaments import router as tournaments_router
from .debates import router as debates_router
from .health import router as health_router
from .websocket import router as websocket_router

__all__ = ["battles_router", "tournaments_router", "debates_router", "health_router", "websocket_router"]
