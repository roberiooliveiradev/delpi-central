"""Use case para a Fase 2 do carregamento progressivo da árvore.

Retorna apenas as séries históricas (trends) para N meses,
sem duplicar departamentos/indicadores.
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
class GetDepartmentsTreeTrendsRequest:
    view_mode: str = "consolidated"
    branch: str | None = None
    competence: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    months: int = 6


class GetDepartmentsTreeTrendsUseCase:
    """Fase 2: séries históricas (sparklines) para a árvore."""

    def __init__(
        self,
        *,
        tree_use_case: GetStrategicIndicatorsDepartmentsTreeUseCase,
        trends_use_case: GetStrategicIndicatorsTrendsRealUseCase,
    ) -> None:
        self._tree = tree_use_case
        self._trends = trends_use_case

    def execute(self, request: GetDepartmentsTreeTrendsRequest) -> dict:
        months = max(2, min(request.months, 12))
        scopes = self._tree._resolve_scopes(request.view_mode, request.branch)

        scope_payloads: list[dict] = []
        with ThreadPoolExecutor(max_workers=min(4, len(scopes))) as executor:
            futures = {
                executor.submit(self._load_scope, request, scope, months): scope
                for scope in scopes
            }
            for future in as_completed(futures):
                scope_payloads.append(future.result())

        scope_payloads.sort(
            key=lambda item: self._tree._scope_sort_key(str(item["scope_key"])),
        )

        return {
            "competence": request.competence,
            "months": months,
            "scopes": [
                {
                    "scope_key": item["scope_key"],
                    "scope_label": item["scope_label"],
                    "branch": item["branch"],
                    "trends": item["trends"],
                }
                for item in scope_payloads
            ],
            "meta": {
                "source": "trends",
                "scope_count": len(scope_payloads),
            },
        }

    def _load_scope(
        self,
        request: GetDepartmentsTreeTrendsRequest,
        scope: _TreeScopeConfig,
        months: int,
    ) -> dict:
        trends_request = GetStrategicIndicatorsTrendsRealRequest(
            branch=scope.branch,
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            months=months,
        )
        snapshots = self._trends.load_period_snapshots(trends_request)
        trends = self._trends.build_response_from_snapshots(snapshots)

        return {
            "scope_key": scope.scope_key,
            "scope_label": scope.scope_label,
            "branch": scope.branch,
            "trends": trends,
        }
