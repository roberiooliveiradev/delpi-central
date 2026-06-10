"""Modo Texto explícito — seleção de visão sem remover dados do payload."""

from __future__ import annotations

from typing import Any


class ChatPresentationTextModeService:
    @classmethod
    def is_user_explicit_text_mode(cls, metadata: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict):
            return False

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        return explicit in {"text", "topics"}

    @classmethod
    def should_embed_in_markdown(cls, metadata: dict[str, Any]) -> bool:
        """Embute árvore/tabela/gráfico no markdown só no modo Texto explícito da sessão."""
        return cls.is_user_explicit_text_mode(metadata)

    @classmethod
    def align_explicit_session_decision(cls, metadata: dict[str, Any]) -> None:
        """Alinha decisão à preferência explícita da sessão, preservando stack e todos os visuais."""
        if not isinstance(metadata, dict):
            return

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if not explicit or explicit == "canvas":
            return

        token = "text" if explicit == "topics" else explicit
        metadata["preferredFormat"] = token

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        decision["selected"] = token
        cls._apply_stack_layout_when_multiple_views(metadata, decision)

    @classmethod
    def _apply_stack_layout_when_multiple_views(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
    ) -> None:
        from app.domain.services.chat_presentation_decision_service import (
            ChatPresentationDecisionService,
        )

        merged_views = ChatPresentationDecisionService._merge_views(
            metadata.get("availableFormats"),
            decision.get("availableViews"),
        )

        if len(merged_views) >= 2:
            decision["layoutMode"] = "stack"
            decision["visualOrder"] = ChatPresentationDecisionService._visual_order_for_stack(
                merged_views,
            )
            decision["availableViews"] = merged_views
            return

        selected = str(decision.get("selected") or "").strip().lower()
        decision["layoutMode"] = "single"
        decision["visualOrder"] = [selected] if selected in merged_views else merged_views[:1] or [selected]

    @classmethod
    def enforce_single_text_decision(cls, metadata: dict[str, Any]) -> None:
        """Compat: delega para alinhamento explícito que preserva stack quando há múltiplas visões."""
        if not cls.is_user_explicit_text_mode(metadata):
            return

        metadata["explicitSessionFormat"] = "text"
        cls.align_explicit_session_decision(metadata)

    @classmethod
    def embed_and_finalize_explicit_text(cls, metadata: dict[str, Any]) -> None:
        """Enriquece markdown do modo Texto e alinha decisão — payload completo permanece."""
        if not isinstance(metadata, dict):
            return

        metadata["explicitSessionFormat"] = "text"
        metadata["preferredFormat"] = "text"

        from app.domain.services.chat_presentation_chart_markdown_service import (
            ChatPresentationChartMarkdownService,
        )
        from app.domain.services.chat_presentation_table_markdown_service import (
            ChatPresentationTableMarkdownService,
        )
        from app.domain.services.chat_presentation_tree_markdown_service import (
            ChatPresentationTreeMarkdownService,
        )

        ChatPresentationTreeMarkdownService.embed_outline_in_text_presentation(metadata)
        ChatPresentationTableMarkdownService.embed_tables_in_text_presentation(metadata)
        ChatPresentationChartMarkdownService.embed_charts_in_text_presentation(metadata)
        cls.finalize_explicit_text_mode(metadata)

    @classmethod
    def finalize_explicit_text_mode(cls, metadata: dict[str, Any]) -> None:
        """Pós-embed: alinha decisão ao Texto explícito sem remover slots nativos."""
        if not cls.is_user_explicit_text_mode(metadata):
            return

        cls.align_explicit_session_decision(metadata)
