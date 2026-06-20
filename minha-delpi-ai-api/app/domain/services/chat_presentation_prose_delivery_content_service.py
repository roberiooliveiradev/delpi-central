"""Loader JSON `presentation_prose_delivery` — modos template × LLM × direct."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "presentation_prose_delivery"


class ChatPresentationProseDeliveryContentService:
    @classmethod
    def mode_label(cls, mode: str) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "modes", mode, "label", default=mode)
            or mode
        ).strip()

    @classmethod
    def require_response_modes_for_llm_prose(cls) -> bool:
        settings = ChatAssistantContentService.get_node(_BUNDLE, "settings")

        if not isinstance(settings, dict):
            return True

        value = settings.get("requireResponseModesForLlmProse")

        if value is None:
            return True

        return bool(value)

    @classmethod
    def llm_prose_everywhere(cls) -> bool:
        """Quando true, todo turno com tool operacional ok usa inferência LLM (sem template/direct)."""
        settings = ChatAssistantContentService.get_node(_BUNDLE, "settings")

        if not isinstance(settings, dict):
            return False

        return bool(settings.get("llmProseEverywhere"))

    @classmethod
    def deprecate_humanized_linhas_as_prose(cls) -> bool:
        settings = ChatAssistantContentService.get_node(_BUNDLE, "settings")

        if not isinstance(settings, dict):
            return False

        return bool(settings.get("deprecateHumanizedLinhasAsProse"))

    @classmethod
    def allow_template_prose_fallback(cls) -> bool:
        """P8.1 — template só quando modos OFF e flag explícita (rollback offline)."""
        settings = ChatAssistantContentService.get_node(_BUNDLE, "settings")

        if not isinstance(settings, dict):
            return False

        return bool(settings.get("allowTemplateProseFallback"))

    @classmethod
    def prose_delivery_mode_for_tier(cls, tier: str | None) -> str | None:
        allowed = frozenset({"template", "llm", "direct"})
        token = str(tier or "").strip().upper()
        mode = str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "proseDeliveryByTier",
                token,
                default="",
            )
            or ""
        ).strip().lower()

        if mode in allowed:
            return mode

        return None

    @classmethod
    def metadata_key(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "metadataKeys", key, default=key)
            or key
        ).strip()

    @classmethod
    def data_only_title_spec(cls, profile_key: str) -> dict[str, str] | None:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "dataOnlyTitles",
            str(profile_key or "").strip(),
        )

        if not isinstance(node, dict):
            return None

        return {
            str(key).strip(): str(value).strip()
            for key, value in node.items()
            if str(key).strip() and str(value).strip()
        }
