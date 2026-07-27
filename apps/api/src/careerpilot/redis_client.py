"""Optional Redis cache for session lookups."""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis

from careerpilot.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


async def get_redis() -> Redis | None:
    global _redis
    if not settings.session_cache_enabled:
        return None
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def _session_key(token_hash: str) -> str:
    return f"session:{token_hash}"


async def cache_session(
    token_hash: str,
    *,
    user_id: str,
    session_id: str,
    ttl_seconds: int,
) -> None:
    client = await get_redis()
    if client is None:
        return
    payload = json.dumps({"user_id": user_id, "session_id": session_id})
    try:
        await client.set(_session_key(token_hash), payload, ex=ttl_seconds)
    except Exception:
        logger.warning("Failed to cache session", exc_info=True)


async def get_cached_session(token_hash: str) -> dict[str, Any] | None:
    client = await get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(_session_key(token_hash))
    except Exception:
        logger.warning("Failed to read session cache", exc_info=True)
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


async def invalidate_cached_session(token_hash: str) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        await client.delete(_session_key(token_hash))
    except Exception:
        logger.warning("Failed to invalidate session cache", exc_info=True)
