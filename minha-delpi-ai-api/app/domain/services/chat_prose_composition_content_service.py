"""Loader do catálogo `prose_composition` — marcadores e políticas de composição LLM."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "prose_composition"


class ChatProseCompositionContentService:
    @classmethod
    def default_policy(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "defaultPolicy", default="llm_markers")
            or "llm_markers"
        ).strip()

    @classmethod
    def marker_catalog(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "markers")

        return node if isinstance(node, dict) else {}

    @classmethod
    def canonical_marker_kinds(cls) -> tuple[str, ...]:
        return tuple(sorted(cls.marker_catalog().keys()))

    @classmethod
    def normalize_marker_kind(cls, raw: str | None) -> str | None:
        token = str(raw or "").strip().lower()

        if not token:
            return None

        for kind, spec in cls.marker_catalog().items():
            if not isinstance(spec, dict):
                continue

            aliases = spec.get("aliases") or [kind]

            if token == kind or token in {str(item).strip().lower() for item in aliases}:
                return kind

        return None

    @classmethod
    def policy_node(cls, policy: str | None) -> dict[str, Any]:
        key = str(policy or cls.default_policy()).strip().lower() or cls.default_policy()
        node = ChatAssistantContentService.get_node(_BUNDLE, "policies", key)

        if isinstance(node, dict):
            return node

        fallback = ChatAssistantContentService.get_node(
            _BUNDLE,
            "policies",
            cls.default_policy(),
        )

        return fallback if isinstance(fallback, dict) else {}

    @classmethod
    def policy_for_explicit_format(cls, explicit_format: str | None) -> str | None:
        token = str(explicit_format or "").strip().lower()

        if not token:
            return None

        mapping = ChatAssistantContentService.get_node(_BUNDLE, "policyByExplicitFormat")

        if not isinstance(mapping, dict):
            return None

        value = mapping.get(token)

        return str(value).strip() if value else None

    @classmethod
    def response_mode_limits(cls, response_mode: str | None) -> dict[str, Any]:
        mode = str(response_mode or "normal").strip().lower() or "normal"
        node = ChatAssistantContentService.get_node(_BUNDLE, "policyByResponseMode", mode)

        return node if isinstance(node, dict) else {}

    @classmethod
    def forbidden_markers_for_explicit(cls, explicit_format: str | None) -> tuple[str, ...]:
        token = str(explicit_format or "").strip().lower()
        node = ChatAssistantContentService.get_node(_BUNDLE, "forbiddenWhenExplicit")

        if not isinstance(node, dict):
            return ()

        raw = node.get(token)

        if not isinstance(raw, list):
            return ()

        return tuple(str(item).strip().lower() for item in raw if str(item).strip())

    @classmethod
    def prompt_rule(cls, key: str, *, default: str = "", **kwargs: Any) -> str:
        template = str(
            ChatAssistantContentService.get(_BUNDLE, "promptRules", key, default=default)
            or default
        ).strip()

        if not template or not kwargs:
            return template

        try:
            return template.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return template

    @classmethod
    def marker_pattern(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "markerPattern",
                default=r"\[\[(tabela|table|grafico|chart|arvore|árvore|tree|kpi|dashboard)(?::(\d+))?\]\]",
            )
            or ""
        ).strip()

    @classmethod
    def llm_may_emit_markers(cls, policy: str | None) -> bool:
        return bool(cls.policy_node(policy).get("llmMayEmitMarkers"))

    @classmethod
    def max_markers(cls, policy: str | None, *, response_mode: str | None = None) -> int:
        policy_cap = cls.policy_node(policy).get("maxMarkers")
        mode_cap = cls.response_mode_limits(response_mode).get("maxMarkers")

        caps: list[int] = []

        for raw in (policy_cap, mode_cap):
            try:
                caps.append(max(0, int(raw)))
            except (TypeError, ValueError):
                continue

        if not caps:
            return 4

        return min(caps)
