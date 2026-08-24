"""Catálogo declarativo de capacidades operacionais por domínio."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)

_BUNDLE = "entity_capability_catalog"


class ChatEntityCapabilityCatalogService:
    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits") or {}

        if not isinstance(node, dict):
            return default

        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def max_extra_routes_per_turn(cls) -> int:
        return cls.limit_int("maxExtraRoutesPerTurn", 4)

    @classmethod
    def max_fan_out_keys(cls) -> int:
        return cls.limit_int("maxFanOutKeys", 8)

    @classmethod
    def domain_capabilities(cls, domain: str) -> list[dict[str, Any]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "domains", domain) or {}

        if not isinstance(node, dict):
            return []

        capabilities = node.get("capabilities")

        return [item for item in capabilities if isinstance(item, dict)] if isinstance(capabilities, list) else []

    @classmethod
    def route_id_for_scope(cls, scope_key: str) -> str | None:
        route_id = ChatAssistantContentService.get(
            _BUNDLE,
            "scopeToRouteId",
            scope_key,
            default="",
        )

        return str(route_id).strip() or None

    @classmethod
    def enrich_insight_scopes(cls, artifact_key: str) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "enrichInsightScopes") or {}

        if not isinstance(node, dict):
            return ()

        scopes = node.get(str(artifact_key or "").strip())

        if not isinstance(scopes, list) or not scopes:
            scopes = node.get("default")

        if not isinstance(scopes, list):
            return ()

        return tuple(str(item).strip() for item in scopes if str(item).strip())

    @classmethod
    def artifact_enrich_key(cls, entity: str | None, profile_key: str | None = None) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "artifactToEnrichKey") or {}

        if isinstance(node, dict):
            entity_key = str(entity or "").strip()

            if entity_key and entity_key in node:
                return str(node[entity_key]).strip()

            profile = str(profile_key or "").strip()

            if profile and profile in node:
                return str(node[profile]).strip()

        return "default"

    @classmethod
    def available(
        cls,
        *,
        domain: str,
        allowed_action_ids: list[str] | None,
        executed_route_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        allowed = {str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()}
        executed = executed_route_ids or set()
        remaining: list[dict[str, Any]] = []

        for capability in cls.domain_capabilities(domain):
            route_id = str(capability.get("routeId") or "").strip()

            if not route_id or route_id in executed:
                continue

            route = OperationalRouteRegistryService.route_by_id(route_id)

            if not route:
                continue

            action_id = cls._resolve_action_id(route)

            if allowed and action_id and action_id not in allowed:
                continue

            remaining.append(
                {
                    **capability,
                    "routeId": route_id,
                    "actionId": action_id,
                }
            )

        return remaining

    @classmethod
    def _resolve_action_id(cls, route: dict[str, Any]) -> str | None:
        action = route.get("actionId")

        if isinstance(action, str) and action.strip():
            return action.strip()

        route_node = route.get("route")

        if isinstance(route_node, dict):
            markers = route_node.get("operationIdMarkers")

            if isinstance(markers, list) and markers:
                return str(markers[0]).strip() or None

        return None
