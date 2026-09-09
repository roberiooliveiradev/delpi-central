"""Coerção determinística de argumentos ao schema OpenAPI (datas ISO quando format=date)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService
from app.domain.services.chat_reference_clock import ChatReferenceClock


class ChatOpenApiArgumentCoercionService:
    _START_NAMES = frozenset({"start_date", "date_start", "startDate", "start"})
    _END_NAMES = frozenset({"end_date", "date_end", "endDate", "end"})

    @classmethod
    def coerce_parameters(
        cls,
        parameters: dict[str, Any],
        schema_params: list[dict[str, Any]],
        *,
        message: str,
        previous_messages: list | None = None,
        execution_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        out = dict(parameters or {})
        date_params = [
            item
            for item in schema_params
            if isinstance(item, dict)
            and str((item.get("schema") or {}).get("format") or "").strip().lower() == "date"
            and str(item.get("name") or "").strip()
        ]
        if not date_params:
            return out

        today = ChatReferenceClock.today(execution_context)
        specific = ChatDateRangeIntentService.resolve_explicit_calendar_period(
            message,
            today=today,
        )
        grounded = specific or ChatDateRangeIntentService.resolve(
            message,
            today=today,
            previous_messages=previous_messages,
        )
        grounded_start = (
            ChatDateRangeIntentService.parse_api_date(grounded.start_date) if grounded else None
        )
        grounded_end = (
            ChatDateRangeIntentService.parse_api_date(grounded.end_date) if grounded else None
        )
        prefer_message_calendar = specific is not None

        for parameter in date_params:
            name = str(parameter.get("name") or "").strip()
            current = out.get(name)
            parsed = ChatDateRangeIntentService.parse_api_date(
                str(current) if current is not None else ""
            )
            if (
                prefer_message_calendar
                and grounded_start is not None
                and name in cls._START_NAMES
            ):
                out[name] = grounded_start.strftime("%Y-%m-%d")
                continue
            if (
                prefer_message_calendar
                and grounded_end is not None
                and name in cls._END_NAMES
            ):
                out[name] = grounded_end.strftime("%Y-%m-%d")
                continue
            if parsed is not None:
                out[name] = parsed.strftime("%Y-%m-%d")
                continue
            if grounded_start is not None and name in cls._START_NAMES:
                out[name] = grounded_start.strftime("%Y-%m-%d")
            elif grounded_end is not None and name in cls._END_NAMES:
                out[name] = grounded_end.strftime("%Y-%m-%d")
            elif grounded_start is not None and name not in cls._END_NAMES:
                out[name] = grounded_start.strftime("%Y-%m-%d")
        return out
