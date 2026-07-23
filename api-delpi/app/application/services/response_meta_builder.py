"""Metadados semânticos do envelope api-delpi (Fase 3)."""

from __future__ import annotations

from typing import Any

DATA_VERSION = "2026-07"


class ResponseMetaBuilder:
    @staticmethod
    def build(
        *,
        operation_id: str,
        entity: str,
        shape: str,
        pagination: dict[str, Any] | None = None,
        fields: dict[str, str] | None = None,
        field_formats: dict[str, str] | None = None,
        related_routes: dict[str, str] | None = None,
        sections: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "dataVersion": DATA_VERSION,
            "operationId": operation_id,
            "entity": entity,
            "shape": shape,
        }
        if pagination is not None:
            meta["pagination"] = pagination
        if fields:
            meta["fields"] = fields
        if field_formats:
            meta["fieldFormats"] = field_formats
        if related_routes:
            meta["relatedRoutes"] = related_routes
        if sections:
            meta["sections"] = sections
        return meta

    @staticmethod
    def pagination_from_data(data: Any) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None

        operational = data.get("pagination")
        if isinstance(operational, dict) and "returned" in operational:
            payload: dict[str, Any] = {}
            for key in ("limit", "offset", "returned", "total", "is_complete"):
                if key in operational:
                    payload[key] = operational[key]
            return payload or None

        required = ("page", "page_size", "total")
        if not all(key in data for key in required):
            return None
        payload = {
            "page": data.get("page"),
            "page_size": data.get("page_size"),
            "total": data.get("total"),
        }
        if "total_pages" in data:
            payload["total_pages"] = data.get("total_pages")
        return payload

    @staticmethod
    def infer_shape(data: Any) -> str:
        if isinstance(data, list):
            return "paged_list" if not data else "scalar"
        if not isinstance(data, dict):
            return "scalar"
        if "product" in data and isinstance(data.get("product"), dict):
            if any(key in data for key in ("structure", "guide", "inspection", "sections")):
                return "composite_analysis"
            return "product_snapshot"
        if "root" in data and "items" in data:
            return "hierarchy"
        if "items" in data and "summary" in data:
            return "playbook_report"
        if ResponseMetaBuilder.pagination_from_data(data) is not None:
            return "paged_list"
        if "items" in data and isinstance(data.get("items"), list):
            return "paged_list"
        if any(key in data for key in ("structure", "production", "shipping")):
            return "composite_analysis"
        return "scalar"

    @staticmethod
    def product_related_routes(code: str) -> dict[str, str]:
        return {
            "detail": f"/products/{code}",
            "summary": f"/products/{code}/summary",
            "stock": f"/products/{code}/stock",
            "structure": f"/products/{code}/structure",
            "analyser": f"/products/{code}/analyser",
            "factoryStatus": f"/products/{code}/factory-status",
        }

    @staticmethod
    def lmp_related_routes(
        sale_number: str,
        *,
        branch: str | None = None,
    ) -> dict[str, str]:
        normalized = str(sale_number).strip()
        branch_suffix = f"?branch={branch}" if branch else ""
        return {
            "detail": f"/engineering/lmps/{normalized}{branch_suffix}",
            "historyEvents": f"/engineering/lmps/{normalized}/history/events{branch_suffix}",
            "historyFlow": f"/engineering/lmps/{normalized}/history/flow{branch_suffix}",
            "dashboardItems": "/engineering/lmps/dashboard/items",
            "dashboardSummary": "/engineering/lmps/dashboard/summary",
            "dashboardCharts": "/engineering/lmps/dashboard/charts",
            "list": "/engineering/lmps",
        }
