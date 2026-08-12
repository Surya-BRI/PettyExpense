from api.routes_admin import router as admin_router
from api.routes_auth import router as auth_router
from api.routes_claims import router as claims_router
from api.routes_projects import router as projects_router

__all__ = ["admin_router", "auth_router", "claims_router", "projects_router"]
