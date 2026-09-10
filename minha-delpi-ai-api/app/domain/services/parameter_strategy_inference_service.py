"""E9.S12.E — infer parameter strategy from OpenAPI action (path/operationId/schema).

Registry JSON `parameters.strategy` is no longer authority after cutover.
"""

from __future__ import annotations

from typing import Any


class ParameterStrategyInferenceService:
    """Deriva strategy canônica sem ler JSON do registry."""

    @classmethod
    def infer_from_action(
        cls,
        action: dict[str, Any] | None,
        *,
        route: dict[str, Any] | None = None,
    ) -> str:
        # Compat: rotas virtuais/testes ainda podem declarar strategy.
        if isinstance(route, dict):
            declared = str((route.get("parameters") or {}).get("strategy") or "").strip()
            if declared:
                return declared

        payload = action if isinstance(action, dict) else {}
        path = str(payload.get("path") or "").strip().lower()
        operation_id = str(payload.get("operationId") or "").strip().lower()

        if not path and isinstance(route, dict):
            # Fallback: first operationId of route + empty path heuristics via oid only.
            route_spec = route.get("route") if isinstance(route.get("route"), dict) else {}
            ids = route_spec.get("operationIds") or []
            if ids:
                operation_id = str(ids[0] or "").strip().lower() or operation_id

        return cls.infer_from_path(path, operation_id=operation_id)

    @classmethod
    def infer_from_path(cls, path: str, *, operation_id: str = "") -> str:
        lowered = str(path or "").strip().lower()
        oid = str(operation_id or "").strip().lower()

        if "by-supplier-part-number" in lowered or "supplier_part_number" in oid:
            return "supplier_part_number"

        if "exclusive-raw-materials" in lowered or "exclusive_raw_material" in oid:
            return "exclusive_catalog"

        if "/system/" in lowered or "protheus" in oid:
            return "system_metadata"

        if (
            "department-idd" in lowered
            or "department-indicators" in lowered
            or "departments-indicators" in lowered
            or "department_idd" in oid
            or "department_indicators" in oid
            or "departments_indicators" in oid
        ):
            return "department_idd"

        if "/products/" in lowered and "search" in lowered:
            return "product_search"

        if (
            "sale_order" in oid
            or "sale-orders" in lowered
            or "totvs-open-orders" in lowered
            or oid == "list_sale_orders"
        ):
            return "sale_orders"

        if "safety-stock" in lowered:
            if "{code}" in lowered or (oid.endswith("_item_details") or "item_details" in oid):
                if "details" in lowered or "items/{code}" in lowered or "item_details" in oid:
                    return "product_code"
            return "supplies_stock"

        if (
            "stock-balances" in lowered
            or "stock-value" in lowered
            or "stock_value" in oid
            or "stock_balances" in oid
        ):
            return "supplies_stock"

        if "lmps/dashboard/summary" in lowered or oid == "get_lmps_dashboard_summary":
            return "date_branch"

        if "/lmps" in lowered or "lmp" in oid:
            return "lmp"

        if "/products/" in lowered:
            return "product_code"

        if any(
            token in lowered
            for token in (
                "/production/",
                "/purchases/",
                "/dashboard/",
                "/supplies/",
                "/commercial/",
                "/engineering/",
                "eficiencia",
                "/kpi",
            )
        ):
            return "date_branch"

        return "none"
