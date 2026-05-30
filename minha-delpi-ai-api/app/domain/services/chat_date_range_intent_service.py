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

_MONTHS_PT = {
    "janeiro": 1,
    "jan": 1,
    "fevereiro": 2,
    "fev": 2,
    "marco": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "maio": 5,
    "mai": 5,
    "junho": 6,
    "jun": 6,
    "julho": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "setembro": 9,
    "set": 9,
    "outubro": 10,
    "out": 10,
    "novembro": 11,
    "nov": 11,
    "dezembro": 12,
    "dez": 12,
}

_MONTH_LABELS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

_PERIOD_METRIC_TERMS = (
    "rol",
    "cpv",
    "otd",
    "idd",
    "giro",
    "kpi",
    "indicador",
    "ebitda",
    "faturamento",
    "ppm",
    "oee",
    "pmr",
)


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
    _YEAR_ONLY_RE = re.compile(r"^\s*(\d{4})\s*$")
    _MONTH_ORDER = tuple(sorted(_MONTHS_PT.keys(), key=len, reverse=True))

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

        if any(
            term in normalized
            for term in (
                "semana passada",
                "semana que vem",
                "proxima semana",
                "mes que vem",
                "proximo mes",
            )
        ):
            week_range = cls._resolve_calendar_week_phrases(normalized, reference)
            if week_range:
                return week_range

            month_range = cls._resolve_next_month_phrases(normalized, reference)
            if month_range:
                return month_range

        point = ChatTemporalIntentService.resolve_point(
            message,
            today=reference,
            default_today=False,
        )
        if point and cls._should_use_point_as_range(normalized):
            return cls._from_dates(
                point.target_date,
                point.target_date,
                reason=f"Data {point.label}.",
            )

        competence = cls._COMPETENCE_RE.search(normalized)

        if competence:
            return cls._month_range(
                int(competence.group(1)),
                int(competence.group(2)),
                reason="Competência explícita na pergunta.",
            )

        last_days = cls._LAST_N_DAYS_RE.search(normalized)

        if last_days:
            days = max(1, min(int(last_days.group(1)), 366))
            start = reference - timedelta(days=days - 1)

            return cls._from_dates(
                start,
                reference,
                reason=f"Últimos {days} dias.",
            )

        if any(term in normalized for term in ("ultima semana", "última semana", "ultimos 7 dias")):
            start = reference - timedelta(days=6)

            return cls._from_dates(start, reference, reason="Última semana.")

        if any(term in normalized for term in ("mes passado", "mês passado", "ultimo mes", "último mês")):
            return cls._previous_month(reference, reason="Mês passado.")

        if any(term in normalized for term in ("mes atual", "mês atual", "este mes", "este mês")):
            return cls._month_range(
                reference.year,
                reference.month,
                reason="Mês atual.",
            )

        if "ano passado" in normalized:
            year = reference.year - 1

            return cls._from_dates(
                date(year, 1, 1),
                date(year, 12, 31),
                reason="Ano passado.",
            )

        month_match = cls._parse_named_month(normalized, reference)

        if month_match:
            return month_match

        year_month = cls._YEAR_MONTH_RE.search(normalized)

        if year_month and any(term in normalized for term in _PERIOD_METRIC_TERMS):
            return cls._month_range(
                int(year_month.group(1)),
                int(year_month.group(2)),
                reason="Período ano-mês na pergunta.",
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

        return (
            f"Para **{ambiguous.month_label}**, preciso confirmar o ano: "
            f"você quer os dados de **{ambiguous.current_year}** (este ano) "
            f"ou de **{ambiguous.previous_year}**?"
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

        return any(term in normalized for term in _PERIOD_METRIC_TERMS)

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
            reason=f"Mês {pending.label} de {year} (confirmação do usuário).",
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
        for name in cls._MONTH_ORDER:
            if not cls._contains_month_name(normalized, name):
                continue

            month = _MONTHS_PT[name]
            label = _MONTH_LABELS_PT.get(month, name)
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

        return cls._from_dates(start, end, reason="Intervalo de datas explícito.")

    @classmethod
    def _parse_named_month(cls, normalized: str, reference: date) -> ResolvedDateRange | None:
        named_month = cls._extract_named_month(normalized)

        if not named_month:
            return None

        if named_month.year is not None:
            return cls._month_range(
                named_month.year,
                named_month.month,
                reason=f"Mês {named_month.label} de {named_month.year}.",
            )

        if reference.month < named_month.month:
            return None

        return cls._month_range(
            reference.year,
            named_month.month,
            reason=f"Mês {named_month.label} de {reference.year}.",
        )

    @classmethod
    def _should_use_point_as_range(cls, normalized: str) -> bool:
        if any(term in normalized for term in _PERIOD_METRIC_TERMS):
            return True

        return any(
            term in normalized
            for term in (
                "ontem",
                "anteontem",
                "antes de ontem",
                "amanha",
                "depois de amanha",
                "dia ",
                " de janeiro",
                " de fevereiro",
                " de marco",
                " de abril",
                " de maio",
                " de junho",
                " de julho",
                " de agosto",
                " de setembro",
                " de outubro",
                " de novembro",
                " de dezembro",
            )
        )

    @classmethod
    def _resolve_calendar_week_phrases(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedDateRange | None:
        from app.domain.services.chat_temporal_intent_service import (
            ChatTemporalIntentService,
        )

        if "semana passada" in normalized:
            start, end = ChatTemporalIntentService.calendar_week_range(
                reference,
                offset_weeks=-1,
            )
            return cls._from_dates(start, end, reason="Semana passada.")

        if any(term in normalized for term in ("semana que vem", "proxima semana")):
            start, end = ChatTemporalIntentService.calendar_week_range(
                reference,
                offset_weeks=1,
            )
            return cls._from_dates(start, end, reason="Semana que vem.")

        return None

    @classmethod
    def _resolve_next_month_phrases(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedDateRange | None:
        if any(
            term in normalized
            for term in ("mes que vem", "mês que vem", "proximo mes", "próximo mês")
        ):
            return cls._next_month(reference, reason="Mês que vem.")

        return None

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
    def _message_role(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @classmethod
    def _message_content(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")
