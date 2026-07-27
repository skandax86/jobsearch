from fastapi import APIRouter

from careerpilot.api.v1.agents import router as agents_router
from careerpilot.api.v1.auth import router as auth_router
from careerpilot.api.v1.health import router as health_router
from careerpilot.api.v1.integrations import router as integrations_router
from careerpilot.api.v1.jobs import router as jobs_router
from careerpilot.api.v1.linkedin_auth import router as linkedin_auth_router
from careerpilot.api.v1.matches import router as matches_router
from careerpilot.api.v1.me import router as me_router
from careerpilot.api.v1.resumes import router as resumes_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router)
api_v1_router.include_router(linkedin_auth_router)
api_v1_router.include_router(me_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(matches_router)
api_v1_router.include_router(integrations_router)
api_v1_router.include_router(agents_router)
