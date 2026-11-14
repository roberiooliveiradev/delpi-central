from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateCampaignBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    starts_at: datetime
    ends_at: datetime
    invite_subject: str | None = Field(default=None, max_length=300)
    invite_body: str | None = Field(default=None, max_length=20000)


class UpdateCampaignBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    invite_subject: str | None = Field(default=None, max_length=300)
    invite_body: str | None = Field(default=None, max_length=20000)


class RecipientAddItemBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_code: str = Field(min_length=1, max_length=40)
    customer_store: str = Field(min_length=1, max_length=20)
    customer_name: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=200)
    contact_email: str | None = Field(default=None, max_length=320)


class AddRecipientsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecipientAddItemBody] = Field(min_length=1, max_length=100)


class UpdateRecipientContactBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    contact_name: str | None = Field(default=None, max_length=200)
    contact_email: str | None = Field(default=None, max_length=320)


class PublicResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(ge=1, le=5)
    recommendation_score: int = Field(ge=0, le=10)
    dimensions: dict[str, Any]
    strengths: str | None = Field(default=None, max_length=5000)
    improvements: str | None = Field(default=None, max_length=5000)
    unmet_needs: str | None = Field(default=None, max_length=5000)
