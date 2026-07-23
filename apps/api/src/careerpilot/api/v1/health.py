from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from careerpilot import __version__
from careerpilot.config import settings

router = APIRouter()


class HealthData(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthResponse(BaseModel):
    data: HealthData
    metadata: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        data=HealthData(
            status="ok",
            version=__version__,
            environment=settings.app_env,
        )
    )
