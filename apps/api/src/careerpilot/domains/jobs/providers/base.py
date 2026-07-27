"""Job discovery providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DiscoveredJob:
    provider: str
    external_id: str
    title: str
    company_name: str
    description: str | None = None
    location: str | None = None
    remote_type: str | None = None
    canonical_url: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None
    compensation: dict[str, Any] | None = None
    requirements: dict[str, Any] | None = None
    company_website: str | None = None
    company_industry: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
