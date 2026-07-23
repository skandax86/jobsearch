from fastapi import APIRouter

from careerpilot.api.v1.health import router as health_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
