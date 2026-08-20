from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from production_control_app.core.security import PC_PROBLEM_ANALYSIS_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "problem_analysis.json"


@lru_cache(maxsize=1)
def _settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


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


def _severity(delay_days: int, critical_days: int) -> str:
    if delay_days >= critical_days:
        return "critical"
    return "attention"


def map_delayed_order(item: dict[str, Any], *, critical_days: int, title_template: str) -> dict[str, Any]:
    order = str(item.get("production_order") or "").strip()
    op_key = str(item.get("op_key") or "").strip() or order
    delay_days = _as_int(item.get("days_late"), 0)
    title = title_template.format(order=order or op_key, days=delay_days)
    return {
        "id": f"delayed-order:{op_key}",
        "kind": "delayed_order",
        "severity": _severity(delay_days, critical_days),
        "title": title,
        "product_code": str(item.get("product_code") or "").strip() or None,
        "product_description": str(item.get("product_description") or item.get("description") or "").strip()
        or None,
        "production_order": order or None,
        "op_key": op_key or None,
        "work_center": str(item.get("work_center") or "").strip() or None,
        "delay_days": delay_days,
        "branch": str(item.get("branch") or "").strip() or None,
        "metrics": {
            "planned_qty": _as_float(item.get("planned_qty")),
            "produced_qty": _as_float(item.get("produced_qty")),
            "pending_qty": _as_float(item.get("pending_qty")),
            "warehouse": str(item.get("warehouse") or "").strip() or None,
            "delivery_date": str(
                item.get("due_date") or item.get("delivery_date") or item.get("dt_entrega") or ""
            ).strip()
            or None,
            "has_balance": item.get("has_balance"),
            "is_open": item.get("is_open"),
        },
    }


class ProblemAnalysisService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def build(
        self,
        user: object | None,
        *,
        branch: str,
        issue_id: str | None = None,
    ) -> dict[str, Any]:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_PROBLEM_ANALYSIS_VIEW):
            raise PermissionError("Você não tem permissão para análise de problemas.")

        cfg = _settings()
        critical_days = _as_int(cfg.get("criticalDelayDays"), 7)
        page_size = _as_int(cfg.get("pageSize"), 100)
        titles = cfg.get("titles") if isinstance(cfg.get("titles"), dict) else {}
        title_template = str(titles.get("delayedOrder") or "OP {order} atrasada ({days} dias)")

        try:
            items_payload = _unwrap_data(
                self._gateway.fetch_pcp_orders_items(
                    branch=branch,
                    delayed_only=True,
                    page_size=page_size,
                )
            )
            summary_payload = _unwrap_data(self._gateway.fetch_pcp_orders_summary(branch=branch))
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError("Não foi possível consultar as ordens PCP.") from exc

        raw_items = items_payload.get("items")
        if not isinstance(raw_items, list):
            raw_items = []

        issues = [
            map_delayed_order(item, critical_days=critical_days, title_template=title_template)
            for item in raw_items
            if isinstance(item, dict)
        ]
        issues.sort(key=lambda row: (-int(row.get("delay_days") or 0), str(row.get("id"))))

        critical = sum(1 for row in issues if row["severity"] == "critical")
        attention = sum(1 for row in issues if row["severity"] == "attention")
        totvs_summary = summary_payload.get("summary") if isinstance(summary_payload.get("summary"), dict) else {}
        open_orders = _as_int(totvs_summary.get("open_orders"), 0)
        delayed_orders = _as_int(totvs_summary.get("delayed_orders"), len(issues))
        ok_count = max(0, open_orders - delayed_orders)

        selected_id = (issue_id or "").strip()
        selected = next((row for row in issues if row["id"] == selected_id), None)
        if selected is None and issues:
            selected = issues[0]

        return {
            "branch": branch,
            "summary": {
                "critical": critical,
                "attention": attention,
                "ok": ok_count,
                "issue_count": len(issues),
            },
            "issues": issues,
            "selected": selected,
        }
