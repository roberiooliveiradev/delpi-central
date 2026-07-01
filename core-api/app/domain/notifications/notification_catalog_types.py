# app/domain/notifications/notification_catalog_types.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NotificationCategorySpec:
    id: str
    label: str
    icon: str
    mutable: bool
    kind: str
    source_apps: tuple[str, ...] = ()
    plugin_id: str | None = None


@dataclass(frozen=True)
class NotificationCatalog:
    version: int
    categories: dict[str, NotificationCategorySpec]
    legacy_category_aliases: dict[str, str] = field(default_factory=dict)

    @property
    def allowed_categories(self) -> frozenset[str]:
        return frozenset(self.categories.keys())

    @property
    def mutable_categories(self) -> frozenset[str]:
        return frozenset(
            category_id
            for category_id, spec in self.categories.items()
            if spec.mutable
        )

    @property
    def category_default_icons(self) -> dict[str, str]:
        return {category_id: spec.icon for category_id, spec in self.categories.items()}

    @property
    def source_app_plugin_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for spec in self.categories.values():
            if spec.kind != "app" or not spec.plugin_id:
                continue
            for source_app in spec.source_apps:
                key = source_app.strip().lower()
                if key:
                    aliases[key] = spec.plugin_id
        return aliases

    def resolve_category(self, raw_category: str | None) -> str:
        normalized = (raw_category or "system").strip().lower()
        return self.legacy_category_aliases.get(normalized, normalized)

    def category_for_source_app(self, source_app: str | None) -> str | None:
        if not source_app:
            return None
        key = source_app.strip().lower()
        for category_id, spec in self.categories.items():
            if key in {item.lower() for item in spec.source_apps}:
                return category_id
        return None

    def to_api_categories(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for category_id in sorted(self.categories.keys()):
            spec = self.categories[category_id]
            payload: dict[str, object] = {
                "id": spec.id,
                "label": spec.label,
                "icon": spec.icon,
                "mutable": spec.mutable,
                "kind": spec.kind,
            }
            if spec.source_apps:
                payload["sourceApps"] = list(spec.source_apps)
            if spec.plugin_id:
                payload["pluginId"] = spec.plugin_id
            items.append(payload)
        return items
