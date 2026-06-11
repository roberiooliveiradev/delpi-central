"""Loader de bundles assistant/*.json via AssistantContentPort."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, ClassVar

from app.domain.ports.assistant_content_port import AssistantContentPort


def invalidate_assistant_content_cache(bundle: str | None = None) -> None:
    _bundle_content.cache_clear()

    if ChatAssistantContentService._port is not None:
        ChatAssistantContentService._port.invalidate_cache(bundle)


@lru_cache(maxsize=32)
def _bundle_content(bundle: str) -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle(bundle)


class ChatAssistantContentService:
    _port: ClassVar[AssistantContentPort | None] = None

    @classmethod
    def configure(cls, port: AssistantContentPort) -> None:
        cls._port = port
        _bundle_content.cache_clear()

    @classmethod
    def _require_port(cls) -> AssistantContentPort:
        if cls._port is None:
            raise RuntimeError(
                "AssistantContentPort não configurado — chame configure_domain_infrastructure_ports()"
            )

        return cls._port

    @classmethod
    def load_bundle(cls, bundle: str) -> dict[str, Any]:
        return cls._require_port().load_bundle(bundle)

    @classmethod
    def load_personality_playbook(cls) -> dict[str, Any]:
        return cls._require_port().load_personality_playbook()

    @classmethod
    def load_stream(cls) -> dict[str, Any]:
        return cls._require_port().load_stream()

    @classmethod
    def load_skills_catalog(cls) -> dict[str, Any]:
        return cls._require_port().load_skills_catalog()

    @classmethod
    def get(cls, bundle: str, *path: str, default: str = "") -> str:
        node: Any = _bundle_content(bundle)

        for key in path:
            if not isinstance(node, dict):
                return default

            node = node.get(key)

        if node is None:
            return default

        if isinstance(node, str):
            return node

        return default

    @classmethod
    def format(cls, bundle: str, *path: str, default: str = "", **values) -> str:
        template = cls.get(bundle, *path, default=default)

        if not template:
            return default

        try:
            return template.format(**values)
        except KeyError:
            return template

    @classmethod
    def list(cls, bundle: str, *path: str) -> list[str]:
        node: Any = _bundle_content(bundle)

        for key in path:
            if not isinstance(node, dict):
                return []

            node = node.get(key)

        if not isinstance(node, list):
            return []

        return [str(item) for item in node if str(item).strip()]

    @classmethod
    def get_mapping(cls, bundle: str, *path: str) -> dict[str, str]:
        node: Any = _bundle_content(bundle)

        for key in path:
            if not isinstance(node, dict):
                return {}

            node = node.get(key)

        if not isinstance(node, dict):
            return {}

        return {
            str(item_key): str(item_value)
            for item_key, item_value in node.items()
            if str(item_key).strip() and item_value is not None
        }

    @classmethod
    def get_error_type(cls, error_type: str, field: str, *, default: str = "") -> str:
        node: Any = _bundle_content("error_handling").get("types", {}).get(error_type, {})

        if not isinstance(node, dict):
            return default

        value = node.get(field)

        if value is None:
            return default

        if isinstance(value, str):
            return value

        return default

    @classmethod
    def get_error_reasons(cls, error_type: str) -> list[str]:
        node: Any = _bundle_content("error_handling").get("types", {}).get(error_type, {})

        if not isinstance(node, dict):
            return []

        reasons = node.get("reasons")

        if not isinstance(reasons, list):
            return []

        return [str(item) for item in reasons if str(item).strip()]

    @classmethod
    def get_node(cls, bundle: str, *path: str) -> Any:
        node: Any = _bundle_content(bundle)

        for key in path:
            if not isinstance(node, dict):
                return None

            node = node.get(key)

        return node

    @classmethod
    def title_for_path(
        cls,
        bundle: str,
        path: str,
        *,
        path_key: str = "titlesByPathFragment",
        default: str | None = None,
    ) -> str | None:
        """Primeiro fragmento de path que casar no mapa de títulos (mais específico primeiro)."""
        lowered = str(path or "").lower()
        fragments = cls.get_mapping(bundle, path_key)

        if not fragments:
            return default

        for fragment, label in sorted(
            fragments.items(),
            key=lambda item: len(str(item[0] or "")),
            reverse=True,
        ):
            if fragment in lowered:
                return label

        return default
