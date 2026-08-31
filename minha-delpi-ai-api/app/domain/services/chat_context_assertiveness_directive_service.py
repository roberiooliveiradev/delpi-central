"""Diretivas de assertividade do turno anterior → prompt do turno atual."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)


class ChatContextAssertivenessDirectiveService:
    @classmethod
    def build_prompt_addon(
        cls,
        previous_messages: list[Any] | None,
    ) -> str:
        snapshot = cls._latest_assertiveness(previous_messages)
        if not isinstance(snapshot, dict):
            return ""

        try:
            score = float(snapshot.get("score"))
        except (TypeError, ValueError):
            score = 100.0

        flags = [
            str(item).strip()
            for item in (snapshot.get("flags") or [])
            if str(item).strip()
        ]

        if score >= 80 and not flags:
            return ""

        directives: list[str] = []
        for flag in flags:
            text = ChatOperationalLlmSynthesisContextContentService.assertiveness_directive(
                flag
            )
            if text and text not in directives:
                directives.append(text)

        if not directives and score < 80:
            default = ChatOperationalLlmSynthesisContextContentService.assertiveness_directive(
                "default_low"
            )
            if default:
                directives.append(default)

        if not directives:
            return ""

        body = "\n".join(f"- {item}" for item in directives)
        return f"\n\nDiretivas de continuidade (turno anterior):\n{body}"

    @classmethod
    def _latest_assertiveness(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        if not previous_messages:
            return None

        for item in reversed(list(previous_messages)):
            role = str(
                getattr(item, "role", None) or (item or {}).get("role") or ""
            ).strip()
            if role != "assistant":
                continue
            metadata = getattr(item, "metadata", None)
            if metadata is None and isinstance(item, dict):
                metadata = item.get("metadata")
            if not isinstance(metadata, dict):
                continue
            snapshot = metadata.get("contextAssertiveness")
            if isinstance(snapshot, dict):
                return snapshot

        return None
