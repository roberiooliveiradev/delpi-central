from __future__ import annotations
from typing import Any

class ResponseMetaBuilder:
    @staticmethod
    def infer_shape(data: Any) -> str:
        if isinstance(data, dict) and "items" in data:
            return "paged_list"
        return "scalar"

    @staticmethod
    def pagination_from_data(data: Any) -> dict | None:
        if not isinstance(data, dict):
            return None
        if "page" in data and "page_size" in data:
            return {
                "page": data.get("page"),
                "page_size": data.get("page_size"),
                "total": data.get("total"),
                "total_pages": data.get("total_pages"),
            }
        return None

    @staticmethod
    def product_related_routes(code: str | None) -> None:
        return None

    @staticmethod
    def build(*, operation_id: str, entity: str, shape: str, pagination=None, fields=None, field_formats=None, related_routes=None, sections=None) -> dict:
        meta = {
            "dataVersion": "2026-07",
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
