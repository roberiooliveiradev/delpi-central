"""E11.S4 — continuity facets from structured route metadata (not path-tail / inventory).

Authority:
1. ``route.continuityFacets`` (explicit)
2. ``route.intentBinding``
3. ``route.routeSegment`` (legacy field, if present)
4. facet derived from ``route.id`` (camelCase → kebab after product/domain prefix)
5. optional aliases passed by the registry loader (no domain FS/content IO)

No filesystem read of OpenAPI operationId inventory. No path substring authority.
"""

from __future__ import annotations

import re
from typing import Any, Mapping


class RouteSegmentInferenceService:
    """Continuity facet resolver — structured route metadata only."""

    _CAMEL_1 = re.compile(r"(.)([A-Z][a-z]+)")
    _CAMEL_2 = re.compile(r"([a-z0-9])([A-Z])")
    _ID_PREFIXES = ("product", "domain")

    @classmethod
    def path_for_operation_id(cls, operation_id: str | None) -> str | None:
        """Deprecated stub — inventory path lookup removed (E11.S4)."""
        _ = operation_id
        return None

    @classmethod
    def continuity_keys_from_path(cls, path: str | None) -> frozenset[str]:
        """Deprecated stub — path-tail is not continuity authority."""
        _ = path
        return frozenset()

    @classmethod
    def continuity_keys_for_route(
        cls,
        route: dict[str, Any] | None,
        *,
        aliases: Mapping[str, tuple[str, ...]] | None = None,
    ) -> frozenset[str]:
        if not isinstance(route, dict):
            return frozenset()

        keys: set[str] = set()

        declared_facets = route.get("continuityFacets")
        if isinstance(declared_facets, list):
            for item in declared_facets:
                token = str(item or "").strip().lower()
                if token:
                    keys.add(token)

        intent = str(route.get("intentBinding") or "").strip().lower()
        if intent:
            keys.add(intent)

        declared = str(route.get("routeSegment") or "").strip().lower()
        if declared:
            keys.add(declared)

        from_id = cls._facet_from_route_id(str(route.get("id") or ""))
        if from_id:
            keys.add(from_id)

        alias_map = aliases or {}
        expanded = set(keys)
        for key in keys:
            expanded.update(alias_map.get(key, ()))
            for canon, values in alias_map.items():
                if key == canon or key in values:
                    expanded.add(canon)
                    expanded.update(values)
        return frozenset(expanded)

    @classmethod
    def route_matches_segment(
        cls,
        route: dict[str, Any] | None,
        segment: str | None,
        *,
        aliases: Mapping[str, tuple[str, ...]] | None = None,
    ) -> bool:
        normalized = str(segment or "").strip().lower()
        if not normalized:
            return False
        return normalized in cls.continuity_keys_for_route(route, aliases=aliases)

    @classmethod
    def has_product_continuity_segment(
        cls,
        route: dict[str, Any] | None,
        *,
        aliases: Mapping[str, tuple[str, ...]] | None = None,
    ) -> bool:
        if not isinstance(route, dict):
            return False
        match = route.get("match") if isinstance(route.get("match"), dict) else {}
        if bool(match.get("requiresProductIdentifier")):
            return True
        domain = str(route.get("domain") or "").strip().lower()
        if domain in {"product", "domainproductsearch", "product_search"}:
            return True
        return bool(cls.continuity_keys_for_route(route, aliases=aliases))

    @classmethod
    def _facet_from_route_id(cls, route_id: str) -> str:
        token = str(route_id or "").strip()
        if not token:
            return ""
        rest = token
        lowered = token.lower()
        for prefix in cls._ID_PREFIXES:
            if lowered.startswith(prefix) and len(token) > len(prefix):
                boundary = token[len(prefix) : len(prefix) + 1]
                if boundary.isupper() or boundary.isdigit():
                    rest = token[len(prefix) :]
                    break
        return cls._camel_to_kebab(rest)

    @classmethod
    def _camel_to_kebab(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = cls._CAMEL_1.sub(r"\1-\2", text)
        text = cls._CAMEL_2.sub(r"\1-\2", text)
        return text.replace("_", "-").lower().strip("-")


def invalidate_route_segment_inference_cache() -> None:
    """No-op kept for call-site compat (no process cache after E11.S4)."""
    return None
