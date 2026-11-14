from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SatisfactionCampaign:
    id: str
    name: str
    starts_at: datetime
    ends_at: datetime
    questionnaire_version: str
    invite_subject: str
    invite_body: str
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime
    version: int
    recipient_count: int = 0
    response_count: int = 0

    def window_status(self, *, now: datetime) -> str:
        if now < self.starts_at:
            return "scheduled"
        if now >= self.ends_at:
            return "closed"
        return "open"


@dataclass(frozen=True)
class SatisfactionRecipient:
    id: str
    campaign_id: str
    customer_code: str
    customer_store: str
    customer_name_snapshot: str | None
    contact_name: str | None
    contact_email: str | None
    token_hash: str
    token_ciphertext: str
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime
    version: int
    has_response: bool = False
    response_id: str | None = None
    submitted_at: datetime | None = None


@dataclass(frozen=True)
class SatisfactionResponse:
    id: str
    recipient_id: str
    overall_score: int
    recommendation_score: int
    dimensions: dict[str, int | None]
    strengths: str | None
    improvements: str | None
    unmet_needs: str | None
    questionnaire_version: str
    submitted_at: datetime


@dataclass
class RecipientAddItem:
    customer_code: str
    customer_store: str
    customer_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None


@dataclass
class RecipientAddResult:
    included: list[SatisfactionRecipient] = field(default_factory=list)
    already_existing: list[SatisfactionRecipient] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)
