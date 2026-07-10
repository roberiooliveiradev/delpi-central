from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROUTES_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_data_routes.json"

DATA_BLOCK_TYPES = frozenset({"data_kpi", "data_chart", "data_table", "data_metric", "data_source"})
DATA_VIEW_BLOCK_TYPES = frozenset({"chart_view", "table_view"})
FETCHABLE_DATA_BLOCK_TYPES = DATA_BLOCK_TYPES


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))


class TvDataRouteCatalogService:
    """Allowlist de rotas api-delpi disponíveis para blocos data_* na TV."""

    def list_routes(self) -> list[dict[str, Any]]:
        raw = _load_catalog().get("routes") or []
        if not isinstance(raw, list):
            return []
        return [dict(item) for item in raw if isinstance(item, dict)]

    def get_route(self, operation_id: str) -> dict[str, Any] | None:
        op = str(operation_id or "").strip()
        if not op:
            return None
        for route in self.list_routes():
            if str(route.get("operationId") or "") == op:
                return route
        return None

    def is_allowed(self, operation_id: str) -> bool:
        return self.get_route(operation_id) is not None

    @staticmethod
    def is_data_block(block: dict[str, Any]) -> bool:
        return str(block.get("type") or "") in DATA_BLOCK_TYPES

    @staticmethod
    def is_data_view_block(block: dict[str, Any]) -> bool:
        return str(block.get("type") or "") in DATA_VIEW_BLOCK_TYPES


def reset_tv_data_route_catalog_cache() -> None:
    _load_catalog.cache_clear()
