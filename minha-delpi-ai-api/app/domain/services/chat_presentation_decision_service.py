"""Fachada pública de decisão de apresentação — delega aos módulos canônicos (jun/2026)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_automatic_score_service import (
    ChatPresentationAutomaticScoreService,
)
from app.domain.services.chat_presentation_decide_service import (
    ChatPresentationDecideService,
)
from app.domain.services.chat_presentation_decision_enrichment_service import (
    ChatPresentationDecisionEnrichmentService,
)


class ChatPresentationDecisionService:
    """API estável: decide, enrich_metadata, compute_scores."""

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
        return ChatPresentationDecideService.decide(
            intent=intent,
            rows=rows,
            user_message=user_message,
            user_preference=user_preference,
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

    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        intent: str | None = None,
        user_message: str | None = None,
        user_preference: str | None = None,
        axis_user_message: str | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationDecisionEnrichmentService.enrich(
            metadata,
            intent=intent,
            user_message=user_message,
            user_preference=user_preference,
            axis_user_message=axis_user_message,
        )

    @classmethod
    def compute_scores(
        cls,
        *,
        data_shape: dict[str, Any] | None,
        available_views: list[str] | None = None,
        user_message: str | None = None,
    ) -> dict[str, int]:
        return ChatPresentationAutomaticScoreService.compute_scores(
            data_shape=data_shape,
            available_views=available_views,
            user_message=user_message,
        )
