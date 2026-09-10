"""Catálogo declarativo de rotas operacionais (legado/policies + CI autoTierC).

Runtime de seleção de actions: Action Catalog OpenAPI (Postgres).
`autoTierCRoutes` vive só em `operational_route_registry_autotierc.ci.json` (gate CI api-delpi).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def invalidate_operational_route_registry_cache() -> None:
    _registry_content.cache_clear()
    _autotierc_ci_content.cache_clear()
    from app.domain.services.route_segment_inference_service import (
        invalidate_route_segment_inference_cache,
    )

    invalidate_route_segment_inference_cache()


@lru_cache(maxsize=1)
def _registry_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("operational_route_registry")


@lru_cache(maxsize=1)
def _autotierc_ci_content() -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[2]
        / "content"
        / "pt-BR"
        / "assistant"
        / "operational_route_registry_autotierc.ci.json"
    )
    if not path.is_file():
        return {}
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


class OperationalRouteRegistryService:
    @classmethod
    def version(cls) -> str:
        return str(_registry_content().get("version") or "").strip()

    @classmethod
    def dispatch_order(cls) -> list[str]:
        order = _registry_content().get("dispatchOrder")

        if not isinstance(order, list):
            return []

        # autoTierC removido do runtime — Action Catalog OpenAPI é a fonte.
        return [
            str(item).strip()
            for item in order
            if str(item).strip() and str(item).strip() != "autoTierCRoutes"
        ]

    @classmethod
    def manual_routes(cls) -> list[dict[str, Any]]:
        routes = _registry_content().get("routes")

        if not isinstance(routes, list):
            return []

        return [route for route in routes if isinstance(route, dict)]

    @classmethod
    def auto_tier_c_routes(cls) -> list[dict[str, Any]]:
        """Runtime: sempre vazio. Seleção usa OpenAPI Action Catalog."""
        return []

    @classmethod
    def ci_auto_tier_c_routes(cls) -> list[dict[str, Any]]:
        """Somente CI / gerador — espelho do baseline api-delpi."""
        routes = _autotierc_ci_content().get("autoTierCRoutes")
        if not isinstance(routes, list):
            return []
        return [route for route in routes if isinstance(route, dict)]

    @classmethod
    def ci_auto_tier_c_path(cls) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "content"
            / "pt-BR"
            / "assistant"
            / "operational_route_registry_autotierc.ci.json"
        )

    @classmethod
    def routes(cls) -> list[dict[str, Any]]:
        normalized = cls.manual_routes()

        return sorted(
            normalized,
            key=lambda route: int(route.get("priority") or 0),
            reverse=True,
        )

    @classmethod
    def route_by_operation_id(cls, operation_id: str) -> dict[str, Any] | None:
        """Legacy lookup — CI autoTierC only (not used for OpenAPI selection)."""
        target = str(operation_id or "").strip()

        if not target:
            return None

        for route in cls.ci_auto_tier_c_routes():
            if str(route.get("operationId") or "").strip() == target:
                return route

        return None

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
        filtered = [
            route
            for route in cls.manual_routes()
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

        return sorted(filtered, key=cls._vocabulary_route_sort_key)

    @staticmethod
    def _vocabulary_route_sort_key(route: dict[str, Any]) -> tuple[int, int]:
        """Facetas de produto (segmento/código) antes de catch-alls como productSearch."""
        from app.domain.services.route_segment_inference_service import (
            RouteSegmentInferenceService,
        )

        domain = str(route.get("domain") or "").strip()
        match = route.get("match") if isinstance(route.get("match"), dict) else {}
        has_segment = RouteSegmentInferenceService.has_product_continuity_segment(route)
        requires_product = bool(match.get("requiresProductIdentifier"))

        # domainProductSearch before inferred path keys — /products/search also yields keys.
        if domain == "domainProductSearch":
            class_rank = 2
        elif has_segment or requires_product or domain == "product":
            class_rank = 0
        else:
            class_rank = 1

        # Dentro da classe: maior priority primeiro (mesmo critério de routes()).
        return (class_rank, -int(route.get("priority") or 0))

    @classmethod
    def production_operational_routes(cls) -> list[dict[str, Any]]:
        return [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "productionOperational"
        ]

    @classmethod
    def routes_by_segment(cls, segment: str) -> list[dict[str, Any]]:
        from app.domain.services.route_segment_inference_service import (
            RouteSegmentInferenceService,
        )

        normalized = str(segment or "").strip().lower()

        if not normalized:
            return []

        return [
            route
            for route in cls.routes()
            if RouteSegmentInferenceService.route_matches_segment(route, normalized)
        ]

    @classmethod
    def system_metadata_routes(cls) -> list[dict[str, Any]]:
        routes = [
            route
            for route in cls.routes()
            if str(route.get("domain") or "").strip() == "domainSystem"
        ]

        return sorted(
            routes,
            key=lambda route: int(route.get("priority") or 0),
            reverse=True,
        )

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
    def sql_readiness_entries(cls) -> list[dict[str, Any]]:
        node = _registry_content().get("sqlReadiness")

        if not isinstance(node, dict):
            return []

        entries = node.get("productionOperationalKinds")

        if not isinstance(entries, list):
            return []

        return [entry for entry in entries if isinstance(entry, dict)]

    @classmethod
    def route_path_marker_for_segment(cls, segment: str) -> str | None:
        """Hint de path por segment — pós-E9.S12.D deriva de operationIds (OpenAPI)."""
        normalized = str(segment or "").strip().lower()

        if not normalized:
            return None

        if not cls.routes_by_segment(normalized):
            return None

        # Canonical: continuity segment as path fragment (ex.: stock → /stock).
        return f"/{normalized}"

    @classmethod
    def refinement_intent_by_route_segment(cls) -> dict[str, str]:
        from app.domain.services.route_segment_inference_service import (
            RouteSegmentInferenceService,
        )

        mapping: dict[str, str] = {}

        for route in cls.intent_bound_routes():
            intent = str(route.get("intentBinding") or "").strip().lower()
            if not intent:
                continue

            for segment in RouteSegmentInferenceService.continuity_keys_for_route(route):
                # Prefer exact intentBinding key when present among derived keys.
                if segment == intent or segment not in mapping:
                    mapping[segment] = intent

        return mapping

    @classmethod
    def preflight_sql_fallback_policies(cls) -> list[dict[str, Any]]:
        return [
            policy
            for policy in cls.fallback_policies()
            if policy.get("runBeforeSqlRefinement")
        ]

    @classmethod
    def paginated_path_fragments(cls) -> tuple[str, ...]:
        node = _registry_content().get("refinementVocabulary")

        if not isinstance(node, dict):
            return ()

        raw = node.get("paginatedPathFragments")

        if not isinstance(raw, list):
            return ()

        return tuple(
            str(fragment).strip()
            for fragment in raw
            if str(fragment).strip()
        )
