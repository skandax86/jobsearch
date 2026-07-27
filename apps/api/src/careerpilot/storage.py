"""Object storage client (MinIO / S3-compatible)."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from careerpilot.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_minio_client() -> Minio:
    parsed = urlparse(settings.storage_endpoint)
    host = parsed.netloc or parsed.path
    secure = parsed.scheme == "https"
    return Minio(
        host,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        secure=secure,
        region=settings.storage_region,
    )


async def ensure_bucket() -> None:
    client = get_minio_client()

    def _ensure() -> None:
        if not client.bucket_exists(settings.storage_bucket):
            client.make_bucket(settings.storage_bucket, location=settings.storage_region)
            logger.info("Created storage bucket %s", settings.storage_bucket)

    await asyncio.to_thread(_ensure)


async def put_object(
    *,
    object_key: str,
    data: bytes,
    content_type: str,
) -> None:
    from io import BytesIO

    client = get_minio_client()

    def _put() -> None:
        client.put_object(
            settings.storage_bucket,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    await asyncio.to_thread(_put)


async def get_object(object_key: str) -> bytes:
    client = get_minio_client()

    def _get() -> bytes:
        response = client.get_object(settings.storage_bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    return await asyncio.to_thread(_get)


async def delete_object(object_key: str) -> None:
    client = get_minio_client()

    def _delete() -> None:
        try:
            client.remove_object(settings.storage_bucket, object_key)
        except S3Error:
            logger.warning("Failed to delete object %s", object_key, exc_info=True)

    await asyncio.to_thread(_delete)
