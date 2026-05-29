"""Tradução de colunas operacionais — conteúdo editável + OpenAPI responseSchema."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


def invalidate_column_label_cache() -> None:
    _column_labels_content.cache_clear()


@lru_cache(maxsize=1)
def _column_labels_content() -> dict[str, Any]:
    return ContentService.load_json("assistant/column_labels")


class ExternalActionColumnLabelService:
    """Resolve labels de campos para tabelas do presenter operacional."""

    def label_for(
        self,
        key: str,
        *,
        schema_labels: dict[str, str] | None = None,
    ) -> str:
        normalized_key = str(key or "").strip()

        if not normalized_key:
            return ""

        if schema_labels:
            schema_label = schema_labels.get(normalized_key)

            if isinstance(schema_label, str) and schema_label.strip():
                return schema_label.strip()

        content = _column_labels_content()
        fields = content.get("fields") or {}
        configured = fields.get(normalized_key)

        if isinstance(configured, str) and configured.strip():
            return configured.strip()

        return normalized_key.replace("_", " ").strip().capitalize()

    def resolve_schema_labels(self, response_schema: dict | None) -> dict[str, str]:
        if not isinstance(response_schema, dict):
            return {}

        labels: dict[str, str] = {}

        for status_code, response in response_schema.items():
            if not str(status_code).startswith(("2", "default")):
                continue

            if not isinstance(response, dict):
                continue

            content = response.get("content") or {}

            if not isinstance(content, dict):
                continue

            for media in content.values():
                if not isinstance(media, dict):
                    continue

                schema = media.get("schema")

                if isinstance(schema, dict):
                    self._collect_schema_property_labels(schema, labels)

        return labels

    def detect_table_profile(self, row: dict, *, path: str = "") -> str | None:
        if not isinstance(row, dict):
            return None

        content = _column_labels_content()
        profiles = content.get("tableProfiles") or {}
        priority = content.get("profilePriority") or list(profiles.keys())
        lowered_path = str(path or "").lower()

        for profile_name in priority:
            profile = profiles.get(profile_name)

            if not isinstance(profile, dict):
                continue

            detect = profile.get("detect") or {}

            if not self._profile_matches(row, detect, lowered_path):
                continue

            return str(profile_name)

        return None

    def preferred_columns(
        self,
        profile_name: str,
        row: dict,
        *,
        schema_labels: dict[str, str] | None = None,
    ) -> list[tuple[str, str]]:
        if not isinstance(row, dict):
            return []

        content = _column_labels_content()
        profile = (content.get("tableProfiles") or {}).get(profile_name) or {}
        configured = profile.get("preferredColumns") or []
        columns: list[tuple[str, str]] = []

        for item in configured:
            if isinstance(item, (list, tuple)) and len(item) >= 1:
                key = str(item[0]).strip()
            elif isinstance(item, str) and item.strip():
                key = item.strip()
            else:
                continue

            if key not in row:
                continue

            label = self.label_for(key, schema_labels=schema_labels)
            columns.append((key, label))

        return columns

    def _profile_matches(
        self,
        row: dict,
        detect: dict,
        lowered_path: str,
    ) -> bool:
        path_contains = detect.get("pathContains") or []

        if path_contains and not any(token in lowered_path for token in path_contains):
            return False

        any_keys = detect.get("anyKeys") or []

        if any_keys and any(key in row for key in any_keys):
            exclude_if = detect.get("excludeIfAnyKeys") or []

            if exclude_if and any(key in row for key in exclude_if):
                return False

            return True

        for group in detect.get("anyKeyGroups") or []:
            if not isinstance(group, (list, tuple)):
                continue

            if all(key in row for key in group):
                return True

        exclude_if = detect.get("excludeIfAnyKeys") or []

        if exclude_if and any(key in row for key in exclude_if):
            return False

        required_all = detect.get("allKeys") or []

        if required_all and all(key in row for key in required_all):
            return True

        return False

    def _collect_schema_property_labels(
        self,
        schema: dict,
        labels: dict[str, str],
        *,
        depth: int = 0,
    ) -> None:
        if depth > 8 or not isinstance(schema, dict):
            return

        properties = schema.get("properties")

        if isinstance(properties, dict):
            for key, spec in properties.items():
                if not isinstance(spec, dict):
                    continue

                title = spec.get("title") or spec.get("x-label") or spec.get("x-ptLabel")

                if isinstance(title, str) and title.strip():
                    labels[str(key)] = title.strip()

                if spec.get("type") == "array":
                    items = spec.get("items")

                    if isinstance(items, dict):
                        self._collect_schema_property_labels(
                            items,
                            labels,
                            depth=depth + 1,
                        )
                elif spec.get("type") == "object":
                    self._collect_schema_property_labels(
                        spec,
                        labels,
                        depth=depth + 1,
                    )

        items = schema.get("items")

        if isinstance(items, dict):
            self._collect_schema_property_labels(items, labels, depth=depth + 1)
