from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ResolveInteractionRoomBody(BaseModel):
    kind: str = Field(..., min_length=1)
    entity_type: str | None = None
    entity_key: str | None = None
    group_id: UUID | None = None
    title: str | None = None
