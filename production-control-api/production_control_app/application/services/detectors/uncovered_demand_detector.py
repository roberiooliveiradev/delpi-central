"""Detector — demanda sem cobertura de OP/estoque.

Reusa a mesma regra da aba Demanda (``DemandCoverageService``): saldo aberto
sem estoque nem OP suficiente, ou OP só prevista depois da entrega. A
api-delpi só entrega o dump TOTVS; a classificação fica no BFF.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from production_control_app.application.services.demand_service import (
    DemandService,
    _DemandSnapshotCache,
)
from production_control_app.application.services.problem_analysis_settings import as_int
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.problem_detector import (
    DetectorPage,
    DetectorSummary,
)
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)
from production_control_app.domain.services.demand_coverage_service import (
    STATUS_AT_RISK,
    DemandCoverageService,
    DemandLine,
)

DETECTOR_ID = "uncovered-demand-lines"

_DEFAULT_SEVERITY = {"uncovered": "critical", "late_op": "attention", "clear": "ok"}
_FAR_FUTURE = date(9999, 12, 31)
_QTY_EPS = 1e-6


class UncoveredDemandDetector:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        settings: dict[str, Any] | None = None,
        today: date | None = None,
        demand_service: DemandService | None = None,
    ) -> None:
        self._settings = settings or {}
        self._today = today
        self._demand = demand_service or DemandService(
            gateway,
            today=today,
            coverage=DemandCoverageService(today=today),
            cache=_DemandSnapshotCache(0),
        )

    @property
    def id(self) -> str:
        return DETECTOR_ID

    def _severity_map(self) -> dict[str, str]:
        raw = self._settings.get("severity")
        if not isinstance(raw, dict):
            return dict(_DEFAULT_SEVERITY)
        return {**_DEFAULT_SEVERITY, **{k: str(v) for k, v in raw.items()}}

    def _page_size(self, requested: int | None = None) -> int:
        if requested and requested > 0:
            return requested
        return as_int(self._settings.get("pageSize"), 50) or 50

    def _reference_date(self) -> date:
        return self._today or date.today()

    def _issue_kind(self, line: DemandLine) -> str | None:
        if line.uncovered_quantity > _QTY_EPS:
            return "uncovered"
        if line.status == STATUS_AT_RISK:
            return "late_op"
        return None

    def _map_item(self, line: DemandLine) -> dict[str, Any]:
        kind = self._issue_kind(line) or "uncovered"
        severity_map = self._severity_map()
        today = self._reference_date()
        payload = line.to_dict(today)
        return {
            "id": f"{DETECTOR_ID}:{line.key}",
            "kind": DETECTOR_ID,
            "severity": severity_map.get(kind, severity_map["uncovered"]),
            "issue_kind": kind,
            "branch": payload["branch"],
            "sales_order": payload["sales_order"],
            "line_item": payload["line_item"],
            "customer_name": payload["customer_name"],
            "customer_code": payload["customer_code"],
            "customer_order": payload["customer_order"],
            "product_code": payload["product_code"],
            "open_quantity": payload["open_quantity"],
            "uncovered_quantity": payload["uncovered_quantity"],
            "allocated_stock": payload["allocated_stock"],
            "covered_by_orders": payload["covered_by_orders"],
            "covering_orders": payload["covering_orders"],
            "due_date": payload["due_date"],
            "coverage_date": payload["coverage_date"],
            "status": payload["status"],
            "days_late": payload["days_late"],
            # Reuso do filtro da grade (produto / cliente).
            "root_code": payload["product_code"],
            "root_description": payload["customer_name"],
        }

    def _summary_from(
        self, lines: list[DemandLine], *, checked_line_count: int
    ) -> DetectorSummary:
        uncovered = [line for line in lines if self._issue_kind(line) == "uncovered"]
        late_op = [line for line in lines if self._issue_kind(line) == "late_op"]
        severity_map = self._severity_map()
        severity = severity_map["clear"]
        if uncovered:
            severity = severity_map["uncovered"]
        elif late_op:
            severity = severity_map["late_op"]
        return DetectorSummary(
            count=len(lines),
            severity=severity,
            metrics={
                "checked_line_count": checked_line_count,
                "uncovered_line_count": len(uncovered),
                "late_op_line_count": len(late_op),
                "uncovered_quantity": round(
                    sum(line.uncovered_quantity for line in uncovered), 3
                ),
            },
        )

    def summarize(self, *, branch: str) -> DetectorSummary:
        all_lines = self._demand.branch_lines(branch)
        problems = [line for line in all_lines if self._issue_kind(line) is not None]
        return self._summary_from(problems, checked_line_count=len(all_lines))

    def collect(self, *, branch: str, page: int, page_size: int) -> DetectorPage:
        resolved_size = self._page_size(page_size)
        resolved_page = max(page, 1)
        try:
            all_lines = self._demand.branch_lines(branch)
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível conferir a cobertura da demanda."
            ) from exc

        lines = [line for line in all_lines if self._issue_kind(line) is not None]
        lines.sort(
            key=lambda line: (
                0 if self._issue_kind(line) == "uncovered" else 1,
                line.due_date or _FAR_FUTURE,
                line.sales_order,
                line.line_item,
            )
        )
        summary = self._summary_from(lines, checked_line_count=len(all_lines))
        start = (resolved_page - 1) * resolved_size
        page_lines = lines[start : start + resolved_size]
        return DetectorPage(
            items=[self._map_item(line) for line in page_lines],
            total=summary.count,
            page=resolved_page,
            page_size=resolved_size,
            summary=summary,
        )