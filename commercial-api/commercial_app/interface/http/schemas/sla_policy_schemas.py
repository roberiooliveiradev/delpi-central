from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SlaAppliesTo = Literal["task", "sample", "order_confirmation", "offer_stage"]


class CreateSlaPolicyBody(BaseModel):
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    appliesTo: SlaAppliesTo
    durationHours: int = Field(..., gt=0)
    calendarCode: str | None = None
    active: bool = True


class UpdateSlaPolicyBody(BaseModel):
    code: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    appliesTo: SlaAppliesTo | None = None
    durationHours: int | None = Field(default=None, gt=0)
    calendarCode: str | None = None
    active: bool | None = None
