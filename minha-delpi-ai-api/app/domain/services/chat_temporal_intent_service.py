"""Compreensão de temporalidade em linguagem natural — ponto único (dia) no chat base."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.services.chat_date_range_intent_service import (
    _MONTH_LABELS_PT,
    _MONTHS_PT,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

_WEEKDAYS_PT: dict[str, int] = {
    "domingo": 6,
    "dom": 6,
    "segunda": 0,
    "segunda feira": 0,
    "seg": 0,
    "terca": 1,
    "terca feira": 1,
    "ter": 1,
    "quarta": 2,
    "quarta feira": 2,
    "qua": 2,
    "quinta": 3,
    "quinta feira": 3,
    "qui": 3,
    "sexta": 4,
    "sexta feira": 4,
    "sex": 4,
    "sabado": 5,
    "sab": 5,
}

_MONTH_ORDER = tuple(sorted(_MONTHS_PT.keys(), key=len, reverse=True))

_SLASH_DMY_RE = re.compile(
    r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b",
)
_ISO_YMD_RE = re.compile(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b")

_RANGE_MARKERS = (
    "semana passada",
    "semana anterior",
    "semana que vem",
    "proxima semana",
    "esta semana",
    "semana atual",
    "mes passado",
    "mes que vem",
    "proximo mes",
    "mes atual",
    "este mes",
    "ano passado",
    "este ano",
    "ano atual",
    "trimestre passado",
    "ultimo trimestre",
    "trimestre atual",
    "este trimestre",
    "ultimos ",
    "ultimas ",
    "ultima semana",
    "ultimos 7 dias",
    "competencia ",
    "dia atual",
    "data atual",
    "data de hoje",
    " de ",
    " a ",
)

_TODAY_PATTERNS = (
    r"\bhoje\b",
    r"\bhj\b",
    r"\bdia atual\b",
    r"\bdata atual\b",
    r"\bneste dia\b",
    r"\bno dia de hoje\b",
    r"\bdata de hoje\b",
    r"\bdia de hoje\b",
    r"\bnesta data\b",
)

_YESTERDAY_PATTERNS = (
    r"\bontem\b",
    r"\bdia anterior\b",
    r"\bdia previo\b",
    r"\bno dia anterior\b",
)

_TOMORROW_PATTERNS = (
    r"\bamanha\b",
    r"\bproximo dia\b",
    r"\bdia seguinte\b",
)


@dataclass(frozen=True)
class ResolvedTemporalPoint:
    target_date: date
    label: str
    kind: str = "explicit"
    use_reference_today: bool = False

    @property
    def iso_date(self) -> str:
        return self.target_date.isoformat()

    @property
    def br_date(self) -> str:
        return self.target_date.strftime("%d/%m/%Y")


class ChatTemporalIntentService:
    @classmethod
    def resolve_point(
        cls,
        message: str | None,
        *,
        today: date | None = None,
        default_today: bool = True,
    ) -> ResolvedTemporalPoint | None:
        reference = today or date.today()
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return cls._maybe_default_today(reference, default_today=default_today)

        explicit = cls._resolve_iso_ymd(normalized, reference)
        if explicit:
            return explicit

        explicit = cls._resolve_named_day_month(normalized, reference)
        if explicit:
            return explicit

        explicit = cls._resolve_slash_date(normalized, reference)
        if explicit:
            return explicit

        relative = cls._resolve_relative_day(normalized, reference)
        if relative:
            return relative

        weekday = cls._resolve_weekday(normalized, reference)
        if weekday:
            return weekday

        for pattern in _TODAY_PATTERNS:
            if re.search(pattern, normalized):
                return cls._for_today(reference)

        return cls._maybe_default_today(reference, default_today=default_today)

    @classmethod
    def has_temporal_reference(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if cls.resolve_point(message, default_today=False):
            return True

        return any(marker in normalized for marker in _RANGE_MARKERS)

    @classmethod
    def infer_point_from_sql(cls, sql: str | None, *, today: date | None = None) -> ResolvedTemporalPoint | None:
        text = str(sql or "")

        if "CAST(GETDATE()" in text:
            return cls._for_today(today or date.today())

        match = re.search(r"DECLARE\s+@DATA\s+DATE\s*=\s*'(\d{4}-\d{2}-\d{2})'", text, re.I)
        if not match:
            return None

        target = date.fromisoformat(match.group(1))
        return cls._build_point(target, today or date.today(), kind="explicit")

    @classmethod
    def _maybe_default_today(
        cls,
        reference: date,
        *,
        default_today: bool,
    ) -> ResolvedTemporalPoint | None:
        if default_today:
            return cls._for_today(reference)
        return None

    @classmethod
    def _for_today(cls, reference: date) -> ResolvedTemporalPoint:
        return ResolvedTemporalPoint(
            target_date=reference,
            label=ExternalActionResponseContentService.get("temporal", "today", default="hoje"),
            kind="today",
            use_reference_today=True,
        )

    @classmethod
    def _build_point(
        cls,
        target: date,
        reference: date,
        *,
        kind: str,
        relative: str | None = None,
        use_reference_today: bool | None = None,
    ) -> ResolvedTemporalPoint:
        if relative:
            label = relative
        elif target == reference:
            label = ExternalActionResponseContentService.get("temporal", "today", default="hoje")
            kind = "today"
        else:
            weekday = ExternalActionResponseContentService.weekday_label(target.weekday())
            label = ExternalActionResponseContentService.format(
                "temporal",
                "weekdayWithDate",
                weekday=weekday,
                date=target.strftime("%d/%m/%Y"),
            )

        if use_reference_today is None:
            today_label = ExternalActionResponseContentService.get("temporal", "today", default="hoje")
            use_reference_today = label == today_label or kind == "today"

        return ResolvedTemporalPoint(
            target_date=target,
            label=label,
            kind=kind,
            use_reference_today=use_reference_today,
        )

    @classmethod
    def _resolve_relative_day(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedTemporalPoint | None:
        if re.search(r"\bantes de ontem\b|\banteontem\b", normalized):
            target = reference - timedelta(days=2)
            return cls._build_point(
                target,
                reference,
                kind="relative",
                relative=ExternalActionResponseContentService.get(
                    "temporal",
                    "dayBeforeYesterday",
                    default="antes de ontem",
                ),
            )

        for pattern in _YESTERDAY_PATTERNS:
            if re.search(pattern, normalized):
                target = reference - timedelta(days=1)
                return cls._build_point(
                    target,
                    reference,
                    kind="relative",
                    relative=ExternalActionResponseContentService.get(
                        "temporal",
                        "yesterday",
                        default="ontem",
                    ),
                )

        if re.search(r"\bdepois de amanha\b", normalized):
            target = reference + timedelta(days=2)
            return cls._build_point(
                target,
                reference,
                kind="relative",
                relative=ExternalActionResponseContentService.get(
                    "temporal",
                    "dayAfterTomorrow",
                    default="depois de amanhã",
                ),
            )

        for pattern in _TOMORROW_PATTERNS:
            if re.search(pattern, normalized):
                target = reference + timedelta(days=1)
                return cls._build_point(
                    target,
                    reference,
                    kind="relative",
                    relative=ExternalActionResponseContentService.get(
                        "temporal",
                        "tomorrow",
                        default="amanhã",
                    ),
                )

        return None

    @classmethod
    def _resolve_iso_ymd(cls, normalized: str, reference: date) -> ResolvedTemporalPoint | None:
        match = _ISO_YMD_RE.search(normalized)
        if not match:
            return None

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        return cls._safe_point(day, month, year, reference, kind="explicit")

    @classmethod
    def _resolve_slash_date(cls, normalized: str, reference: date) -> ResolvedTemporalPoint | None:
        match = _SLASH_DMY_RE.search(normalized)
        if not match:
            return None

        first = int(match.group(1))
        second = int(match.group(2))
        year_raw = match.group(3)

        if year_raw:
            year = int(year_raw)
            if year < 100:
                year += 2000
        else:
            year = reference.year

        day, month = cls._interpret_day_month(first, second)
        target = cls._safe_date(day, month, year)

        if not target and not year_raw:
            target = cls._safe_date(day, month, year + 1)

        if not target:
            return None

        return cls._build_point(target, reference, kind="explicit")

    @classmethod
    def _resolve_named_day_month(
        cls,
        normalized: str,
        reference: date,
    ) -> ResolvedTemporalPoint | None:
        for month_name in _MONTH_ORDER:
            pattern = (
                rf"\b(?:dia\s+)?(\d{{1,2}})\s+de\s+{re.escape(month_name)}"
                rf"(?:\s+de|\s+/|\s+)?(?:\s*(\d{{4}}))?\b"
            )
            match = re.search(pattern, normalized)
            if not match:
                continue

            day = int(match.group(1))
            month = _MONTHS_PT[month_name]
            year_raw = match.group(2)

            if year_raw:
                year = int(year_raw)
            else:
                year = reference.year
                candidate = cls._safe_date(day, month, year)
                if candidate and candidate < reference:
                    year += 1

            target = cls._safe_date(day, month, year)
            if not target:
                return None

            month_label = _MONTH_LABELS_PT.get(month, month_name)
            label = ExternalActionResponseContentService.format(
                "temporal",
                "namedDayMonthYear",
                day=day,
                month=month_label,
                year=year,
            )
            return cls._build_point(target, reference, kind="explicit", relative=label)

        return None

    @classmethod
    def _resolve_weekday(cls, normalized: str, reference: date) -> ResolvedTemporalPoint | None:
        force_next = bool(re.search(r"\bproxim[ao]\b", normalized))
        force_past = bool(
            re.search(r"\b(passad[ao]|ultim[ao]|anterior)\b", normalized)
        )

        ordered = sorted(_WEEKDAYS_PT.keys(), key=len, reverse=True)
        for token in ordered:
            if not re.search(rf"\b{re.escape(token)}\b", normalized):
                continue

            weekday = _WEEKDAYS_PT[token]
            if force_past and not force_next:
                target = cls._previous_weekday(reference, weekday)
            else:
                target = cls._next_weekday(
                    reference,
                    weekday,
                    include_today=not force_next,
                )

            weekday_label = ExternalActionResponseContentService.weekday_label(weekday)
            formatted = target.strftime("%d/%m/%Y")
            return ResolvedTemporalPoint(
                target_date=target,
                label=ExternalActionResponseContentService.format(
                    "temporal",
                    "weekdayWithDate",
                    weekday=weekday_label,
                    date=formatted,
                ),
                kind="weekday",
                use_reference_today=False,
            )

        return None

    @classmethod
    def _next_weekday(
        cls,
        reference: date,
        weekday: int,
        *,
        include_today: bool,
    ) -> date:
        delta = (weekday - reference.weekday()) % 7

        if delta == 0 and not include_today:
            delta = 7

        return reference + timedelta(days=delta)

    @classmethod
    def _previous_weekday(cls, reference: date, weekday: int) -> date:
        delta = (reference.weekday() - weekday) % 7

        if delta == 0:
            delta = 7

        return reference - timedelta(days=delta)

    @classmethod
    def _interpret_day_month(cls, first: int, second: int) -> tuple[int, int]:
        if first > 31:
            return second, first
        if second > 12 and first <= 12:
            return second, first
        return first, second

    @classmethod
    def _safe_point(
        cls,
        day: int,
        month: int,
        year: int,
        reference: date,
        *,
        kind: str,
    ) -> ResolvedTemporalPoint | None:
        target = cls._safe_date(day, month, year)
        if not target:
            return None
        return cls._build_point(target, reference, kind=kind)

    @classmethod
    def _safe_date(cls, day: int, month: int, year: int) -> date | None:
        if year < 100:
            year += 2000

        try:
            return date(year, month, day)
        except ValueError:
            return None

    @classmethod
    def calendar_week_range(
        cls,
        reference: date,
        *,
        offset_weeks: int = 0,
    ) -> tuple[date, date]:
        start_of_week = reference - timedelta(days=reference.weekday())
        start = start_of_week + timedelta(weeks=offset_weeks)
        end = start + timedelta(days=6)
        return start, end
