"""Encrypt integration credentials at rest (Fernet-compatible secret derivation)."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from careerpilot.config import settings

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover - optional until installed
    Fernet = None  # type: ignore[misc, assignment]


def _fernet() -> Any:
    if Fernet is None:
        raise RuntimeError("cryptography package is required for credential encryption")
    digest = hashlib.sha256(settings.credentials_secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return _fernet().encrypt(raw).decode("utf-8")


def decrypt_json(token: str) -> dict[str, Any]:
    raw = _fernet().decrypt(token.encode("utf-8"))
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid credential payload")
    return data
