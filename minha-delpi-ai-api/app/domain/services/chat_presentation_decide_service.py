"""Orquestração de decide() — preferência, intent operacional, genérico."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_generic_decision_service import (
    ChatPresentationGenericDecisionService,
)
from app.domain.services.chat_presentation_operational_intent_decision_service import (
    ChatPresentationOperationalIntentDecisionService,
)
from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)


class ChatPresentationDecideService:
    @classmethod
    def decide(
        cls,
        *,
        intent: str | None = None,
        rows: list[dict[str, Any]] | None = None,
        user_message: str | None = None,
        user_preference: str | None = None,
        primary_presentation: dict[str, Any] | None = None,
        table_presentation: dict[str, Any] | None = None,
        chart_presentation: dict[str, Any] | None = None,
        tree_presentation: dict[str, Any] | None = None,
        dashboard_presentation: dict[str, Any] | None = None,
        text_presentation: dict[str, Any] | None = None,
        available_formats: list[str] | None = None,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message = ChatPresentationGenericDecisionService.normalize_message(user_message)
        preferred = ChatPresentationUserFormatPreferenceService.normalize_from_message(
            user_preference,
            message,
        )
        intent_token = str(intent or "").strip().lower()

        if preferred:
            return ChatPresentationUserFormatPreferenceService.build_decision(
                preferred,
                rows=rows,
                user_message=message,
                available_formats=available_formats,
                intent=intent,
                tree_presentation=tree_presentation,
                primary_presentation=primary_presentation,
            )

        intent_decision = ChatPresentationOperationalIntentDecisionService.resolve(
            intent_token=intent_token,
            message=message,
            rows=rows,
            available_formats=available_formats,
            intent=intent,
            tree_presentation=tree_presentation,
            primary_presentation=primary_presentation,
            text_presentation=text_presentation,
            table_presentation=table_presentation,
            chart_presentation=chart_presentation,
            path=path,
            metadata=metadata,
            user_preference=user_preference,
        )

        if intent_decision:
            return intent_decision

        return ChatPresentationGenericDecisionService.resolve(
            intent=intent,
            rows=rows,
            user_message=user_message,
            user_preference=preferred,
            primary_presentation=primary_presentation,
            table_presentation=table_presentation,
            chart_presentation=chart_presentation,
            tree_presentation=tree_presentation,
            dashboard_presentation=dashboard_presentation,
            text_presentation=text_presentation,
            available_formats=available_formats,
            path=path,
            metadata=metadata,
        )
