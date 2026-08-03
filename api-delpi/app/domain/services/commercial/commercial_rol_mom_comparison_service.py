"""Comparativo MoM de ROL — consolidado, filiais e ranking por cliente."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.entities.commercial.rol_by_customer import RolByCustomerResult
from app.domain.services.reports.report_previous_calendar_month_service import (
    CalendarMonthWindow,
    PreviousCalendarMonthPair,
    ReportPreviousCalendarMonthService,
)


class _FinancialRolPort(Protocol):
    def get_rol(self, request: GetRolRequest) -> dict: ...


class _RolByCustomerPort(Protocol):
    def get_rol_by_customer(
        self,
        request: GetRolByCustomerRequest,
    ) -> RolByCustomerResult: ...


BRANCH_KEYS = ("consolidated", "01", "02")
BRANCH_LABELS_PT = {
    "consolidated": "Consolidado",
    "01": "Jaraguá do Sul (SC)",
    "02": "Rio Bananal (ES)",
}


@dataclass(frozen=True, slots=True)
class RolMomBranchSnapshot:
    branch: str
    label_pt: str
    current: float
    previous: float
    delta: float
    pct_change: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "label_pt": self.label_pt,
            "current": self.current,
            "previous": self.previous,
            "delta": self.delta,
            "pct_change": self.pct_change,
        }


@dataclass(frozen=True, slots=True)
class RolMomCustomerRow:
    customer_code: str
    customer_store: str
    customer_name: str
    current: float
    previous: float
    share_pct: float | None
    delta: float
    pct_change: float | None
    rank: int
    is_others: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "current": self.current,
            "previous": self.previous,
            "share_pct": self.share_pct,
            "delta": self.delta,
            "pct_change": self.pct_change,
            "rank": self.rank,
            "is_others": self.is_others,
        }


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None if current == 0 else None
    return round(((current - previous) / abs(previous)) * 100.0, 2)


def pct_change_allow_new(current: float, previous: float) -> float | None:
    """Δ% quando há base anterior; None se anterior = 0 (novo / sem base)."""
    if previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100.0, 2)


class CommercialRolMomComparisonService:
    """Orquestra get_rol × filiais e ranking por cliente nos dois períodos."""

    def __init__(
        self,
        financial_repository: _FinancialRolPort,
        rol_by_customer_repository: _RolByCustomerPort,
    ) -> None:
        self._financial = financial_repository
        self._by_customer = rol_by_customer_repository

    def build(
        self,
        periods: PreviousCalendarMonthPair,
        *,
        customer_limit: int = 20,
        branch_for_customers: str | None = None,
    ) -> dict[str, Any]:
        branches = tuple(
            self._branch_snapshot(key, periods.report, periods.compare)
            for key in BRANCH_KEYS
        )
        customers = self._customer_rows(
            periods,
            customer_limit=customer_limit,
            branch=branch_for_customers,
        )
        year_evolution = self._year_evolution(periods.report)
        return {
            "report_period": {
                "start_date": periods.report.start_date,
                "end_date": periods.report.end_date,
                "label_pt": periods.report.label_pt,
                "label_pt_title": periods.report.label_pt_title,
                "year": periods.report.year,
                "month": periods.report.month,
            },
            "compare_period": {
                "start_date": periods.compare.start_date,
                "end_date": periods.compare.end_date,
                "label_pt": periods.compare.label_pt,
                "label_pt_title": periods.compare.label_pt_title,
                "year": periods.compare.year,
                "month": periods.compare.month,
            },
            "branches": [item.to_dict() for item in branches],
            "customers": [item.to_dict() for item in customers],
            "year_evolution": year_evolution,
        }

    def _branch_snapshot(
        self,
        branch_key: str,
        report: CalendarMonthWindow,
        compare: CalendarMonthWindow,
    ) -> RolMomBranchSnapshot:
        branch_param = None if branch_key == "consolidated" else branch_key
        current = self._rol_value(branch_param, report.start_date, report.end_date)
        previous = self._rol_value(branch_param, compare.start_date, compare.end_date)
        return RolMomBranchSnapshot(
            branch=branch_key,
            label_pt=BRANCH_LABELS_PT[branch_key],
            current=current,
            previous=previous,
            delta=round(current - previous, 2),
            pct_change=pct_change_allow_new(current, previous),
        )

    def _rol_value(
        self,
        branch: str | None,
        start_date: str,
        end_date: str,
    ) -> float:
        result = self._financial.get_rol(
            GetRolRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )
        return float(result.get("rol_with_ipi") or 0)

    def _year_evolution(self, report: CalendarMonthWindow) -> list[dict[str, Any]]:
        """ROL consolidado de jan até o mês do relatório (mesmo ano)."""
        points: list[dict[str, Any]] = []
        for month in range(1, int(report.month) + 1):
            window = ReportPreviousCalendarMonthService._month_window(
                report.year,
                month,
                offset_months=0,
            )
            value = self._rol_value(None, window.start_date, window.end_date)
            points.append(
                {
                    "year": window.year,
                    "month": window.month,
                    "start_date": window.start_date,
                    "end_date": window.end_date,
                    "label": window.label_pt_chart,
                    "value": value,
                }
            )
        return points

    def _customer_rows(
        self,
        periods: PreviousCalendarMonthPair,
        *,
        customer_limit: int,
        branch: str | None,
    ) -> list[RolMomCustomerRow]:
        current = self._by_customer.get_rol_by_customer(
            GetRolByCustomerRequest(
                branch=branch,
                start_date=periods.report.start_date,
                end_date=periods.report.end_date,
                limit=customer_limit,
                include_others=True,
            )
        )
        previous = self._by_customer.get_rol_by_customer(
            GetRolByCustomerRequest(
                branch=branch,
                start_date=periods.compare.start_date,
                end_date=periods.compare.end_date,
                limit=500,
                include_others=False,
            )
        )
        previous_map = {
            self._customer_key(item.customer_code, item.customer_store): float(
                item.rol_with_ipi
            )
            for item in previous.items
        }

        rows: list[RolMomCustomerRow] = []
        for item in current.items:
            prev_value = previous_map.get(
                self._customer_key(item.customer_code, item.customer_store),
                0.0,
            )
            current_value = float(item.rol_with_ipi)
            rows.append(
                RolMomCustomerRow(
                    customer_code=item.customer_code,
                    customer_store=item.customer_store,
                    customer_name=item.customer_name,
                    current=current_value,
                    previous=prev_value,
                    share_pct=item.share_pct,
                    delta=round(current_value - prev_value, 2),
                    pct_change=pct_change_allow_new(current_value, prev_value),
                    rank=item.rank,
                )
            )

        if current.others is not None:
            others_prev = self._others_previous(
                previous_map=previous_map,
                top_keys={
                    self._customer_key(item.customer_code, item.customer_store)
                    for item in current.items
                },
                previous_total=float(previous.total_rol or 0),
            )
            others_cur = float(current.others.rol_with_ipi)
            rows.append(
                RolMomCustomerRow(
                    customer_code="",
                    customer_store="",
                    customer_name="Demais",
                    current=others_cur,
                    previous=others_prev,
                    share_pct=current.others.share_pct,
                    delta=round(others_cur - others_prev, 2),
                    pct_change=pct_change_allow_new(others_cur, others_prev),
                    rank=current.others.rank,
                    is_others=True,
                )
            )
        return rows

    @staticmethod
    def _customer_key(code: str, store: str) -> str:
        return f"{str(code).strip()}|{str(store).strip()}"

    @staticmethod
    def _others_previous(
        *,
        previous_map: Mapping[str, float],
        top_keys: set[str],
        previous_total: float,
    ) -> float:
        top_previous = sum(
            value for key, value in previous_map.items() if key in top_keys
        )
        return round(previous_total - top_previous, 2)
