"""OAuth state storage (Redis with in-memory fallback)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from careerpilot.redis_client import get_redis

logger = logging.getLogger(__name__)

_MEMORY: dict[str, tuple[float, str]] = {}


def _key(state: str) -> str:
    return f"oauth:state:{state}"


async def save_oauth_state(state: str, payload: dict[str, Any], *, ttl_seconds: int = 600) -> None:
    encoded = json.dumps(payload)
    client = await get_redis()
    if client is not None:
        try:
            await client.set(_key(state), encoded, ex=ttl_seconds)
            return
        except Exception:
            logger.warning("Failed to persist OAuth state in Redis", exc_info=True)
    _MEMORY[state] = (time.time() + ttl_seconds, encoded)


async def pop_oauth_state(state: str) -> dict[str, Any] | None:
    client = await get_redis()
    raw: str | None = None
    if client is not None:
        try:
            raw = await client.get(_key(state))
            if raw:
                await client.delete(_key(state))
        except Exception:
            logger.warning("Failed to read OAuth state from Redis", exc_info=True)
            raw = None

    if raw is None:
        entry = _MEMORY.pop(state, None)
        if entry is None:
            return None
        expires_at, encoded = entry
        if time.time() > expires_at:
            return None
        raw = encoded

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
