from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ContactChannel = Literal["phone", "mobile", "email", "whatsapp", "other"]


class CreateAccountContactBody(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    role_title: str | None = Field(default=None, max_length=255)
    channel: ContactChannel
    email: str | None = Field(default=None, max_length=320)
    phone_e164: str | None = Field(default=None, max_length=17)
    is_whatsapp: bool = False
    is_primary: bool = False
    source: str = Field(default="manual", min_length=1, max_length=100)


class UpdateAccountContactBody(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    role_title: str | None = Field(default=None, max_length=255)
    channel: ContactChannel | None = None
    email: str | None = Field(default=None, max_length=320)
    phone_e164: str | None = Field(default=None, max_length=17)
    is_whatsapp: bool | None = None
    is_primary: bool | None = None
    source: str | None = Field(default=None, max_length=100)
