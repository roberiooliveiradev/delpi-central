"""Respostas diretas para perguntas utilitárias (hora, data) — sem LLM."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


@lru_cache(maxsize=1)
def _utility_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("utility_answers")


class ChatUtilityDirectAnswerService:
    @classmethod
    def is_utility_question(cls, message: str) -> bool:
        return cls.classify(message) is not None

    @classmethod
    def classify(cls, message: str) -> str | None:
        if not ChatDomainConfigService.chat_utility_direct_enabled():
            return None

        text = str(message or "").strip()

        if not text:
            return None

        content = _utility_content()
        max_length = int(content.get("maxMessageLength") or 80)

        if len(text) > max_length:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(text) or ""
        normalized = " ".join(normalized.split())

        if not normalized:
            return None

        exclusions = tuple(str(item) for item in (content.get("exclusions") or ()))

        if ChatMessageNormalizationService.contains_any(normalized, exclusions):
            return None

        patterns = content.get("patterns") or {}
        priority = content.get("categoryPriority") or list(patterns.keys())

        for category in priority:
            for pattern in patterns.get(category) or ():
                if cls._matches_pattern(normalized, str(pattern)):
                    return str(category)

        return None

    @classmethod
    def build_direct_answer(
        cls,
        *,
        message: str,
        now: datetime | None = None,
    ) -> str | None:
        category = cls.classify(message)

        if not category:
            return None

        content = _utility_content()
        template = str((content.get("responses") or {}).get(category) or "").strip()

        if not template:
            return None

        localized = now or cls._now()
        offset_days = int((content.get("dayOffsets") or {}).get(category) or 0)
        target = localized + timedelta(days=offset_days)
        weekday = ExternalActionResponseContentService.weekday_label(target.weekday())
        timezone_label = str(content.get("timezoneLabel") or "horário local").strip()
        month_names = content.get("monthNames") or []
        month_name = (
            str(month_names[target.month - 1])
            if isinstance(month_names, list)
            and len(month_names) >= target.month
            else str(target.month)
        )
        quarter = (target.month - 1) // 3 + 1
        is_weekend = target.weekday() >= 5
        day_notes = content.get("dayNotes") or {}

        values = {
            "time": localized.strftime("%H:%M"),
            "date": target.strftime("%d/%m/%Y"),
            "weekday": weekday,
            "year": str(target.year),
            "month": month_name,
            "quarter": str(quarter),
            "week_number": str(target.isocalendar()[1]),
            "iso_date": target.strftime("%Y-%m-%d"),
            "iso_datetime": localized.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone_label": timezone_label,
            "weekend_note": (
                str(day_notes.get("weekend") or "")
                if is_weekend
                else str(day_notes.get("weekdayUtility") or "")
            ),
            "business_day_note": (
                str(day_notes.get("businessDay") or "")
                if not is_weekend
                else str(day_notes.get("notBusinessDay") or "")
            ),
        }

        try:
            return template.format(**values).strip()
        except KeyError:
            return None

    @classmethod
    def _now(cls) -> datetime:
        timezone_name = ChatDomainConfigService.chat_utility_timezone()

        try:
            return datetime.now(ZoneInfo(timezone_name))
        except Exception:
            return datetime.now(ZoneInfo("America/Sao_Paulo"))

    @classmethod
    def _matches_pattern(cls, normalized: str, pattern: str) -> bool:
        candidate = ChatMessageNormalizationService.normalize_for_matching(pattern) or pattern
        candidate = " ".join(candidate.split())

        if not candidate:
            return False

        if normalized == candidate:
            return True

        if normalized.startswith(f"{candidate} "):
            return True

        trailing = re.sub(r"[\s!?.,:;]+$", "", normalized)

        return trailing == candidate
