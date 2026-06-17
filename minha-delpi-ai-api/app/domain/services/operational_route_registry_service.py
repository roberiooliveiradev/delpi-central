"""Catálogo declarativo de rotas operacionais (DOCIE — Fase 0)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def invalidate_operational_route_registry_cache() -> None:
    _registry_content.cache_clear()


@lru_cache(maxsize=1)
def _registry_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("operational_route_registry")


class OperationalRouteRegistryService:
    @classmethod
    def version(cls) -> str:
        return str(_registry_content().get("version") or "").strip()

    @classmethod
    def dispatch_order(cls) -> list[str]:
        order = _registry_content().get("dispatchOrder")

        if not isinstance(order, list):
            return []

        return [str(item).strip() for item in order if str(item).strip()]

    @classmethod
    def routes(cls) -> list[dict[str, Any]]:
        routes = _registry_content().get("routes")

        if not isinstance(routes, list):
            return []

        normalized = [route for route in routes if isinstance(route, dict)]

        return sorted(
            normalized,
            key=lambda route: int(route.get("priority") or 0),
            reverse=True,
        )

    @classmethod
    def route_by_production_operational_kind(cls, kind: str) -> dict[str, Any] | None:
        target = str(kind or "").strip()

        if not target:
            return None

        for route in cls.routes():
            if str(route.get("productionOperationalKind") or "").strip() == target:
                return route

        return None

    @classmethod
    def route_by_id(cls, route_id: str) -> dict[str, Any] | None:
        target = str(route_id or "").strip()

        if not target:
            return None

        for route in cls.routes():
            if str(route.get("id") or "").strip() == target:
                return route

        return None

    @classmethod
    def route_ids(cls) -> list[str]:
        return [
            str(route.get("id") or "").strip()
            for route in cls.routes()
            if str(route.get("id") or "").strip()
        ]

    @classmethod
    def vocabulary_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if isinstance(route, dict)
            and str(route.get("domain") or "").strip() != "productionOperational"
            and (
                not route.get("intentBinding")
                or (
                    isinstance(route.get("match"), dict)
                    and str(route["match"].get("customPredicate") or "").strip()
                )
            )
        ]

    @classmethod
    def production_operational_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "productionOperational"
        ]

    @classmethod
    def routes_by_segment(cls, segment: str) -> list[dict[str, Any]]:
        normalized = str(segment or "").strip().lower()

        if not normalized:
            return []

        return [
            route
            for route in cls.routes()
            if str(route.get("routeSegment") or "").strip().lower() == normalized
        ]

    @classmethod
    def system_metadata_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "domainSystem"
        ]

    @classmethod
    def lmp_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "domainLmp"
        ]

    @classmethod
    def product_search_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "domainProductSearch"
        ]

    @classmethod
    def product_identifier_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "product"
            and isinstance(route.get("match"), dict)
            and route["match"].get("requiresProductIdentifier")
        ]

    @classmethod
    def intent_bound_routes(cls) -> list[dict[str, Any]]:
        routes = _registry_content().get("routes")

        if not isinstance(routes, list):
            return []

        return [
            route
            for route in routes
            if isinstance(route, dict) and str(route.get("intentBinding") or "").strip()
        ]

    @classmethod
    def actionable_product_predicates(cls) -> list[str]:
        predicates = _registry_content().get("actionableProductPredicates")

        if not isinstance(predicates, list):
            return []

        return [str(item).strip() for item in predicates if str(item).strip()]

    @classmethod
    def playbook_product_predicates(cls) -> list[str]:
        predicates = _registry_content().get("playbookProductPredicates")

        if not isinstance(predicates, list):
            return []

        return [str(item).strip() for item in predicates if str(item).strip()]

    @classmethod
    def fallback_policies(cls) -> list[dict[str, Any]]:
        policies = _registry_content().get("fallbackPolicies")

        if not isinstance(policies, list):
            return []

        normalized = [policy for policy in policies if isinstance(policy, dict)]

        return sorted(
            normalized,
            key=lambda policy: int(policy.get("order") or 0),
        )

    @classmethod
    def fallback_policies_for_phase(cls, phase: str) -> list[dict[str, Any]]:
        target = str(phase or "").strip()

        if not target:
            return []

        return [
            policy
            for policy in cls.fallback_policies()
            if str(policy.get("phase") or "").strip() == target
        ]

    @classmethod
    def sql_refinement_policy(cls) -> dict[str, Any]:
        policy = _registry_content().get("sqlRefinementPolicy")

        if isinstance(policy, dict):
            return policy

        return {}

    @classmethod
    def route_path_marker_for_segment(cls, segment: str) -> str | None:
        normalized = str(segment or "").strip().lower()

        if not normalized:
            return None

        for route in cls.routes():
            if str(route.get("routeSegment") or "").strip().lower() != normalized:
                continue

            route_spec = route.get("route")

            if not isinstance(route_spec, dict):
                continue

            markers = route_spec.get("pathMarkers")

            if not isinstance(markers, list):
                continue

            for marker in markers:
                value = str(marker or "").strip()

                if value:
                    return value

        return None

    @classmethod
    def refinement_intent_by_route_segment(cls) -> dict[str, str]:
        mapping: dict[str, str] = {}

        for route in cls.intent_bound_routes():
            segment = str(route.get("routeSegment") or "").strip().lower()
            intent = str(route.get("intentBinding") or "").strip().lower()

            if segment and intent:
                mapping[segment] = intent

        return mapping

    @classmethod
    def preflight_sql_fallback_policies(cls) -> list[dict[str, Any]]:
        return [
            policy
            for policy in cls.fallback_policies()
            if policy.get("runBeforeSqlRefinement")
        ]
