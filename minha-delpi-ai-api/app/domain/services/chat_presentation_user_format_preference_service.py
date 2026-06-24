"""Preferência explícita de formato — toolbar e marcadores na mensagem."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_decision_builder_service import (
    ChatPresentationDecisionBuilderService,
)
from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

_USER_FORMAT_ALIASES = {
    "text": "text",
    "texto": "text",
    "table": "table",
    "tabela": "table",
    "chart": "chart",
    "grafico": "chart",
    "gráfico": "chart",
    "kpi": "kpi",
    "tree": "tree",
    "arvore": "tree",
    "árvore": "tree",
    "checklist": "checklist",
    "canvas": "canvas",
    "lousa": "canvas",
    "dashboard": "dashboard",
    "line": "line_chart",
    "line_chart": "line_chart",
    "bar_chart": "bar_chart",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
}


class ChatPresentationUserFormatPreferenceService:
    @classmethod
    def resolve_effective(
        cls,
        metadata: dict[str, Any],
        user_preference: str | None,
    ) -> str | None:
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        normalized = ChatPresentationTextFirstPolicyService.normalize_explicit_format(
            user_preference,
        )

        if normalized:
            return normalized

        explicit = ChatPresentationTextFirstPolicyService.normalize_explicit_format(
            metadata.get("explicitSessionFormat"),
        )

        if explicit:
            return explicit

        return None

    @classmethod
    def normalize_from_message(
        cls,
        user_preference: str | None,
        message: str,
    ) -> str | None:
        token = str(user_preference or "").strip().lower()

        if token in _USER_FORMAT_ALIASES:
            return _USER_FORMAT_ALIASES[token]

        if not message:
            return None

        chart_hints = ChatPresentationVocabularyService.format_preference_markers("chartHints")
        table_hints = ChatPresentationVocabularyService.format_preference_markers("tableHints")
        line_tokens = ChatPresentationVocabularyService.format_preference_markers("lineTokens")
        area_tokens = ChatPresentationVocabularyService.format_preference_markers("areaTokens")
        donut_tokens = ChatPresentationVocabularyService.format_preference_markers("donutTokens")
        horizontal_token = ChatPresentationVocabularyService.text(
            "formatPreferenceMarkers",
            "horizontalToken",
            default="horizontal",
        )
        chart_subtype_tokens = ChatPresentationVocabularyService.format_preference_markers(
            "chartSubtypeTokens",
        )

        for alias, mapped in _USER_FORMAT_ALIASES.items():
            if alias in ("text", "table") and f"em {alias}" in message:
                return mapped

            if alias in ("grafico", "gráfico", "chart") and any(
                hint in message for hint in chart_hints
            ):
                if any(token in message for token in chart_subtype_tokens):
                    if any(token in message for token in line_tokens):
                        return "line_chart"

                    if any(token in message for token in area_tokens):
                        return "area_chart"

                    if any(token in message for token in donut_tokens):
                        return "donut"

                    if horizontal_token in message:
                        return "horizontal_bar"

                return "chart"

            if alias in ("tabela", "table") and any(hint in message for hint in table_hints):
                return "table"

        return None

    @classmethod
    def build_decision(
        cls,
        preferred: str,
        *,
        rows: list[dict[str, Any]] | None,
        user_message: str,
        available_formats: list[str] | None,
        intent: str | None,
        tree_presentation: dict[str, Any] | None = None,
        primary_presentation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reason = ChatPresentationVocabularyService.decision_reason
        normalized_views = {
            ChatPresentationDecisionBuilderService.view_from_legacy_format(str(token))
            for token in (available_formats or [])
        }
        resolved = preferred

        effective_tree = ChatPresentationDecisionMetadataService.effective_tree_presentation(
            tree_presentation=tree_presentation,
            primary_presentation=primary_presentation,
        )

        if preferred in {"tree", "chart", "line_chart", "bar_chart", "donut"}:
            if preferred == "tree" and not effective_tree:
                resolved = "text" if "text" in normalized_views else "table"
            elif preferred not in normalized_views and "text" in normalized_views:
                resolved = "text"

        if (
            resolved == "table"
            and ChatPresentationDecisionMetadataService.is_product_field_value_table(rows)
            and "text" in normalized_views
        ):
            from app.domain.services.chat_product_overview_intent_service import (
                ChatProductOverviewIntentService,
            )

            if ChatProductOverviewIntentService.is_product_overview_message(user_message):
                resolved = "text"

        fallback = "table" if rows else "text"
        views = ChatPresentationDecisionBuilderService.merge_views(
            available_formats,
            [resolved, fallback, "text"],
        )
        decision_reason = (
            reason("formatUnavailableFallback")
            if resolved != preferred
            else reason("formatUserRequested")
        )

        return ChatPresentationDecisionBuilderService.build(
            selected=resolved,
            fallback=fallback,
            reason=decision_reason,
            available_views=views,
            rows=rows,
            intent=intent,
        )
