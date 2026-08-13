from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCommercialGroupBody(BaseModel):
    kind: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    sort_order: int = Field(default=0)
    active: bool = Field(default=True)


class ReplaceGroupMembersBody(BaseModel):
    user_ids: list[str] = Field(default_factory=list)


class AddGroupMemberBody(BaseModel):
    user_id: str = Field(..., min_length=1)
