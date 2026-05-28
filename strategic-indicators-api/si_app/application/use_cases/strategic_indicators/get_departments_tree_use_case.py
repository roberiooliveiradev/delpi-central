from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from si_app.application.dto.strategic_indicators.get_indicators_response import (
    GetStrategicIndicatorsResponse,
)
from si_app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.use_cases.strategic_indicators.get_departments_real_use_case import (
    GetStrategicIndicatorsDepartmentsRealUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_indicators_use_case import (
    GetStrategicIndicatorsUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_trends_real_use_case import (
    GetStrategicIndicatorsTrendsRealUseCase,
)
from si_app.shared.goal_scope import BRANCH_UNIT_CODES, is_branch_unit_scope


@dataclass(frozen=True)
class GetStrategicIndicatorsDepartmentsTreeRequest:
    view_mode: str = "consolidated"
    branch: str | None = None
    competence: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    months: int = 6


@dataclass(frozen=True)
class _TreeScopeConfig:
    scope_key: str
    scope_label: str
    branch: str | None


class GetStrategicIndicatorsDepartmentsTreeUseCase:
    def __init__(
        self,
        *,
        trends_use_case: GetStrategicIndicatorsTrendsRealUseCase,
        departments_use_case: GetStrategicIndicatorsDepartmentsRealUseCase,
        indicators_use_case: GetStrategicIndicatorsUseCase,
    ) -> None:
        self._trends_use_case = trends_use_case
        self._departments_use_case = departments_use_case
        self._indicators_use_case = indicators_use_case

    def execute(
        self,
        request: GetStrategicIndicatorsDepartmentsTreeRequest | None = None,
    ) -> dict:
        request = request or GetStrategicIndicatorsDepartmentsTreeRequest()
        months = max(2, min(request.months, 12))
        scopes = self._resolve_scopes(request.view_mode, request.branch)

        scope_payloads: list[dict] = []
        with ThreadPoolExecutor(max_workers=min(4, len(scopes))) as executor:
            futures = {
                executor.submit(self._load_scope, request, scope, months): scope
                for scope in scopes
            }
            for future in as_completed(futures):
                scope_payloads.append(future.result())

        scope_payloads.sort(
            key=lambda item: self._scope_sort_key(str(item["scope_key"])),
        )

        primary = next(
            (item for item in scope_payloads if item["scope_key"] == "consolidated"),
            scope_payloads[0] if scope_payloads else None,
        )
        current_snapshot = (
            primary.get("current_snapshot") if primary is not None else None
        )
        if primary is None or current_snapshot is None:
            return {
                "competence": request.competence,
                "igd": None,
                "igd_exact": None,
                "classification": None,
                "months": months,
                "scopes": [
                    {
                        "scope_key": item["scope_key"],
                        "scope_label": item["scope_label"],
                        "branch": item["branch"],
                        "departments": item["departments"],
                        "indicators": item["indicators"],
                        "trends": item["trends"],
                    }
                    for item in scope_payloads
                ],
                "meta": {"source": "snapshot_series", "scope_count": len(scope_payloads)},
            }

        return {
            "competence": primary["trends"]["competence"],
            "igd": current_snapshot.igd,
            "igd_exact": current_snapshot.igd_exact,
            "classification": current_snapshot.classification,
            "months": months,
            "scopes": [
                {
                    "scope_key": item["scope_key"],
                    "scope_label": item["scope_label"],
                    "branch": item["branch"],
                    "departments": item["departments"],
                    "indicators": item["indicators"],
                    "trends": item["trends"],
                }
                for item in scope_payloads
            ],
            "meta": {
                "source": "snapshot_series",
                "scope_count": len(scope_payloads),
            },
        }

    def _load_scope(
        self,
        request: GetStrategicIndicatorsDepartmentsTreeRequest,
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
        snapshots = self._trends_use_case.load_period_snapshots(trends_request)
        trends = self._trends_use_case.build_response_from_snapshots(snapshots)

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
            "departments": self._map_departments(current_snapshot, previous_snapshot),
            "indicators": self._map_indicators(current_snapshot, previous_snapshot),
            "trends": trends,
        }

    def _map_departments(
        self,
        current: StrategicIndicatorsPeriodSnapshot | None,
        previous: StrategicIndicatorsPeriodSnapshot | None,
    ) -> dict:
        if current is None:
            return {"items": [], "errors": [], "partial_success": False}

        previous_by_id = {
            item.department_id: item for item in previous.calculated_departments
        } if previous is not None else {}

        return {
            "items": [
                self._departments_use_case._map_department(
                    current=item,
                    previous=previous_by_id.get(item.department_id),
                )
                for item in current.calculated_departments
            ],
            "errors": current.measurement_errors,
            "partial_success": len(current.measurement_errors) > 0,
        }

    def _map_indicators(
        self,
        current: StrategicIndicatorsPeriodSnapshot | None,
        previous: StrategicIndicatorsPeriodSnapshot | None,
        *,
        catalog=None,
    ) -> dict:
        if current is None:
            return {"items": [], "errors": [], "partial_success": False}

        response = self._indicators_use_case.build_from_period_snapshot(
            current,
            previous_snapshot=previous,
            catalog=catalog,
            compact=True,
        )
        return self._serialize_indicators_response(response, compact=True)

    @staticmethod
    def _serialize_indicators_response(
        result: GetStrategicIndicatorsResponse,
        *,
        compact: bool = False,
    ) -> dict:
        return {
            "items": [
                {
                    "department_id": item.department_id,
                    "department_name": item.department_name,
                    "indicator_id": item.indicator_id,
                    "indicator_name": item.indicator_name,
                    "weight_pct": item.weight_pct,
                    "goal_label": item.goal_label,
                    "goal_value": float(item.goal_value)
                    if item.goal_value is not None
                    else None,
                    "goal_periodicity": item.goal_periodicity,
                    "goal_mode": getattr(item, "goal_mode", "standard"),
                    **(
                        {}
                        if compact
                        else {
                            "monthly_targets": [
                                {
                                    **target,
                                    "target_value": float(target["target_value"])
                                    if target.get("target_value") is not None
                                    else None,
                                }
                                if isinstance(target, dict)
                                else target
                                for target in (getattr(item, "monthly_targets", []) or [])
                            ],
                        }
                    ),
                    "scope_type": item.scope_type,
                    "performance_direction": getattr(
                        item,
                        "performance_direction",
                        "higher_is_better",
                    ),
                    "value": float(item.value) if item.value is not None else None,
                    "realized": {
                        key: float(value) if value is not None else None
                        for key, value in (item.realized or {}).items()
                    },
                    "score": float(item.score) if item.score is not None else None,
                    "gap": float(item.gap) if item.gap is not None else None,
                    "gaps": {
                        key: float(value) if value is not None else None
                        for key, value in (item.gaps or {}).items()
                    },
                    "goals": {
                        key: float(value) if value is not None else None
                        for key, value in (getattr(item, "goals", None) or {}).items()
                    },
                    "has_value": item.has_value,
                    "trend": item.trend,
                    "classification": item.classification,
                    "source": item.source,
                    "value_unit": getattr(item, "value_unit", None),
                    "value_prefix": getattr(item, "value_prefix", None),
                    "value_suffix": getattr(item, "value_suffix", None),
                    "value_decimals": getattr(item, "value_decimals", 2),
                }
                for item in result.items
            ],
            "errors": [
                {
                    "department_id": error.department_id,
                    "source": error.source,
                    "message": error.message,
                }
                for error in result.errors
            ],
            "partial_success": result.partial_success,
        }

    def _resolve_scopes(
        self,
        view_mode: str,
        branch: str | None,
    ) -> list[_TreeScopeConfig]:
        normalized_mode = (view_mode or "consolidated").strip().lower()
        normalized_branch = (branch or "").strip()

        if normalized_mode == "branch" and normalized_branch:
            scope_key = (
                normalized_branch
                if is_branch_unit_scope(normalized_branch)
                else BRANCH_UNIT_CODES[0]
            )
            return [
                _TreeScopeConfig(
                    scope_key=scope_key,
                    scope_label=f"Filial {normalized_branch}",
                    branch=scope_key,
                )
            ]

        return [
            _TreeScopeConfig(
                scope_key="consolidated",
                scope_label="Consolidado",
                branch=None,
            ),
        ]

    @staticmethod
    def _scope_sort_key(scope_key: str) -> int:
        order = {"consolidated": 0, "01": 1, "02": 2}
        return order.get(scope_key, 99)
