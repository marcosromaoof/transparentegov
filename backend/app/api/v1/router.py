from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes_admin import router as admin_router
from app.api.v1.routes_analysis import router as analysis_router
from app.api.v1.routes_collectors import router as collectors_router
from app.api.v1.routes_entities import router as entities_router
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_investigations import router as investigations_router
from app.api.v1.routes_politicians import router as politicians_router
from app.api.v1.routes_reports import router as reports_router
from app.api.v1.routes_territory import router as territory_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(territory_router)
api_router.include_router(investigations_router)
api_router.include_router(entities_router)
api_router.include_router(politicians_router)
api_router.include_router(admin_router)
api_router.include_router(collectors_router)
api_router.include_router(analysis_router)
api_router.include_router(reports_router)

