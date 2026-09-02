from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DeviceReading:
    metrics: dict[str, Any]
    recorded_at: datetime = field(default_factory=utc_now)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    success: bool
    metrics: dict[str, Any] | None = None
    error_message: str | None = None
    error_code: str | None = None
    response_payload: dict[str, Any] = field(default_factory=dict)
