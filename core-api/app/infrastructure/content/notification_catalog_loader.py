# app/infrastructure/content/notification_catalog_loader.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.notifications.notification_catalog_types import (
    NotificationCatalog,
    NotificationCategorySpec,
)

_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "notification_catalog.json"
)


def default_catalog_path() -> Path:
    return _CATALOG_PATH


def load_notification_catalog(path: Path | None = None) -> NotificationCatalog:
    catalog_path = path or default_catalog_path()
    with catalog_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    return _parse_catalog(raw)


def _parse_catalog(raw: dict[str, Any]) -> NotificationCatalog:
    version = int(raw.get("version") or 1)
    categories_raw = raw.get("categories")
    if not isinstance(categories_raw, dict) or not categories_raw:
        raise ValueError("notification_catalog.categories must be a non-empty object")

    categories: dict[str, NotificationCategorySpec] = {}
    for category_id, item in categories_raw.items():
        if not isinstance(item, dict):
            raise ValueError(f"notification_catalog.categories.{category_id} must be an object")

        label = str(item.get("label") or "").strip()
        icon = str(item.get("icon") or "bell").strip() or "bell"
        kind = str(item.get("kind") or "platform").strip().lower() or "platform"
        mutable = bool(item.get("mutable", True))
        plugin_id = item.get("pluginId") or item.get("plugin_id")
        plugin_id_str = str(plugin_id).strip() if plugin_id else None

        source_apps_raw = item.get("sourceApps") or item.get("source_apps") or []
        if not isinstance(source_apps_raw, list):
            raise ValueError(
                f"notification_catalog.categories.{category_id}.sourceApps must be an array"
            )
        source_apps = tuple(
            str(source_app).strip()
            for source_app in source_apps_raw
            if str(source_app).strip()
        )

        if kind == "app" and not source_apps:
            raise ValueError(
                f"notification_catalog.categories.{category_id} kind=app requires sourceApps"
            )

        categories[str(category_id).strip().lower()] = NotificationCategorySpec(
            id=str(category_id).strip().lower(),
            label=label or category_id,
            icon=icon,
            mutable=mutable,
            kind=kind,
            source_apps=source_apps,
            plugin_id=plugin_id_str,
        )

    legacy_aliases_raw = raw.get("legacyCategoryAliases") or raw.get("legacy_category_aliases") or {}
    if not isinstance(legacy_aliases_raw, dict):
        raise ValueError("notification_catalog.legacyCategoryAliases must be an object")

    legacy_aliases: dict[str, str] = {}
    for alias, target in legacy_aliases_raw.items():
        alias_key = str(alias).strip().lower()
        target_key = str(target).strip().lower()
        if alias_key and target_key:
            legacy_aliases[alias_key] = target_key

    for alias, target in legacy_aliases.items():
        if target not in categories:
            raise ValueError(
                f"notification_catalog legacy alias '{alias}' points to unknown category '{target}'"
            )

    return NotificationCatalog(
        version=version,
        categories=categories,
        legacy_category_aliases=legacy_aliases,
    )
