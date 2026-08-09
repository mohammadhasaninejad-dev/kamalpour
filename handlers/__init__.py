from .start import router as start_router
from .search import router as search_router
from .admin import router as admin_router

__all__ = ["start_router", "search_router", "admin_router"]