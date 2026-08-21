from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ResolveInteractionRoomBody(BaseModel):
    kind: str = Field(..., min_length=1)
    entity_type: str | None = None
    entity_key: str | None = None
    group_id: UUID | None = None
    title: str | None = None


class AddInteractionRoomMemberBody(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: str = "member"


class PostInteractionMessageBody(BaseModel):
    body_text: str = ""
    message_kind: str = "text"
    parent_id: UUID | None = None
    mentions: list[dict] | None = None


class UpdateInteractionMessageBody(BaseModel):
    body_text: str = ""
    # When set (incl. empty list), replaces all mentions; omit to leave unchanged.
    mentions: list[dict] | None = None


class CreateTaskFromInteractionMessageBody(BaseModel):
    """Título vem do body_text da mensagem; assignee default = actor."""

    description: str | None = None


class RenameInteractionRoomBody(BaseModel):
    title: str = Field(..., min_length=1)
