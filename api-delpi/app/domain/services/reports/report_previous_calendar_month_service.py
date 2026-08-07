"""Períodos do Relatório Gerencial — mês civil anterior e comparativo.

Dado ``as_of`` no fuso America/Sao_Paulo, o relatório cobre o mês civil
imediatamente anterior; o comparativo é o mês anterior a esse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.shared.pt_month_labels import MONTH_ABBREV_PT

DEFAULT_TIMEZONE = "America/Sao_Paulo"

_MONTH_LABELS_PT = MONTH_ABBREV_PT


@dataclass(frozen=True, slots=True)
class CalendarMonthWindow:
    """Janela de um mês civil (datas inclusivas YYYY-MM-DD)."""

    start_date: str
    end_date: str
    year: int
    month: int

    @property
    def label_pt(self) -> str:
        return f"{_MONTH_LABELS_PT[self.month - 1]}/{self.year}"

    @property
    def label_pt_chart(self) -> str:
        """Rótulo curto estilo gráfico: Jan/26."""
        short = _MONTH_LABELS_PT[self.month - 1]
        return f"{short[:1].upper()}{short[1:]}/{str(self.year)[2:]}"

    @property
    def label_pt_title(self) -> str:
        full = (
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        )
        return f"{full[self.month - 1]}/{self.year}"


@dataclass(frozen=True, slots=True)
class PreviousCalendarMonthPair:
    report: CalendarMonthWindow
    compare: CalendarMonthWindow


class ReportPreviousCalendarMonthService:
    """Resolve mês do relatório e mês comparativo a partir de uma data de referência."""

    @staticmethod
    def resolve(
        as_of: date | datetime | None = None,
        *,
        timezone_name: str = DEFAULT_TIMEZONE,
    ) -> PreviousCalendarMonthPair:
        as_of_date = ReportPreviousCalendarMonthService._coerce_date(
            as_of,
            timezone_name=timezone_name,
        )
        report = ReportPreviousCalendarMonthService._month_window(
            as_of_date.year,
            as_of_date.month,
            offset_months=-1,
        )
        compare = ReportPreviousCalendarMonthService._month_window(
            as_of_date.year,
            as_of_date.month,
            offset_months=-2,
        )
        return PreviousCalendarMonthPair(report=report, compare=compare)

    @staticmethod
    def _coerce_date(
        as_of: date | datetime | None,
        *,
        timezone_name: str,
    ) -> date:
        tz = ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
        if as_of is None:
            return datetime.now(tz).date()
        if isinstance(as_of, datetime):
            if as_of.tzinfo is None:
                return as_of.replace(tzinfo=tz).date()
            return as_of.astimezone(tz).date()
        return as_of

    @staticmethod
    def _month_window(year: int, month: int, *, offset_months: int) -> CalendarMonthWindow:
        y, m = year, month + offset_months
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(y, m + 1, 1) - timedelta(days=1)
        return CalendarMonthWindow(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            year=y,
            month=m,
        )
