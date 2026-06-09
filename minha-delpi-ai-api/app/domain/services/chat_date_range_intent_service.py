"""Resolve períodos em linguagem natural para parâmetros start_date/end_date (DD-MM-YYYY)."""

from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

from app.domain.services.chat_date_range_vocabulary_service import (
    ChatDateRangeVocabularyService,
)


def _contains_any(normalized: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in normalized for phrase in phrases)


@dataclass(frozen=True)
class ResolvedDateRange:
    start_date: str
    end_date: str
    reason: str


@dataclass(frozen=True)
class NamedMonth:
    month: int
    label: str
    year: int | None = None


@dataclass(frozen=True)
class AmbiguousNamedMonth:
    month: int
    month_label: str
    current_year: int
    previous_year: int


class ChatDateRangeIntentService:
    _DATE_RANGE_RE = re.compile(
        r"\bde\s+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\s+a\s+"
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        re.IGNORECASE,
    )
    _COMPETENCE_RE = re.compile(r"\bcompetencia\s+(\d{4})-(\d{1,2})\b", re.IGNORECASE)
    _YEAR_MONTH_RE = re.compile(r"\b(\d{4})-(\d{1,2})\b")
    _LAST_N_DAYS_RE = re.compile(
        r"\bultim[ao]s?\s+(\d{1,3})\s+dias?\b",
        re.IGNORECASE,
    )
    _LAST_N_WEEKS_RE = re.compile(
        r"\bultim[ao]s?\s+(\d{1,2})\s+semanas?\b",
        re.IGNORECASE,
    )
    _YEAR_ONLY_RE = re.compile(r"^\s*(\d{4})\s*$")
    @classmethod
    def _month_order(cls) -> tuple[str, ...]:
        return tuple(
            sorted(
                ChatDateRangeVocabularyService.months_pt().keys(),
                key=len,
                reverse=True,
            )
        )


    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        today: date | None = None,
        previous_messages: list[Any] | None = None,
    ) -> ResolvedDateRange | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        reference = today or date.today()

        year_follow_up = cls._resolve_year_follow_up(
            normalized,
            previous_messages,
            reference=reference,
        )

        if year_follow_up:
            return year_follow_up

        explicit = cls._parse_explicit_range(normalized)

        if explicit:
            return explicit

        from app.domain.services.chat_temporal_intent_service import (
            ChatTemporalIntentService,
        )

        week_range = cls._resolve_calendar_week_phrases(normalized, reference)
        if week_range:
            return week_range

        month_range = cls._resolve_next_month_phrases(normalized, reference)
        if month_range:
            return month_range

        quarter_range = cls._resolve_quarter_phrases(normalized, reference)
        if quarter_range:
            return quarter_range

        point = ChatTemporalIntentService.resolve_point(
            message,
            today=reference,
            default_today=False,
        )
        if point and cls._should_use_point_as_range(normalized):
            return cls._from_dates(
                point.target_date,
                point.target_date,
                reason=cls._reason("pointAsRange", label=point.label),
            )

        competence = cls._COMPETENCE_RE.search(normalized)

        if competence:
            return cls._month_range(
                int(competence.group(1)),
                int(competence.group(2)),
                reason=cls._reason("competence"),
            )

        last_weeks = cls._LAST_N_WEEKS_RE.search(normalized)

        if last_weeks:
            weeks = max(1, min(int(last_weeks.group(1)), 52))
            start = reference - timedelta(days=weeks * 7 - 1)

            return cls._from_dates(
                start,
                reference,
                reason=cls._reason("lastNWeeks", weeks=weeks),
            )

        last_days = cls._LAST_N_DAYS_RE.search(normalized)

        if last_days:
            days = max(1, min(int(last_days.group(1)), 366))
            start = reference - timedelta(days=days - 1)

            return cls._from_dates(
                start,
                reference,
                reason=cls._reason("lastNDays", days=days),
            )

        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("rollingLastWeekPhrases")):
            start = reference - timedelta(days=6)

            return cls._from_dates(start, reference, reason=cls._reason("rollingLastWeek"))

        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("previousMonthPhrases")):
            return cls._previous_month(reference, reason=cls._reason("previousMonth"))

        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("currentMonthPhrases")):
            return cls._month_range(
                reference.year,
                reference.month,
                reason=cls._reason("currentMonth"),
            )

        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("lastYearPhrases")):
            year = reference.year - 1

            return cls._from_dates(
                date(year, 1, 1),
                date(year, 12, 31),
                reason=cls._reason("lastYear"),
            )

        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("currentYearPhrases")):
            return cls._from_dates(
                date(reference.year, 1, 1),
                date(reference.year, 12, 31),
                reason=cls._reason("currentYear"),
            )

        month_match = cls._parse_named_month(normalized, reference)

        if month_match:
            return month_match

        year_month = cls._YEAR_MONTH_RE.search(normalized)

        if year_month and any(term in normalized for term in ChatDateRangeVocabularyService.terms("periodMetricTerms")):
            return cls._month_range(
                int(year_month.group(1)),
                int(year_month.group(2)),
                reason=cls._reason("yearMonthInQuestion"),
            )

        return None

    @classmethod
    def detect_ambiguous_named_month(
        cls,
        message: str | None,
        *,
        today: date | None = None,
    ) -> AmbiguousNamedMonth | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        reference = today or date.today()
        named_month = cls._extract_named_month(normalized)

        if not named_month or named_month.year is not None:
            return None

        if reference.month >= named_month.month:
            return None

        return AmbiguousNamedMonth(
            month=named_month.month,
            month_label=named_month.label,
            current_year=reference.year,
            previous_year=reference.year - 1,
        )

    @classmethod
    def build_ambiguity_clarification(
        cls,
        message: str | None,
        *,
        today: date | None = None,
    ) -> str | None:
        ambiguous = cls.detect_ambiguous_named_month(message, today=today)

        if not ambiguous:
            return None

        template = ChatAssistantContentService.get(
            "operational_parameters",
            "ambiguousPeriodYear",
            default=(
                "Para **{month_label}**, preciso confirmar o ano: "
                "você quer os dados de **{current_year}** (este ano) "
                "ou de **{previous_year}**?"
            ),
        )
        return template.format(
            month_label=ambiguous.month_label,
            current_year=ambiguous.current_year,
            previous_year=ambiguous.previous_year,
        )

    @classmethod
    def is_year_clarification_reply(
        cls,
        message: str | None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not previous_messages:
            return False

        if cls._parse_year_hint(normalized, reference=date.today()) is None:
            return False

        return cls._find_pending_ambiguous_period_question(
            previous_messages,
            reference=date.today(),
        ) is not None

    @classmethod
    def looks_like_period_metric_question(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if cls._extract_named_month(normalized):
            return True

        return any(term in normalized for term in ChatDateRangeVocabularyService.terms("periodMetricTerms"))

    @classmethod
    def _resolve_year_follow_up(
        cls,
        normalized: str,
        previous_messages: list[Any] | None,
        *,
        reference: date,
    ) -> ResolvedDateRange | None:
        if not previous_messages:
            return None

        year = cls._parse_year_hint(normalized, reference=reference)

        if year is None:
            return None

        pending = cls._find_pending_ambiguous_period_question(
            previous_messages,
            reference=reference,
        )

        if not pending:
            return None

        return cls._month_range(
            year,
            pending.month,
            reason=cls._reason("yearConfirmation", month=pending.label, year=year),
        )

    @classmethod
    def _find_pending_ambiguous_period_question(
        cls,
        previous_messages: list[Any] | None,
        *,
        reference: date | None = None,
    ) -> NamedMonth | None:
        today = reference or date.today()

        for item in reversed(previous_messages or []):
            role = cls._message_role(item)

            if role != "user":
                continue

            content = cls._message_content(item)
            normalized = ChatMessageNormalizationService.normalize_for_matching(content)

            if not normalized:
                continue

            named_month = cls._extract_named_month(normalized)

            if not named_month or named_month.year is not None:
                continue

            if today.month >= named_month.month:
                continue

            return named_month

        return None

    @classmethod
    def _parse_year_hint(cls, normalized: str, *, reference: date) -> int | None:
        if any(
            term in normalized
            for term in (
                "desse ano",
                "deste ano",
                "este ano",
                "ano atual",
                "ano corrente",
            )
        ):
            return reference.year

        if any(term in normalized for term in ("ano passado", "ultimo ano", "último ano")):
            return reference.year - 1

        year_match = cls._YEAR_ONLY_RE.match(normalized)

        if year_match:
            return int(year_match.group(1))

        if re.fullmatch(r"\d{4}", normalized.strip()):
            return int(normalized.strip())

        return None

    @classmethod
    def _extract_named_month(cls, normalized: str) -> NamedMonth | None:
        for name in cls._month_order():
            if not cls._contains_month_name(normalized, name):
                continue

            month = ChatDateRangeVocabularyService.months_pt()[name]
            label = ChatDateRangeVocabularyService.month_labels_pt().get(month, name)
            year = cls._extract_year_for_month(normalized, name)

            return NamedMonth(month=month, label=label, year=year)

        return None

    @classmethod
    def _contains_month_name(cls, normalized: str, name: str) -> bool:
        return re.search(rf"\b{re.escape(name)}\b", normalized) is not None

    @classmethod
    def _extract_year_for_month(cls, normalized: str, month_name: str) -> int | None:
        patterns = (
            rf"\b{re.escape(month_name)}\s+de\s+(\d{{4}})\b",
            rf"\bde\s+(\d{{4}})\b[^\d]{{0,24}}\b{re.escape(month_name)}\b",
            rf"\b{re.escape(month_name)}\s*/\s*(\d{{4}})\b",
            rf"\b(\d{{4}})\s*/\s*{re.escape(month_name)}\b",
        )

        for pattern in patterns:
            match = re.search(pattern, normalized)

            if match:
                return int(match.group(1))

        return None

    @classmethod
    def _parse_explicit_range(cls, normalized: str) -> ResolvedDateRange | None:
        match = cls._DATE_RANGE_RE.search(normalized)

        if not match:
            return None

        start = cls._to_date(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )
        end = cls._to_date(
            int(match.group(4)),
            int(match.group(5)),
            int(match.group(6)),
        )

        if not start or not end:
            return None

        if start > end:
            start, end = end, start

        return cls._from_dates(start, end, reason=cls._reason("explicitRange"))

    @classmethod
    def _parse_named_month(cls, normalized: str, reference: date) -> ResolvedDateRange | None:
        named_month = cls._extract_named_month(normalized)

        if not named_month:
            return None

        if named_month.year is not None:
            return cls._month_range(
                named_month.year,
                named_month.month,
                reason=cls._reason(
                    "namedMonthYear",
                    month=named_month.label,
                    year=named_month.year,
                ),
            )

        if reference.month < named_month.month:
            return None

        return cls._month_range(
            reference.year,
            named_month.month,
            reason=cls._reason(
                "namedMonthYear",
                month=named_month.label,
                year=reference.year,
            ),
        )

    @classmethod
    def _should_use_point_as_range(cls, normalized: str) -> bool:
        if any(term in normalized for term in ChatDateRangeVocabularyService.terms("periodMetricTerms")):
            return True

        return _contains_any(normalized, ChatDateRangeVocabularyService.terms("pointAsRangePhrases"))

    @classmethod
    def _resolve_calendar_week_phrases(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedDateRange | None:
        from app.domain.services.chat_temporal_intent_service import (
            ChatTemporalIntentService,
        )

        reason_by_offset = {
            -1: "lastWeekCalendar",
            0: "currentWeekCalendar",
            1: "nextWeekCalendar",
        }

        for offset, phrases in ChatDateRangeVocabularyService.week_offset_phrases().items():
            if not _contains_any(normalized, phrases):
                continue

            start, end = ChatTemporalIntentService.calendar_week_range(
                reference,
                offset_weeks=offset,
            )
            return cls._from_dates(
                start,
                end,
                reason=cls._reason(reason_by_offset[offset]),
            )

        return None

    @classmethod
    def _resolve_next_month_phrases(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedDateRange | None:
        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("nextMonthPhrases")):
            return cls._next_month(reference, reason=cls._reason("nextMonth"))

        return None

    @classmethod
    def _resolve_quarter_phrases(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedDateRange | None:
        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("previousQuarterPhrases")):
            return cls._quarter_range(
                reference,
                offset=-1,
                reason=cls._reason("previousQuarter"),
            )

        if _contains_any(normalized, ChatDateRangeVocabularyService.terms("currentQuarterPhrases")):
            return cls._quarter_range(
                reference,
                offset=0,
                reason=cls._reason("currentQuarter"),
            )

        return None

    @classmethod
    def _quarter_range(
        cls,
        reference: date,
        *,
        offset: int,
        reason: str,
    ) -> ResolvedDateRange:
        quarter = (reference.month - 1) // 3 + 1 + offset
        year = reference.year

        while quarter < 1:
            quarter += 4
            year -= 1

        while quarter > 4:
            quarter -= 4
            year += 1

        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        last_day = monthrange(year, end_month)[1]

        return cls._from_dates(
            date(year, start_month, 1),
            date(year, end_month, last_day),
            reason=reason,
        )

    @classmethod
    def _next_month(cls, reference: date, *, reason: str) -> ResolvedDateRange:
        if reference.month == 12:
            year = reference.year + 1
            month = 1
        else:
            year = reference.year
            month = reference.month + 1

        return cls._month_range(year, month, reason=reason)

    @classmethod
    def _previous_month(cls, reference: date, *, reason: str) -> ResolvedDateRange:
        if reference.month == 1:
            year = reference.year - 1
            month = 12
        else:
            year = reference.year
            month = reference.month - 1

        return cls._month_range(year, month, reason=reason)

    @classmethod
    def _month_range(cls, year: int, month: int, *, reason: str) -> ResolvedDateRange:
        month = max(1, min(month, 12))
        last_day = monthrange(year, month)[1]

        return cls._from_dates(
            date(year, month, 1),
            date(year, month, last_day),
            reason=reason,
        )

    @classmethod
    def _from_dates(cls, start: date, end: date, *, reason: str) -> ResolvedDateRange:
        return ResolvedDateRange(
            start_date=cls.format_api_date(start),
            end_date=cls.format_api_date(end),
            reason=reason,
        )

    @classmethod
    def format_api_date(cls, value: date) -> str:
        return f"{value.day:02d}-{value.month:02d}-{value.year:04d}"

    @classmethod
    def _to_date(cls, day: int, month: int, year: int) -> date | None:
        if year < 100:
            year += 2000

        try:
            return date(year, month, day)
        except ValueError:
            return None

    @classmethod
    def _reason(cls, key: str, **values) -> str:
        return ExternalActionResponseContentService.format(
            "dateRangeReasons",
            key,
            **values,
        )

    @classmethod
    def _message_role(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @classmethod
    def _message_content(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")
