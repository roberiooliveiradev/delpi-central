from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class RequestAttachment:
    id: UUID | str
    request_id: UUID | str
    original_name: str
    stored_name: str
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    created_by_user_id: str
    created_by_name: str
    created_at: datetime | None = None


@dataclass(slots=True)
class RequestArtifact:
    id: UUID | str
    request_id: UUID | str
    artifact_kind: str
    original_name: str
    stored_name: str
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    produced_by_user_id: str
    produced_by_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(slots=True)
class RequestEvent:
    id: UUID | str
    request_id: UUID | str
    event_type: str
    actor_user_id: str | None = None
    actor_name: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(slots=True)
class RequestComment:
    id: UUID | str
    request_id: UUID | str
    author_user_id: str
    author_name: str
    body: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
