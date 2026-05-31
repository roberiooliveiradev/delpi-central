"""Catálogo único de funcionalidades do assistente — Playbook autoajuda, Fase 2."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.application.security.chat_permissions import (
    CHAT_ADMIN_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
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

                if cls._word_matches_haystack(word, haystack):
                    score += 2

            if score > 0:
                scored.append((score, dict(feature)))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [feature for _, feature in scored[:limit]]

    @classmethod
    def _word_matches_haystack(cls, word: str, haystack: str) -> bool:
        if word in haystack:
            return True

        if len(word) < 4:
            return False

        min_prefix = min(7, len(word))

        for token in re.findall(r"[a-z0-9]+", haystack):
            if len(token) < 4:
                continue

            if token.startswith(word) or word.startswith(token):
                return True

            shared = cls._shared_prefix_length(word, token)

            if shared >= min_prefix:
                return True

        return False

    @staticmethod
    def _shared_prefix_length(left: str, right: str) -> int:
        limit = min(len(left), len(right))
        index = 0

        while index < limit and left[index] == right[index]:
            index += 1

        return index

    @classmethod
    def resolve_availability(
        cls,
        *,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
        web_search_enabled: bool | None = None,
        user_permissions: set[str] | None = None,
        is_superadmin: bool = False,
        can_use_tools: bool | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        allowed_ids = {str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()}
        catalog = action_catalog or []
        permissions = {str(item).strip() for item in (user_permissions or []) if str(item).strip()}
        tools_allowed = cls.user_can_use_tools(
            permissions=permissions,
            is_superadmin=is_superadmin,
            can_use_tools=can_use_tools,
        )

        available_now: list[dict[str, Any]] = []
        requires_agent: list[dict[str, Any]] = []
        requires_permission: list[dict[str, Any]] = []
        requires_profile_permission: list[dict[str, Any]] = []
        disabled: list[dict[str, Any]] = []

        for feature in cls.list_features():
            entry = dict(feature)

            if entry.get("featureFlag") == "web_search_enabled":
                if web_search_enabled is False:
                    disabled.append(entry)
                    continue

                available_now.append(entry)
                continue

            profile_permissions = cls._feature_profile_permissions(entry)

            if profile_permissions and not cls._has_permissions(
                profile_permissions,
                permissions=permissions,
                is_superadmin=is_superadmin,
            ):
                requires_profile_permission.append(entry)
                continue

            if not entry.get("requiresAgent"):
                available_now.append(entry)
                continue

            if not tools_allowed:
                requires_profile_permission.append(entry)
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
            "requiresProfilePermission": requires_profile_permission,
            "disabled": disabled,
        }

    @classmethod
    def user_can_use_tools(
        cls,
        *,
        permissions: set[str],
        is_superadmin: bool,
        can_use_tools: bool | None,
    ) -> bool:
        if is_superadmin:
            return True

        if can_use_tools is not None:
            return bool(can_use_tools)

        return (
            CHAT_TOOLS_USE_PERMISSION in permissions
            or CHAT_TOOLS_MANAGE_PERMISSION in permissions
            or CHAT_ADMIN_PERMISSION in permissions
        )

    @classmethod
    def _feature_profile_permissions(cls, feature: dict[str, Any]) -> list[str]:
        raw = feature.get("requiredPermissions") or feature.get("required_permissions")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item).strip()]

    @classmethod
    def _has_permissions(
        cls,
        required: list[str],
        *,
        permissions: set[str],
        is_superadmin: bool,
    ) -> bool:
        if is_superadmin:
            return True

        if not required:
            return True

        return all(token in permissions for token in required)

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
    def latest_release_version(cls) -> str | None:
        releases = _release_notes_data().get("releases")

        if not isinstance(releases, list) or not releases:
            return None

        latest = releases[-1]

        if not isinstance(latest, dict):
            return None

        version = str(latest.get("version") or "").strip()

        return version or None

    @classmethod
    def list_contextual_highlights(cls, *, limit: int = 3) -> list[dict[str, Any]]:
        releases = _release_notes_data().get("releases")

        if not isinstance(releases, list) or not releases:
            return []

        latest = releases[-1]

        if not isinstance(latest, dict):
            return []

        version = str(latest.get("version") or "").strip()
        items = latest.get("items")

        if not isinstance(items, list):
            return []

        highlights: list[dict[str, Any]] = []

        for item in items[:limit]:
            if not isinstance(item, dict):
                continue

            feature_id = str(item.get("featureId") or "").strip()
            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()
            examples = item.get("examples")

            example_query = None

            if isinstance(examples, list) and examples:
                example_query = str(examples[0]).strip() or None

            if not title:
                continue

            highlights.append(
                {
                    "featureId": feature_id or None,
                    "title": title,
                    "description": description,
                    "exampleQuery": example_query,
                    "releaseVersion": version or None,
                }
            )

        return highlights

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
