"""Conteúdo declarativo do grounding de turno — bundle ``turn_grounding``."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "turn_grounding"


class ChatTurnGroundingContentService:
    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "limits") or {}
        if not isinstance(raw, dict):
            return default
        try:
            return int(raw.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def max_preview_chars(cls) -> int:
        return cls.limit_int("maxPreviewChars", 1200)

    @classmethod
    def max_top_keys(cls) -> int:
        return cls.limit_int("maxTopKeys", 8)

    @classmethod
    def max_top_keys_for_component_type(cls, component_type: str) -> int:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "limits",
            "maxTopKeysByComponentType",
        )

        if not isinstance(node, dict):
            return cls.max_top_keys()

        try:
            return int(node.get(str(component_type or "").strip().upper(), cls.max_top_keys()))
        except (TypeError, ValueError):
            return cls.max_top_keys()

    @classmethod
    def component_type_fields(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "componentTypeFields")
            if str(item).strip()
        )

    @classmethod
    def extract_key_fields(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "extractKeyFields")
            if str(item).strip()
        )

    @classmethod
    def identity_field_keys(cls, field: str) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "identityFieldKeys") or {}
        if not isinstance(node, dict):
            return ()
        raw = node.get(str(field or "").strip()) or []
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def identity_preview_lead(cls, *, code: str, description: str) -> str:
        return str(
            ChatAssistantContentService.format(
                _BUNDLE,
                "prompt",
                "identityPreviewLead",
                default="Código: {code}\nDescrição: {description}",
                code=code,
                description=description,
            )
            or ""
        ).strip()

    @classmethod
    def last_result_heading(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "prompt", "lastResultHeading", default="")
            or "Último resultado em foco"
        ).strip()

    @classmethod
    def referring_to_label(
        cls,
        *,
        title: str | None = None,
        row_count: int | None = None,
    ) -> str:
        safe_title = str(title or "").strip() or str(
            ChatAssistantContentService.get(
                _BUNDLE, "referringTo", "defaultTitle", default=""
            )
            or "Último resultado"
        ).strip()
        count = int(row_count) if row_count is not None else 0
        if count > 0:
            return ChatAssistantContentService.format(
                _BUNDLE,
                "referringTo",
                "labelTemplate",
                default="{title} · {rowCount} itens",
                title=safe_title,
                rowCount=count,
            )
        return ChatAssistantContentService.format(
            _BUNDLE,
            "referringTo",
            "labelTemplateNoCount",
            default="{title}",
            title=safe_title,
        )

    @classmethod
    def status_value(cls, key: str) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "statuses") or {}
        if not isinstance(node, dict):
            return key
        return str(node.get(key) or key).strip() or key

    @classmethod
    def expand_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "expandTriggers")
            if str(item).strip()
        )

    @classmethod
    def insight_enrich_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "insightEnrichTriggers")
            if str(item).strip()
        )

    @classmethod
    def insight_narrate_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "insightNarrateTriggers")
            if str(item).strip()
        )

    @classmethod
    def insight_triggers(cls) -> tuple[str, ...]:
        return cls.insight_enrich_triggers() + cls.insight_narrate_triggers()

    @classmethod
    def fan_out_on_referent_items(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "fanOutOnReferentItems")
            if str(item).strip()
        )

    @classmethod
    def referent_type_triggers(cls) -> dict[str, tuple[str, ...]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "referentTypeTriggers") or {}

        if not isinstance(node, dict):
            return {}

        resolved: dict[str, tuple[str, ...]] = {}

        for component_type, triggers in node.items():
            if not isinstance(triggers, list):
                continue

            cleaned = tuple(
                str(item).strip()
                for item in triggers
                if str(item).strip()
            )

            if cleaned:
                resolved[str(component_type).strip().upper()] = cleaned

        return resolved

    @classmethod
    def clarify_ambiguous_artifact(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE, "clarify", "ambiguousWhichArtifact", default=""
            )
            or ""
        ).strip()

    @classmethod
    def narrate_instruction(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE, "prompt", "narrateInstruction", default=""
            )
            or ""
        ).strip()

    @classmethod
    def format_excerpt_prompt_block(cls, excerpt: dict[str, Any] | None) -> str:
        if not isinstance(excerpt, dict) or not excerpt:
            return ""

        lines = [cls.last_result_heading()]
        title = str(excerpt.get("title") or "").strip()

        if title:
            lines.append(
                ChatAssistantContentService.format(
                    _BUNDLE,
                    "prompt",
                    "titleLine",
                    default="Título: {title}",
                    title=title,
                )
            )

        row_count = excerpt.get("rowCount")

        if isinstance(row_count, int) and row_count > 0:
            lines.append(
                ChatAssistantContentService.format(
                    _BUNDLE,
                    "prompt",
                    "rowCountLine",
                    default="Quantidade: {rowCount}",
                    rowCount=row_count,
                )
            )

        top_keys = excerpt.get("topKeys")

        if isinstance(top_keys, list) and top_keys:
            keys_text = ", ".join(str(item).strip() for item in top_keys if str(item).strip())
            if keys_text:
                lines.append(
                    ChatAssistantContentService.format(
                        _BUNDLE,
                        "prompt",
                        "topKeysLine",
                        default="Códigos em foco: {topKeys}",
                        topKeys=keys_text,
                    )
                )

        identity = excerpt.get("identityFields")
        if isinstance(identity, dict):
            code = str(identity.get("code") or "").strip()
            description = str(identity.get("description") or "").strip()
            if code:
                lines.append(
                    ChatAssistantContentService.format(
                        _BUNDLE,
                        "prompt",
                        "identityCodeLine",
                        default="Código: {code}",
                        code=code,
                    )
                )
            if description:
                lines.append(
                    ChatAssistantContentService.format(
                        _BUNDLE,
                        "prompt",
                        "identityDescriptionLine",
                        default="Descrição: {description}",
                        description=description,
                    )
                )

        preview = str(excerpt.get("preview") or "").strip()
        max_chars = cls.max_preview_chars()

        if preview:
            if max_chars > 0 and len(preview) > max_chars:
                preview = f"{preview[:max_chars]}\n…"

            lines.append(preview)

        return "\n".join(line for line in lines if line).strip()

    @classmethod
    def fast_enrich_insight_mode_suggestions(cls) -> list[dict[str, str]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "fastEnrichInsightModeSuggestions")
        suggestions: list[dict[str, str]] = []

        if not isinstance(node, list):
            return suggestions

        for item in node:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()

            if label and query:
                suggestions.append({"label": label, "query": query})

        return suggestions
