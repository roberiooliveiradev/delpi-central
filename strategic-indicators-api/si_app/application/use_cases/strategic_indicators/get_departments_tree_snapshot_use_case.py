"""Use case leve para a Fase 1 do carregamento progressivo da árvore.

Retorna IGD, departamentos e indicadores do período atual com variação
em relação ao mês anterior, **sem** séries históricas (sparklines).

Usa `get_current_and_previous_snapshot` em vez de `load_period_snapshots` para
evitar o custo de montar N períodos e agregações de trends na fase snapshot.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.application.use_cases.strategic_indicators.get_departments_tree_use_case import (
    GetStrategicIndicatorsDepartmentsTreeUseCase,
    _TreeScopeConfig,
)
from si_app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)


@dataclass(frozen=True)
class GetDepartmentsTreeSnapshotRequest:
    view_mode: str = "consolidated"
    branch: str | None = None
    competence: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class GetDepartmentsTreeSnapshotUseCase:
    """Fase 1: estrutura da árvore (IGD + departamentos + indicadores)."""

    def __init__(
        self,
        *,
        tree_use_case: GetStrategicIndicatorsDepartmentsTreeUseCase,
        snapshot_service: StrategicIndicatorsSnapshotService,
        alerts_summary_port: StrategicIndicatorsAlertsSummaryPort,
    ) -> None:
        self._tree = tree_use_case
        self._snapshot_service = snapshot_service
        self._alerts_summary_port = alerts_summary_port

    def execute(self, request: GetDepartmentsTreeSnapshotRequest) -> dict:
        scopes = self._tree._resolve_scopes(request.view_mode, request.branch)

        scope_payloads: list[dict] = []
        with ThreadPoolExecutor(max_workers=min(4, len(scopes))) as executor:
            futures = {
                executor.submit(self._load_scope, request, scope): scope
                for scope in scopes
            }
            for future in as_completed(futures):
                scope_payloads.append(future.result())

        scope_payloads.sort(
            key=lambda item: self._tree._scope_sort_key(str(item["scope_key"])),
        )

        primary = next(
            (item for item in scope_payloads if item["scope_key"] == "consolidated"),
            scope_payloads[0] if scope_payloads else None,
        )
        current_snapshot = (
            primary.get("current_snapshot") if primary is not None else None
        )
        measurement_errors = (
            list(current_snapshot.measurement_errors) if current_snapshot else []
        )
        calculated_departments = (
            current_snapshot.calculated_departments if current_snapshot else []
        )

        return {
            "competence": (
                current_snapshot.period.competence
                if current_snapshot is not None
                else request.competence
            ),
            "igd": current_snapshot.igd if current_snapshot else None,
            "igd_exact": current_snapshot.igd_exact if current_snapshot else None,
            "classification": (
                current_snapshot.classification if current_snapshot else None
            ),
            "errors": measurement_errors,
            "partial_success": len(measurement_errors) > 0,
            "alerts_summary": self._alerts_summary_port.get_alerts_summary(
                departments=calculated_departments,
                measurement_errors=measurement_errors,
            ),
            "scopes": [
                {
                    "scope_key": item["scope_key"],
                    "scope_label": item["scope_label"],
                    "branch": item["branch"],
                    "departments": item["departments"],
                    "indicators": item["indicators"],
                }
                for item in scope_payloads
            ],
            "meta": {
                "source": "snapshot",
                "scope_count": len(scope_payloads),
            },
        }

    def _load_scope(
        self,
        request: GetDepartmentsTreeSnapshotRequest,
        scope: _TreeScopeConfig,
    ) -> dict:
        comparative = self._snapshot_service.get_current_and_previous_snapshot(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            branch=scope.branch,
        )

        current_snapshot = comparative.current
        previous_snapshot = comparative.previous

        return {
            "scope_key": scope.scope_key,
            "scope_label": scope.scope_label,
            "branch": scope.branch,
            "current_snapshot": current_snapshot,
            "departments": self._tree._map_departments(
                current_snapshot,
                previous_snapshot,
            ),
            "indicators": self._tree._map_indicators(
                current_snapshot,
                previous_snapshot,
                catalog=comparative.catalog,
            ),
        }
