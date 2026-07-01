from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ParticipantInput:
    full_name: str
    company_name: str
    visit_date: date
    participant_info: str | None = None
    thank_you_message: str | None = None


@dataclass(frozen=True)
class ParticipantUpdate:
    full_name: str | None = None
    company_name: str | None = None
    visit_date: date | None = None
    participant_info: str | None = None
    thank_you_message: str | None = None
