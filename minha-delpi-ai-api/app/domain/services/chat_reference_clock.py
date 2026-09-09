"""Relógio injetável para períodos — evals declaram referenceDate."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService


class ChatReferenceClock:
    @classmethod
    def today(cls, execution_context: dict[str, Any] | None = None) -> date:
        if isinstance(execution_context, dict):
            raw = execution_context.get("referenceDate") or execution_context.get("today")
            parsed = ChatDateRangeIntentService.parse_api_date(str(raw or "") if raw is not None else "")
            if parsed is not None:
                return parsed
            if isinstance(raw, date) and not isinstance(raw, bool):
                return raw
        return date.today()
