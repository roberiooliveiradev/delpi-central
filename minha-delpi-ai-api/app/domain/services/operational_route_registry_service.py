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
            if isinstance(route, dict) and not route.get("intentBinding")
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
