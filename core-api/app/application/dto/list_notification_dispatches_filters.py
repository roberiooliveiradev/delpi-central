# app/application/dto/list_notification_dispatches_filters.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

RevokedFilter = Literal["all", "active", "revoked"]


@dataclass(frozen=True)
class ListNotificationDispatchesFilters:
    status: str | None = None
    category: str | None = None
    source_app: str | None = None
    search: str | None = None
    revoked: RevokedFilter = "all"
    date_from: datetime | None = None
    date_to: datetime | None = None
