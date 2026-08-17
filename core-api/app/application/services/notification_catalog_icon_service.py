# app/application/services/notification_catalog_icon_service.py

"""Ícones de categorias app: manifesto publicado (`apps.icon`), não o JSON do catálogo."""

from __future__ import annotations

from typing import Mapping, Protocol

from app.application.services.notification_catalog_service import NotificationCatalogService
from app.domain.notifications.notification_catalog_types import NotificationCatalog


class _AppIconLookup(Protocol):
    def get(self, app_id: str) -> object | None: ...


class NotificationCatalogIconService:
    """Resolve ícone de preferências / catálogo API a partir do app registrado."""

    @staticmethod
    def published_icons_by_plugin_id(admin_apps: _AppIconLookup) -> dict[str, str]:
        catalog = NotificationCatalogService.get()
        icons: dict[str, str] = {}
        for spec in catalog.categories.values():
            if spec.kind != "app" or not spec.plugin_id:
                continue
            plugin_id = spec.plugin_id.strip()
            if not plugin_id or plugin_id in icons:
                continue
            app = admin_apps.get(plugin_id)
            raw_icon = getattr(app, "icon", None) if app is not None else None
            icon = str(raw_icon).strip() if raw_icon else ""
            if icon:
                icons[plugin_id] = icon
        return icons

    @staticmethod
    def to_api_categories(
        admin_apps: _AppIconLookup,
        *,
        catalog: NotificationCatalog | None = None,
    ) -> list[dict[str, object]]:
        source = catalog or NotificationCatalogService.get()
        published = NotificationCatalogIconService.published_icons_by_plugin_id(admin_apps)
        items: list[dict[str, object]] = []
        for item in source.to_api_categories():
            plugin_id = str(item.get("pluginId") or "").strip()
            if item.get("kind") == "app" and plugin_id and plugin_id in published:
                item = {**item, "icon": published[plugin_id]}
            items.append(item)
        return items

    @staticmethod
    def resolve_icon_for_category(
        category_id: str,
        *,
        published_icons: Mapping[str, str] | None = None,
        catalog: NotificationCatalog | None = None,
    ) -> str:
        source = catalog or NotificationCatalogService.get()
        normalized = source.resolve_category(category_id)
        spec = source.categories.get(normalized)
        if not spec:
            return "bell"
        if spec.kind == "app" and spec.plugin_id:
            published = (published_icons or {}).get(spec.plugin_id, "")
            if published.strip():
                return published.strip()
        return (spec.icon or "bell").strip() or "bell"
