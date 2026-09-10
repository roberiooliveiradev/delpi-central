"""E9.S12.D — continuity segment keys derived from OpenAPI paths (operationIds).

Registry JSON `routeSegment` is no longer authority after cutover.
Runtime continuity keys (e.g. open-orders, inbound-invoice) may differ from
path tails (sales/open-orders, inbound-invoice-items); matching normalizes both.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


def invalidate_route_segment_inference_cache() -> None:
    _operation_id_to_path.cache_clear()


@lru_cache(maxsize=1)
def _operation_id_to_path() -> dict[str, str]:
    inventory_path = (
        Path(__file__).resolve().parents[4]
        / "api-delpi"
        / "app"
        / "content"
        / "openapi_operation_id_inventory.json"
    )
    if not inventory_path.is_file():
        return {}

    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    operations = payload.get("operations") if isinstance(payload, dict) else None
    if not isinstance(operations, list):
        return {}

    mapping: dict[str, str] = {}
    for row in operations:
        if not isinstance(row, dict):
            continue
        operation_id = str(row.get("operationId") or "").strip()
        path = str(row.get("path") or "").strip()
        if operation_id and path:
            mapping[operation_id] = path
    return mapping


class RouteSegmentInferenceService:
    """Deriva chaves de continuidade product-path sem ler `route.routeSegment`."""

    _PATH_SUFFIXES = ("-items", "-item", "-summary")
    _CODE_RE = re.compile(r"^\d{5,}$")

    @classmethod
    def path_for_operation_id(cls, operation_id: str | None) -> str | None:
        target = str(operation_id or "").strip()
        if not target:
            return None
        return _operation_id_to_path().get(target)

    @classmethod
    def continuity_keys_from_path(cls, path: str | None) -> frozenset[str]:
        parts = [part for part in str(path or "").lower().strip("/").split("/") if part]
        if not parts or parts[0] != "products":
            return frozenset()

        rest = parts[1:]
        if not rest:
            return frozenset()

        keys: set[str] = set()

        if len(rest) == 1:
            if not cls._is_placeholder(rest[0]):
                keys.add(rest[0])
            return frozenset(keys)

        if cls._is_placeholder(rest[0]) or cls._looks_like_code(rest[0]):
            tail_parts = rest[1:]
        elif cls._is_placeholder(rest[-1]):
            # /products/directives/{identifier}
            tail_parts = rest[:-1]
        else:
            tail_parts = rest

        if not tail_parts:
            return frozenset(keys)

        keys.add("/".join(tail_parts))
        keys.add(tail_parts[-1])

        last = tail_parts[-1]
        for suffix in cls._PATH_SUFFIXES:
            if last.endswith(suffix) and len(last) > len(suffix):
                keys.add(last[: -len(suffix)])

        return frozenset(keys)

    @classmethod
    def continuity_keys_for_route(cls, route: dict[str, Any] | None) -> frozenset[str]:
        if not isinstance(route, dict):
            return frozenset()

        keys: set[str] = set()

        # Compat: declared field still honored if present (tests / transitional).
        declared = str(route.get("routeSegment") or "").strip().lower()
        if declared:
            keys.add(declared)

        route_spec = route.get("route") if isinstance(route.get("route"), dict) else {}
        for item in route_spec.get("operationIds") or []:
            path = cls.path_for_operation_id(str(item or "").strip())
            if path:
                keys.update(cls.continuity_keys_from_path(path))

        return frozenset(keys)

    @classmethod
    def route_matches_segment(
        cls,
        route: dict[str, Any] | None,
        segment: str | None,
    ) -> bool:
        normalized = str(segment or "").strip().lower()
        if not normalized:
            return False
        return normalized in cls.continuity_keys_for_route(route)

    @classmethod
    def has_product_continuity_segment(cls, route: dict[str, Any] | None) -> bool:
        return bool(cls.continuity_keys_for_route(route))

    @staticmethod
    def _is_placeholder(token: str) -> bool:
        return token.startswith("{") and token.endswith("}")

    @classmethod
    def _looks_like_code(cls, token: str) -> bool:
        return bool(cls._CODE_RE.fullmatch(token))
