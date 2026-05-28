"""Resolve períodos em linguagem natural para parâmetros start_date/end_date (DD-MM-YYYY)."""

from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

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


@dataclass(frozen=True)
class ResolvedDateRange:
    start_date: str
    end_date: str
    reason: str


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

    @classmethod
    def resolve(cls, message: str | None, *, today: date | None = None) -> ResolvedDateRange | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        reference = today or date.today()

        explicit = cls._parse_explicit_range(normalized)

        if explicit:
            return explicit

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

        if year_month and any(
            term in normalized
            for term in ("cpv", "otd", "idd", "giro", "kpi", "indicador", "rol", "ebitda")
        ):
            return cls._month_range(
                int(year_month.group(1)),
                int(year_month.group(2)),
                reason="Período ano-mês na pergunta.",
            )

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
        for name, month in _MONTHS_PT.items():
            if name not in normalized:
                continue

            year_match = re.search(rf"\b{re.escape(name)}\s+de\s+(\d{{4}})\b", normalized)

            if year_match:
                year = int(year_match.group(1))
            else:
                year = reference.year

            return cls._month_range(year, month, reason=f"Mês {name}.")

        return None

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
