import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import careerpilot.db.models  # noqa: F401 — register all ORM mappers
from careerpilot import __version__
from careerpilot.api.v1.router import api_v1_router
from careerpilot.config import settings

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info("Starting %s v%s (%s)", settings.app_name, __version__, settings.app_env)
    from careerpilot.storage import ensure_bucket

    try:
        await ensure_bucket()
    except Exception:
        logger.exception("Failed to ensure object storage bucket; uploads may fail")
    yield
    from careerpilot.redis_client import close_redis

    await close_redis()
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI-native Career Operating System API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
