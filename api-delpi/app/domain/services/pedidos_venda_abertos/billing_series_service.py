"""Série de faturamento da carteira — buckets por granularidade."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class BillingSeriesPoint:
    """Ponto da série (chave do bucket)."""

    month: str  # chave do período (YYYY-MM-DD / YYYY-MM / YYYY)
    label: str
    value: float
    date_start: str  # YYYY-MM-DD
    date_end: str

    def to_dict(self) -> dict:
        return {
            "month": self.month,
            "label": self.label,
            "value": self.value,
            "date_start": self.date_start,
            "date_end": self.date_end,
        }


_MONTH_LABELS_PT = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)


def _shift_month(anchor: date, *, months_back: int) -> date:
    year = anchor.year
    month = anchor.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def month_key_iso(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def month_key_from_protheus(year_month: str) -> str | None:
    text = (year_month or "").strip()
    if len(text) >= 6 and text[:6].isdigit():
        return f"{text[0:4]}-{text[4:6]}"
    if len(text) >= 7 and text[4] == "-":
        return text[:7]
    return None


def period_key_from_protheus(value: str, *, granularity: str) -> str | None:
    """Normaliza a chave SQL (Protheus) para a chave do bucket ISO."""
    text = (value or "").strip()
    grain = (granularity or "month").strip().lower()
    if grain in {"day", "week"}:
        if len(text) >= 8 and text[:8].isdigit():
            return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
        if len(text) >= 10 and text[4] == "-":
            return text[:10]
        return None
    if grain == "year":
        if len(text) >= 4 and text[:4].isdigit():
            return text[:4]
        return None
    return month_key_from_protheus(text)


def period_key_to_date(period_key: str) -> date | None:
    text = (period_key or "").strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    if len(text) == 8 and text.isdigit():
        try:
            return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
        except ValueError:
            return None
    if len(text) == 7 and text[4] == "-":
        try:
            return date(int(text[0:4]), int(text[5:7]), 1)
        except ValueError:
            return None
    if len(text) == 6 and text.isdigit():
        try:
            return date(int(text[0:4]), int(text[4:6]), 1)
        except ValueError:
            return None
    if len(text) == 4 and text.isdigit():
        try:
            return date(int(text), 1, 1)
        except ValueError:
            return None
    return None


def month_label_pt(value: date) -> str:
    return f"{_MONTH_LABELS_PT[value.month - 1]}/{str(value.year)[2:]}"


def build_billing_series_window(
    *,
    end: date | None = None,
    months: int = 12,
) -> list[date]:
    """Retorna o 1º dia de cada mês, do mais antigo ao mais recente (inclui mês atual)."""
    anchor = end or date.today()
    count = max(1, min(int(months), 36))
    return [_shift_month(anchor, months_back=offset) for offset in range(count - 1, -1, -1)]


def fill_billing_monthly_series(
    *,
    billed_by_month: dict[str, float],
    end: date | None = None,
    months: int = 12,
) -> list[BillingSeriesPoint]:
    points: list[BillingSeriesPoint] = []
    for month_start in build_billing_series_window(end=end, months=months):
        key = month_key_iso(month_start)
        last_day = monthrange(month_start.year, month_start.month)[1]
        month_end = date(month_start.year, month_start.month, last_day)
        points.append(
            BillingSeriesPoint(
                month=key,
                label=month_label_pt(month_start),
                value=float(billed_by_month.get(key, 0.0) or 0.0),
                date_start=month_start.isoformat(),
                date_end=month_end.isoformat(),
            )
        )
    return points
