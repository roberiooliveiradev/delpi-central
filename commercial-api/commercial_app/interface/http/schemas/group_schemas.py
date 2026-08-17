from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCommercialGroupBody(BaseModel):
    name: str = Field(..., min_length=1)
    kind: str | None = Field(
        default=None,
        description="Identificador técnico opcional; se omitido, deriva do nome.",
    )
    sort_order: int = Field(default=0)
    active: bool = Field(default=True)


class RenameCommercialGroupBody(BaseModel):
    name: str = Field(..., min_length=1, description="Novo nome de exibição; kind permanece imutável.")


class ReplaceGroupMembersBody(BaseModel):
    user_ids: list[str] = Field(default_factory=list)


class AddGroupMemberBody(BaseModel):
    user_id: str = Field(..., min_length=1)
