from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from production_control_app.application.services.problem_analysis_service import (
    map_delayed_order,
)
from production_control_app.core.security import PC_ACCESS, can
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.current_month_period import current_month_bounds
from production_control_app.domain.services.product_code_scope import product_code_matches_prefixes

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "overview.json"
_PROBLEM_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "problem_analysis.json"


@lru_cache(maxsize=1)
def _overview_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _problem_settings() -> dict[str, Any]:
    return json.loads(_PROBLEM_CONTENT_PATH.read_text(encoding="utf-8"))


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data
    return payload if isinstance(payload, dict) else {}


def _series_value(point: dict[str, Any], branch: str) -> float | None:
    key = "otd_filial_02" if branch == "02" else "otd_filial_01"
    value = _as_float(point.get(key))
    if value is not None:
        return value
    fallback = _as_float(point.get("otd_filial_01"))
    if fallback is not None:
        return fallback
    return _as_float(point.get("otd_filial_02"))


def _series_label(point: dict[str, Any]) -> str:
    start = str(point.get("start_date") or "").strip()
    if len(start) >= 10:
        return f"{start[8:10]}/{start[5:7]}"
    return str(point.get("periodo") or start or "").strip()


class OverviewService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def build(self, user: object | None, *, branch: str) -> dict[str, Any]:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")

        cfg = _overview_settings()
        problem_cfg = _problem_settings()
        timezone = str(cfg.get("timezone") or "America/Sao_Paulo")
        granularity = str(cfg.get("seriesGranularity") or "day")
        delayed_page = _as_int(cfg.get("delayedListPageSize"), 100)
        otd_page = _as_int(cfg.get("otdOrdersPageSize"), 1)
        raw_prefixes = cfg.get("delayedProductCodePrefixes")
        prefixes = [str(item).strip() for item in raw_prefixes] if isinstance(raw_prefixes, list) else ["8", "9"]
        critical_days = _as_int(problem_cfg.get("criticalDelayDays"), 7)
        titles = problem_cfg.get("titles") if isinstance(problem_cfg.get("titles"), dict) else {}
        title_template = str(titles.get("delayedOrder") or "OP {order} atrasada ({days} dias)")

        start, end = current_month_bounds(timezone=timezone)
        start_s = start.isoformat()
        end_s = end.isoformat()

        try:
            otd_payload = _unwrap_data(
                self._gateway.fetch_production_otd(
                    branch=branch,
                    start_date=start_s,
                    end_date=end_s,
                    page_size=otd_page,
                )
            )
            series_payload = _unwrap_data(
                self._gateway.fetch_production_otd_series(
                    branch=branch,
                    start_date=start_s,
                    end_date=end_s,
                    granularity=granularity,
                )
            )
            items_payload = _unwrap_data(
                self._gateway.fetch_pcp_orders_items(
                    branch=branch,
                    delayed_only=True,
                    page_size=delayed_page,
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError("Não foi possível montar a gestão à vista do PCP.") from exc

        otd_summary = otd_payload.get("summary") if isinstance(otd_payload.get("summary"), dict) else {}

        raw_points = series_payload.get("points")
        if not isinstance(raw_points, list):
            raw_points = []
        series = []
        for point in raw_points:
            if not isinstance(point, dict):
                continue
            series.append(
                {
                    "label": _series_label(point),
                    "value": _series_value(point, branch),
                    "start_date": str(point.get("start_date") or "").strip() or None,
                    "end_date": str(point.get("end_date") or "").strip() or None,
                }
            )

        raw_items = items_payload.get("items")
        if not isinstance(raw_items, list):
            raw_items = []
        delayed_orders: list[dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            mapped = map_delayed_order(item, critical_days=critical_days, title_template=title_template)
            if product_code_matches_prefixes(mapped.get("product_code"), prefixes):
                delayed_orders.append(mapped)
        delayed_orders.sort(key=lambda row: (-int(row.get("delay_days") or 0), str(row.get("id"))))

        delayed_count = len(delayed_orders)

        return {
            "branch": branch,
            "period": {
                "start_date": start_s,
                "end_date": end_s,
                "granularity": granularity,
            },
            "otd": {
                "on_time_delivery_pct": _as_float(otd_summary.get("on_time_delivery_pct")),
                "late_ops": _as_int(otd_summary.get("late_ops"), 0),
                "on_time_ops": _as_int(otd_summary.get("on_time_ops"), 0),
                "total_ops_finished": _as_int(otd_summary.get("total_ops_finished"), 0),
                "late_percentage": _as_float(otd_summary.get("late_percentage")),
                "series": series,
            },
            "delayed_ops": {
                "count": delayed_count,
                "late_percentage": _as_float(otd_summary.get("late_percentage")),
                "items": delayed_orders,
            },
        }
