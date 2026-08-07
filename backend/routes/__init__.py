from .battles import router as battles_router
from .tournaments import router as tournaments_router
from .debates import router as debates_router
from .pits import router as pits_router
from .auth import router as auth_router
from .promo import router as promo_router
from .edu_routes import router as edu_router
from .seo import router as seo_router
from .agent_routes import router as agent_router
from .health import router as health_router
from .websocket import router as websocket_router

__all__ = ["battles_router", "tournaments_router", "debates_router", "pits_router", "auth_router", "promo_router", "edu_router", "seo_router", "agent_router", "health_router", "websocket_router"]
