"""Chips de refinamento após correção textual."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_correction_preference_service import (
    ChatTextCorrectionPreferenceService,
)
from app.domain.services.chat_text_correction_quality_validator import (
    ChatTextCorrectionQualityValidator,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatTextCorrectionFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None = None,
        answer: str | None = None,
        workspace_context: dict | None = None,
        guard_meta: dict[str, Any] | None = None,
        canvas_updated: bool = False,
    ) -> None:
        if not (
            ChatTextCorrectionIntentService.is_text_correction(message)
            or (workspace_context or {}).get("textCorrectionMode")
        ):
            return

        working_memory = (workspace_context or {}).get("workingMemory") or {}
        ctx = ChatTextCorrectionIntentService.extract_context(
            message,
            working_memory=working_memory,
        )
        subtype = ctx.get("subtype")
        suggestions = cls.build_suggestions(subtype)

        if suggestions:
            metadata["textCorrectionFollowUpSuggestions"] = suggestions

        text_task = ChatTextCorrectionIntentService.build_text_task_metadata(
            message=message,
            answer=answer,
        )

        if text_task:
            metadata.update(text_task)

        quality = ChatTextCorrectionQualityValidator.validate(
            answer,
            user_message=message,
            subtype=subtype,
            preserved_codes=ctx.get("preservedCodes"),
        )

        if quality.get("checks"):
            metadata["textCorrectionQuality"] = quality

        cls._attach_preferences_metadata(metadata, workspace_context, message)
        cls.merge_guard_metadata(metadata, guard_meta)

        from app.application.services.chat_text_correction_metrics_service import (
            ChatTextCorrectionMetricsService,
        )

        ChatTextCorrectionMetricsService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            workspace_context=workspace_context,
            guard_meta=guard_meta,
            follow_up_count=len(suggestions),
            canvas_updated=canvas_updated,
        )

        from app.application.services.chat_admin_debug_service import ChatAdminDebugService

        ChatAdminDebugService.sync_text_correction_trace(metadata)

    @classmethod
    def _attach_preferences_metadata(
        cls,
        metadata: dict,
        workspace_context: dict | None,
        message: str | None,
    ) -> None:
        working_memory = (workspace_context or {}).get("workingMemory") or {}
        prefs = ChatTextCorrectionPreferenceService.detect(
            message,
            working_memory=working_memory,
        )
        pref_meta = ChatTextCorrectionPreferenceService.build_metadata(prefs)

        if pref_meta:
            metadata["textCorrectionPreferences"] = pref_meta

    @classmethod
    def merge_guard_metadata(cls, metadata: dict, guard_meta: dict[str, Any] | None) -> None:
        if not guard_meta:
            return

        guard = guard_meta.get("textCorrectionGuard") or {}
        quality = guard.get("quality")

        if isinstance(quality, dict):
            metadata["textCorrectionQuality"] = quality

    @classmethod
    def build_suggestions(cls, subtype: str | None = None) -> list[dict[str, str]]:
        playbook = _playbook()
        chips = playbook.get("textCorrectionFollowUpChips") or []
        queries = playbook.get("textCorrectionFollowUpQueries") or {}
        suggestions: list[dict[str, str]] = []

        for label in chips:
            if not isinstance(label, str) or not label.strip():
                continue

            query = queries.get(label) or cls._default_query(label, subtype)
            suggestions.append({"label": label.strip(), "query": query})

        return suggestions[:10]

    @classmethod
    def _default_query(cls, label: str, subtype: str | None) -> str:
        lowered = label.lower()

        if "formal" in lowered:
            return "deixe o texto anterior mais formal, mantendo o sentido"

        if "curto" in lowered:
            return "deixe o texto anterior mais curto sem mudar o pedido principal"

        if "claro" in lowered:
            return "deixe o texto anterior mais claro"

        if "altera" in lowered or "mostrar" in lowered:
            return "mostre o texto anterior antes e depois e liste o que mudou"

        if "e-mail" in lowered:
            return "transforme o texto anterior em um e-mail formal"

        if "comunicado" in lowered:
            return "transforme o texto anterior em um comunicado interno"

        if "inglês" in lowered or "ingles" in lowered:
            return "traduza o texto anterior para inglês corporativo"

        if "lousa" in lowered:
            return "coloque o texto corrigido anterior na lousa"

        if "copiar" in lowered:
            return "repita só a versão final corrigida do texto anterior"

        return f"{label} no texto anterior"
