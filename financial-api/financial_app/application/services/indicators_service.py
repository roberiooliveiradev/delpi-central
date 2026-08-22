from __future__ import annotations

from typing import Any

from financial_app.application.services.content_loader import load_content
from financial_app.application.services.payload_mapping import (
    as_float,
    as_int,
    as_opt_float,
    as_opt_str,
    as_str,
    unwrap_data,
)
from financial_app.application.services.response_cache import cached_fetch
from financial_app.core.security import FIN_INDICATORS_VIEW
from financial_app.domain.errors import StrategicIndicatorsGatewayError
from financial_app.domain.ports.strategic_indicators_gateway import StrategicIndicatorsGatewayPort
from financial_app.domain.services.branch_access_service import BranchAccessService


def _settings() -> dict[str, Any]:
    return load_content("indicators.json")


class IndicatorsService:
    def __init__(
        self,
        gateway: StrategicIndicatorsGatewayPort,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def department(
        self,
        user: object | None,
        *,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        self._branch_access.assert_can_use(user, FIN_INDICATORS_VIEW)
        gateway_branch = (
            self._branch_access.resolve_branch_scope(user, branch) if branch is not None else None
        )
        cfg = _settings()
        department_id = str(cfg.get("departmentId") or "financial")
        try:
            payload = self._cached(
                "department",
                {
                    "branch": gateway_branch,
                    "competence": competence,
                    "start": start_date,
                    "end": end_date,
                    "dept": department_id,
                },
                lambda: unwrap_data(
                    self._gateway.fetch_department_indicators(
                        department_id=department_id,
                        competence=competence,
                        start_date=start_date,
                        end_date=end_date,
                        branch=gateway_branch,
                    )
                ),
                refresh=refresh,
            )
        except StrategicIndicatorsGatewayError as exc:
            return self._unavailable("departmentUnavailable", exc)

        item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
        if not isinstance(item, dict) or not item:
            return {
                "available": False,
                "reason": str((cfg.get("messages") or {}).get("notPublished") or ""),
                "detail": None,
            }

        partial = bool(item.get("partial_success") or item.get("partialSuccess"))
        notice = str((cfg.get("messages") or {}).get("partialSuccess") or "") if partial else None
        return {
            "available": True,
            "departmentId": as_str(item.get("department_id") or item.get("departmentId")),
            "departmentName": as_str(item.get("department_name") or item.get("departmentName")),
            "shortName": as_str(item.get("short_name") or item.get("shortName")),
            "idd": as_float(item.get("idd") if item.get("idd") is not None else item.get("score")),
            "classification": as_opt_str(item.get("classification")),
            "contribution": as_opt_float(item.get("contribution")),
            "aggregationMode": as_opt_str(
                item.get("aggregation_mode") or item.get("aggregationMode")
            ),
            "partialSuccess": partial,
            "notice": notice,
            "indicators": [
                self._map_indicator(row)
                for row in item.get("indicators") or []
                if isinstance(row, dict)
            ],
        }

    def global_score(
        self,
        user: object | None,
        *,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        self._branch_access.assert_can_use(user, FIN_INDICATORS_VIEW)
        gateway_branch = (
            self._branch_access.resolve_branch_scope(user, branch) if branch is not None else None
        )
        try:
            payload = self._cached(
                "global",
                {
                    "branch": gateway_branch,
                    "competence": competence,
                    "start": start_date,
                    "end": end_date,
                },
                lambda: unwrap_data(
                    self._gateway.fetch_global_score(
                        competence=competence,
                        start_date=start_date,
                        end_date=end_date,
                        branch=gateway_branch,
                    )
                ),
                refresh=refresh,
            )
        except StrategicIndicatorsGatewayError as exc:
            return self._unavailable("globalUnavailable", exc)

        return {
            "available": True,
            "igd": as_opt_float(payload.get("igd")),
            "classification": as_opt_str(payload.get("classification")),
            "trendDirection": as_opt_str(
                payload.get("trendDirection") or payload.get("trend_direction")
            ),
            "bestDepartment": as_opt_str(
                payload.get("bestDepartment") or payload.get("best_department")
            ),
            "primaryRisk": as_opt_str(payload.get("primaryRisk") or payload.get("primary_risk")),
            "competence": as_opt_str(payload.get("competence")),
        }

    def _cached(
        self,
        kind: str,
        parts: dict[str, Any],
        loader,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        ttl = as_int((_settings().get("cacheTtlSeconds") or {}).get(kind), 0)
        key = f"indicators:{kind}:{sorted(parts.items())}"
        return cached_fetch(key, ttl, loader, refresh=refresh)

    @staticmethod
    def _unavailable(message_key: str, exc: Exception) -> dict[str, Any]:
        messages = _settings().get("messages") or {}
        return {
            "available": False,
            "reason": str(messages.get(message_key) or ""),
            "detail": str(exc),
        }

    @staticmethod
    def _map_indicator(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "indicatorId": as_str(item.get("indicator_id") or item.get("indicatorId")),
            "name": as_str(item.get("name")),
            "weightPct": as_float(item.get("weight_pct") or item.get("weightPct")),
            "goalLabel": as_opt_str(item.get("goal_label") or item.get("goalLabel")),
            "goalValue": as_float(item.get("goal_value") or item.get("goalValue")),
            "goalPeriodicity": as_opt_str(
                item.get("goal_periodicity") or item.get("goalPeriodicity")
            ),
            "goalMode": as_opt_str(item.get("goal_mode") or item.get("goalMode")),
            "performanceDirection": as_opt_str(
                item.get("performance_direction") or item.get("performanceDirection")
            ),
            "value": as_float(item.get("value")),
            "hasValue": bool(item.get("has_value") if "has_value" in item else item.get("hasValue", True)),
            "score": as_float(item.get("score")),
            "gap": as_float(item.get("gap")),
            "classification": as_opt_str(item.get("classification")),
            "valueUnit": as_opt_str(item.get("value_unit") or item.get("valueUnit")),
            "valuePrefix": as_opt_str(item.get("value_prefix") or item.get("valuePrefix")),
            "valueSuffix": as_opt_str(item.get("value_suffix") or item.get("valueSuffix")),
            "valueDecimals": as_int(item.get("value_decimals") or item.get("valueDecimals"), 2),
        }
