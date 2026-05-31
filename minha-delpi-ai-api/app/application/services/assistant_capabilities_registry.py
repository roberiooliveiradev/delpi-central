"""Catálogo único de funcionalidades do assistente — Playbook autoajuda, Fase 2."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _catalog_data() -> dict[str, Any]:
    return ContentService.load_json("assistant/features_catalog")


def clear_catalog_cache() -> None:
    _catalog_data.cache_clear()
    _release_notes_data.cache_clear()


@lru_cache(maxsize=1)
def _release_notes_data() -> dict[str, Any]:
    try:
        return ContentService.load_json("assistant/assistant_release_notes")
    except (FileNotFoundError, OSError, ValueError):
        return {"releases": []}


class AssistantCapabilitiesRegistry:
    @classmethod
    def catalog_version(cls) -> str:
        return str(_catalog_data().get("version") or "").strip()

    @classmethod
    def list_features(cls) -> list[dict[str, Any]]:
        raw = _catalog_data().get("features")

        if not isinstance(raw, list):
            return []

        return [item for item in raw if isinstance(item, dict)]

    @classmethod
    def get_feature(cls, feature_id: str) -> dict[str, Any] | None:
        token = str(feature_id or "").strip()

        if not token:
            return None

        for feature in cls.list_features():
            if str(feature.get("id") or "") == token:
                return dict(feature)

        return None

    @classmethod
    def find_by_help_topic(cls, topic: str) -> dict[str, Any] | None:
        token = str(topic or "").strip()

        if not token:
            return None

        for feature in cls.list_features():
            if str(feature.get("helpTopicId") or "") == token:
                return dict(feature)

        return None

    @classmethod
    def search(cls, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        normalized = str(query or "").strip().lower()

        if not normalized:
            return cls.list_features()[:limit]

        scored: list[tuple[int, dict[str, Any]]] = []

        for feature in cls.list_features():
            haystack = " ".join(
                [
                    str(feature.get("id") or ""),
                    str(feature.get("title") or ""),
                    str(feature.get("summary") or ""),
                    str(feature.get("category") or ""),
                    " ".join(str(item) for item in (feature.get("examples") or [])),
                ]
            ).lower()

            score = 0

            for word in normalized.split():
                if len(word) < 3:
                    continue

                if word in haystack:
                    score += 2

            if score > 0:
                scored.append((score, dict(feature)))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [feature for _, feature in scored[:limit]]

    @classmethod
    def resolve_availability(
        cls,
        *,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
        web_search_enabled: bool | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        allowed_ids = {str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()}
        catalog = action_catalog or []

        available_now: list[dict[str, Any]] = []
        requires_agent: list[dict[str, Any]] = []
        requires_permission: list[dict[str, Any]] = []
        disabled: list[dict[str, Any]] = []

        for feature in cls.list_features():
            entry = dict(feature)
            feature_id = str(entry.get("id") or "")

            if entry.get("featureFlag") == "web_search_enabled":
                if web_search_enabled is False:
                    disabled.append(entry)
                    continue

                available_now.append(entry)
                continue

            if not entry.get("requiresAgent"):
                available_now.append(entry)
                continue

            if not allowed_ids:
                requires_agent.append(entry)
                continue

            required_actions = [
                str(item).lower()
                for item in (entry.get("requiredActions") or [])
                if str(item).strip()
            ]

            if not required_actions:
                requires_agent.append(entry)
                continue

            if cls._matches_actions(required_actions, catalog, allowed_ids):
                available_now.append(entry)
            else:
                requires_permission.append(entry)

        return {
            "availableNow": available_now,
            "requiresAgent": requires_agent,
            "requiresPermission": requires_permission,
            "disabled": disabled,
        }

    @classmethod
    def format_release_notes_answer(cls, *, limit: int = 6) -> str | None:
        releases = _release_notes_data().get("releases")

        if not isinstance(releases, list) or not releases:
            return None

        latest = releases[-1]

        if not isinstance(latest, dict):
            return None

        version = str(latest.get("version") or "").strip()
        items = latest.get("items")

        if not isinstance(items, list) or not items:
            return None

        lines = [
            f"Principais novidades (versão **{version or 'recente'}**):",
            "",
        ]

        for item in items[:limit]:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()

            if title:
                lines.append(f"- **{title}** — {description}" if description else f"- **{title}**")

        lines.extend(
            [
                "",
                "Pergunte *«como uso a lousa?»*, *«como pesquiso na web?»* ou *«o que você pode fazer?»* "
                "para ver exemplos atualizados.",
            ]
        )

        return "\n".join(lines).strip()

    @classmethod
    def _matches_actions(
        cls,
        required_tokens: list[str],
        catalog: list[dict],
        allowed_ids: set[str],
    ) -> bool:
        for action in catalog:
            action_id = str(action.get("actionId") or "").strip()

            if action_id not in allowed_ids:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()
            haystack = f"{path} {operation_id}"

            if any(token in haystack for token in required_tokens):
                return True

        return False
