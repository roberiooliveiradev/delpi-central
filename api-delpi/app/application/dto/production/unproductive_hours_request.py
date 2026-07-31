"""DTOs e formatters — horas improdutivas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.domain.production.unproductive_hours_view_scope import (
    DEFAULT_ITEMS_SORT,
    DEFAULT_MONTHS_WINDOW,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RANKING_LIMIT,
    ITEMS_SORT_VALUES,
    MAX_MONTHS_WINDOW,
    MAX_PAGE_SIZE,
    MAX_RANKING_LIMIT,
    METRIC_HOURS,
    METRIC_VALUES,
    OPERADOR_SEM_NOME_LABEL,
    RANK_BY_VALUES,
    VALID_UNPRODUCTIVE_HOURS_BRANCHES,
)


def round_hours(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 4)


def round_cost(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 2)


def as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def display_operator_name(value: Any) -> str:
    return clean_text(value) or OPERADOR_SEM_NOME_LABEL


def iso_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text[:10]


def _default_period_start(end: date, months_window: int = DEFAULT_MONTHS_WINDOW) -> date:
    offset = months_window - 1
    total = end.year * 12 + end.month - 1 - offset
    year = total // 12
    month = total % 12 + 1
    return date(year, month, 1)


def _months_inclusive(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _parse_iso_date(value: str | None) -> date | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class UnproductiveHoursPeriod:
    start_date: date
    end_date: date
    branch: str | None

    @classmethod
    def resolve(
        cls,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> UnproductiveHoursPeriod:
        normalized_branch = str(branch or "").strip() or None
        if normalized_branch is not None and normalized_branch not in VALID_UNPRODUCTIVE_HOURS_BRANCHES:
            raise ValueError('branch inválida. Use "01" ou "02".')

        parsed_start = _parse_iso_date(start_date)
        parsed_end = _parse_iso_date(end_date)

        if start_date and parsed_start is None:
            raise ValueError("start_date inválida. Use o formato YYYY-MM-DD.")
        if end_date and parsed_end is None:
            raise ValueError("end_date inválida. Use o formato YYYY-MM-DD.")

        if parsed_start is None and parsed_end is None:
            end = date.today()
            start = _default_period_start(end)
            return cls(start_date=start, end_date=end, branch=normalized_branch)

        if parsed_start is None or parsed_end is None:
            raise ValueError("Informe start_date e end_date juntas, ou omita ambas.")

        if parsed_start > parsed_end:
            raise ValueError("start_date não pode ser maior que end_date.")

        if _months_inclusive(parsed_start, parsed_end) > MAX_MONTHS_WINDOW:
            raise ValueError(f"Período máximo permitido: {MAX_MONTHS_WINDOW} meses.")

        return cls(
            start_date=parsed_start,
            end_date=parsed_end,
            branch=normalized_branch,
        )

    def iso_range(self) -> tuple[str, str]:
        return self.start_date.isoformat(), self.end_date.isoformat()

    def periodo_dict(self) -> dict[str, str | None]:
        start, end = self.iso_range()
        return {
            "start_date": start,
            "end_date": end,
            "branch": self.branch,
            # Aliases camelCase PT (legado)
            "dataInicio": start,
            "dataFim": end,
            "filial": self.branch,
        }


@dataclass
class UnproductiveHoursQueryRequest:
    period: UnproductiveHoursPeriod
    stop_reason: str | None = None
    resource: str | None = None
    cost_center: str | None = None
    operator_code: str | None = None

    def __post_init__(self) -> None:
        self.stop_reason = clean_text(self.stop_reason) or None
        self.resource = clean_text(self.resource) or None
        self.cost_center = clean_text(self.cost_center) or None
        self.operator_code = clean_text(self.operator_code) or None

    def filter_kwargs(self) -> dict[str, str | None]:
        start, end = self.period.iso_range()
        return {
            "start_date": start,
            "end_date": end,
            "branch": self.period.branch,
            "stop_reason": self.stop_reason,
            "resource": self.resource,
            "cost_center": self.cost_center,
            "operator_code": self.operator_code,
        }

    def periodo_dict(self) -> dict[str, str | None]:
        return self.period.periodo_dict()


@dataclass
class UnproductiveHoursItemsRequest(UnproductiveHoursQueryRequest):
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    sort: str = DEFAULT_ITEMS_SORT

    def __post_init__(self) -> None:
        super().__post_init__()
        self.page = max(1, int(self.page or 1))
        self.page_size = min(MAX_PAGE_SIZE, max(1, int(self.page_size or DEFAULT_PAGE_SIZE)))
        sort = (self.sort or DEFAULT_ITEMS_SORT).strip().lower()
        if sort not in ITEMS_SORT_VALUES:
            raise ValueError(
                f"sort inválido. Use um de: {', '.join(ITEMS_SORT_VALUES)}."
            )
        self.sort = sort

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass
class UnproductiveHoursRankingRequest(UnproductiveHoursQueryRequest):
    rank_by: str = ""
    metric: str = METRIC_HOURS
    limit: int = DEFAULT_RANKING_LIMIT

    def __post_init__(self) -> None:
        super().__post_init__()
        rank_by = clean_text(self.rank_by).lower()
        if rank_by not in RANK_BY_VALUES:
            raise ValueError(
                f"rank_by inválido. Use um de: {', '.join(RANK_BY_VALUES)}."
            )
        self.rank_by = rank_by
        metric = clean_text(self.metric).lower() or METRIC_HOURS
        if metric not in METRIC_VALUES:
            raise ValueError(
                f"metric inválida. Use um de: {', '.join(METRIC_VALUES)}."
            )
        self.metric = metric
        self.limit = min(
            MAX_RANKING_LIMIT,
            max(1, int(self.limit or DEFAULT_RANKING_LIMIT)),
        )
