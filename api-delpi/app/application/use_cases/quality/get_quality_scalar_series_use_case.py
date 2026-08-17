"""Série mensal genérica a partir de um summary scalar (quality dashboard)."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Callable


@dataclass(frozen=True)
class QualityScalarSeriesPoint:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityScalarSeriesResponse:
    metric: str
    granularity: str
    truncated: bool
    points: list[QualityScalarSeriesPoint]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "granularity": self.granularity,
            "truncated": self.truncated,
            "points": [asdict(point) for point in self.points],
        }


def _parse_flexible_date(value: str | None) -> date | None:
    if not value:
        return None
    trimmed = value.strip()
    try:
        return date.fromisoformat(trimmed)
    except ValueError:
        pass
    parts = trimmed.split("-")
    if len(parts) == 3 and len(parts[0]) == 2:
        try:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year, month, day)
        except ValueError:
            return None
    return None


def _format_delpi(d: date) -> str:
    return f"{str(d.day).zfill(2)}-{str(d.month).zfill(2)}-{d.year}"


def iter_month_buckets(
    *,
    start_date: str | None,
    end_date: str | None,
    max_months: int = 24,
) -> tuple[list[tuple[str, str, str]], bool]:
    """Retorna [(sort_key YYYY-MM, start DD-MM-YYYY, end DD-MM-YYYY), …]."""
    range_start = _parse_flexible_date(start_date)
    range_end = _parse_flexible_date(end_date)
    if not range_start or not range_end or range_start > range_end:
        return [], False

    buckets: list[tuple[str, str, str]] = []
    truncated = False
    year, month = range_start.year, range_start.month
    while True:
        month_start = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        clamped_start = max(month_start, range_start)
        clamped_end = min(month_end, range_end)
        if clamped_start <= clamped_end:
            key = f"{year}-{str(month).zfill(2)}"
            buckets.append(
                (key, _format_delpi(clamped_start), _format_delpi(clamped_end))
            )
        if month_end >= range_end:
            break
        month += 1
        if month > 12:
            month = 1
            year += 1
        if len(buckets) >= max_months:
            truncated = True
            break
    return buckets, truncated


class GetQualityScalarSeriesUseCase:
    """Orquestra N summaries mensais e devolve points densos."""

    def __init__(
        self,
        *,
        metric: str,
        fetch_metrics: Callable[[str | None, str, str], dict[str, Any]],
    ) -> None:
        self._metric = metric
        self._fetch_metrics = fetch_metrics

    def execute(
        self,
        *,
        branch: str | None,
        date_start: str | None,
        date_end: str | None,
        granularity: str = "month",
    ) -> QualityScalarSeriesResponse:
        if granularity != "month":
            raise ValueError("granularity must be month")

        buckets, truncated = iter_month_buckets(
            start_date=date_start,
            end_date=date_end,
        )
        points: list[QualityScalarSeriesPoint] = []
        for sort_key, bucket_start, bucket_end in buckets:
            metrics = self._fetch_metrics(branch, bucket_start, bucket_end)
            points.append(
                QualityScalarSeriesPoint(
                    periodo=sort_key,
                    sort_key=sort_key,
                    start_date=bucket_start,
                    end_date=bucket_end,
                    metrics=metrics,
                )
            )
        return QualityScalarSeriesResponse(
            metric=self._metric,
            granularity=granularity,
            truncated=truncated,
            points=points,
        )
