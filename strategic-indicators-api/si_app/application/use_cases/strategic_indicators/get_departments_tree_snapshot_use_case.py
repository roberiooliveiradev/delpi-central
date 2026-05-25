"""Use case leve para a Fase 1 do carregamento progressivo da árvore.

Retorna IGD, departamentos e indicadores apenas para o período atual
(competência + mês anterior para variação), **sem** séries históricas.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from si_app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from si_app.application.use_cases.strategic_indicators.get_departments_tree_use_case import (
    GetStrategicIndicatorsDepartmentsTreeUseCase,
    _TreeScopeConfig,
)
from si_app.application.use_cases.strategic_indicators.get_trends_real_use_case import (
    GetStrategicIndicatorsTrendsRealUseCase,
)


@dataclass(frozen=True)
class GetDepartmentsTreeSnapshotRequest:
    view_mode: str = "consolidated"
    branch: str | None = None
    competence: str | None = None
    start_date: str | None = None
    end_date: str | None = None


_SNAPSHOT_MONTHS = 2


class GetDepartmentsTreeSnapshotUseCase:
    """Fase 1: estrutura da árvore (IGD + departamentos + indicadores)."""

    def __init__(
        self,
        *,
        tree_use_case: GetStrategicIndicatorsDepartmentsTreeUseCase,
        trends_use_case: GetStrategicIndicatorsTrendsRealUseCase,
    ) -> None:
        self._tree = tree_use_case
        self._trends = trends_use_case

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
        trends_request = GetStrategicIndicatorsTrendsRealRequest(
            branch=scope.branch,
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            months=_SNAPSHOT_MONTHS,
        )
        snapshots = self._trends.load_period_snapshots(trends_request)

        current_snapshot = snapshots[-1] if snapshots else None
        previous_snapshot = (
            snapshots[-2]
            if len(snapshots) >= 2
            else (snapshots[-1] if snapshots else None)
        )

        return {
            "scope_key": scope.scope_key,
            "scope_label": scope.scope_label,
            "branch": scope.branch,
            "current_snapshot": current_snapshot,
            "departments": self._tree._map_departments(
                current_snapshot, previous_snapshot
            ),
            "indicators": self._tree._map_indicators(
                current_snapshot, previous_snapshot
            ),
        }
