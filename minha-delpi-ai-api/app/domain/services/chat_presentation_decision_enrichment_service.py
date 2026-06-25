"""Pós-processamento de metadata — decisão, insight, recomendações e contrato MFE."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_automatic_score_service import (
    ChatPresentationAutomaticScoreService,
)
from app.domain.services.chat_presentation_chart_decision_service import (
    ChatPresentationChartDecisionService,
)
from app.domain.services.chat_presentation_decision_builder_service import (
    ChatPresentationDecisionBuilderService,
)
from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_insight_service import (
    ChatPresentationInsightService,
)
from app.domain.services.chat_presentation_route_visual_policy_service import (
    ChatPresentationRouteVisualPolicyService,
)
from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationDecisionEnrichmentService:
    @classmethod
    def enrich(
        cls,
        metadata: dict[str, Any],
        *,
        intent: str | None = None,
        user_message: str | None = None,
        user_preference: str | None = None,
        axis_user_message: str | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_presentation_decision_service import (
            ChatPresentationDecisionService,
        )

        primary_presentation = metadata.get("presentation")
        tree_presentation = ChatPresentationDecisionMetadataService.effective_tree_presentation(
            tree_presentation=metadata.get("treePresentation"),
            primary_presentation=primary_presentation,
        )

        path = str(metadata.get("path") or "").strip()
        effective_preference = ChatPresentationUserFormatPreferenceService.resolve_effective(
            metadata,
            user_preference,
        )

        decision = ChatPresentationDecisionService.decide(
            intent=intent,
            rows=ChatPresentationDecisionMetadataService.rows_from_metadata_tables(metadata),
            user_message=user_message,
            user_preference=effective_preference,
            primary_presentation=primary_presentation,
            table_presentation=metadata.get("tablePresentation"),
            chart_presentation=metadata.get("chartPresentation"),
            tree_presentation=tree_presentation,
            dashboard_presentation=ChatPresentationDecisionMetadataService.resolve_dashboard_presentation(
                metadata,
            ),
            text_presentation=metadata.get("textPresentation"),
            available_formats=metadata.get("availableFormats"),
            path=path or None,
            metadata=metadata,
        )

        table_rows = ChatPresentationDecisionMetadataService.rows_from_metadata_tables(metadata)
        entity = ChatPresentationDecisionMetadataService.resolve_entity(metadata, path=path or None)

        ChatPresentationAutomaticScoreService.attach_scores_and_reading_layers(
            decision,
            metadata=metadata,
            table_rows=table_rows,
            user_message=user_message,
        )
        ChatPresentationAutomaticScoreService.apply_automatic_score_selection(
            decision,
            metadata=metadata,
            effective_preference=effective_preference,
            user_message=user_message,
            path=path or None,
            entity=entity,
        )
        ChatPresentationAutomaticScoreService.ensure_purpose(
            decision,
            metadata=metadata,
            user_message=user_message,
        )

        cls._attach_insight(
            decision,
            metadata=metadata,
            table_rows=table_rows,
            tree_presentation=tree_presentation,
        )

        policy_notice = ChatPresentationChartDecisionService.apply_policy_to_metadata(
            metadata,
            decision,
            user_message=axis_user_message or user_message,
        )

        if policy_notice:
            decision["policyNotice"] = policy_notice
            decision["insight"] = f"{decision['insight']} {policy_notice}".strip()

        cls._attach_chart_explanation(metadata, decision, path=path)
        cls._attach_dashboard_explanation(metadata, decision)

        from app.domain.services.chat_presentation_recommendation_service import (
            ChatPresentationRecommendationService,
        )

        recommendations = ChatPresentationRecommendationService.build(
            decision=decision,
            user_message=axis_user_message or user_message,
            metadata=metadata,
        )

        if recommendations:
            decision["recommendations"] = recommendations

        ChatPresentationRecommendationService.prune_for_selected(decision)

        ChatPresentationChartDecisionService.apply_category_aggregation(metadata)
        ChatPresentationRouteVisualPolicyService.apply(metadata, decision)

        cls._apply_text_first_and_integrated_stack(
            metadata,
            decision,
            path=path or None,
            entity=entity,
            effective_preference=effective_preference,
            user_message=user_message,
        )

        ChatPresentationRecommendationService.prune_for_selected(decision)

        from app.domain.services.chat_presentation_structure_dedup_service import (
            ChatPresentationStructureDedupService,
        )

        views = decision.get("availableViews")

        if isinstance(views, list):
            decision["availableViews"] = ChatPresentationStructureDedupService.prune_available_views(
                views,
                metadata,
            )

        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        if str(metadata.get("explicitSessionFormat") or "").strip():
            ChatPresentationTextModeService.align_explicit_session_decision(metadata)

        from app.domain.services.chat_presentation_generic_decision_service import (
            ChatPresentationGenericDecisionService,
        )

        if ChatPresentationGenericDecisionService._has_narrative_payload(
            text_presentation=metadata.get("textPresentation")
            if isinstance(metadata.get("textPresentation"), dict)
            else None,
            metadata=metadata,
        ):
            cls._sanitize_zero_row_reason(
                decision,
                reason=ChatPresentationVocabularyService.decision_reason,
            )

        metadata["presentationDecision"] = decision

        legacy = ChatPresentationDecisionBuilderService.legacy_preferred_format(
            decision.get("selected"),
        )

        if legacy:
            metadata["preferredFormat"] = legacy

        views = decision.get("availableViews") or []

        if views:
            metadata["availableFormats"] = ChatPresentationDecisionBuilderService.legacy_available_formats(
                views,
            )

        return metadata

    @classmethod
    def _attach_insight(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        table_rows: list[dict[str, Any]],
        tree_presentation: dict[str, Any] | None,
    ) -> None:
        shape = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}
        narrative_markdown = ""

        if isinstance(metadata.get("textPresentation"), dict):
            narrative_markdown = str(metadata["textPresentation"].get("markdown") or "").strip()

        insight_shape = {
            **shape,
            "labelKey": shape.get("labelKey"),
            "treeNodes": ChatPresentationDecisionMetadataService.tree_node_count(tree_presentation),
            "hasNarrative": bool(narrative_markdown),
        }

        decision["insight"] = ChatPresentationInsightService.build_with_metadata(
            selected=str(decision.get("selected") or ""),
            rows=table_rows,
            data_shape=insight_shape,
            reason=str(decision.get("reason") or ""),
            metadata=metadata,
        )

        if str(decision.get("layoutMode") or "") == "stack" and narrative_markdown:
            decision["insight"] = ChatPresentationDecisionMetadataService.stack_commentary_insight(
                metadata,
            )

    @classmethod
    def _attach_chart_explanation(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        path: str,
    ) -> None:
        chart_presentation = metadata.get("chartPresentation") or metadata.get("presentation")

        if not isinstance(chart_presentation, dict) or chart_presentation.get("type") != "chart":
            return

        from app.domain.services.chat_presentation_chart_explain_service import (
            ChatPresentationChartExplainService,
        )

        explanation = ChatPresentationChartExplainService.build(
            presentation=chart_presentation,
            decision=decision,
            insight=str(decision.get("insight") or ""),
            path=str(path or metadata.get("sourcePath") or "").strip(),
        )

        if explanation:
            decision["chartExplanation"] = explanation

    @classmethod
    def _attach_dashboard_explanation(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
    ) -> None:
        dashboard_presentation = metadata.get("presentation")

        if (
            not isinstance(dashboard_presentation, dict)
            or dashboard_presentation.get("type") != "dashboard"
        ):
            return

        from app.domain.services.chat_presentation_dashboard_explain_service import (
            ChatPresentationDashboardExplainService,
        )

        ChatPresentationDashboardExplainService.enrich_panel_charts(
            dashboard_presentation,
            decision=decision,
        )

        dashboard_explanation = ChatPresentationDashboardExplainService.build(
            presentation=dashboard_presentation,
            decision=decision,
            insight=str(decision.get("insight") or ""),
        )

        if dashboard_explanation:
            decision["dashboardExplanation"] = dashboard_explanation

    @classmethod
    def _sanitize_zero_row_reason(
        cls,
        decision: dict[str, Any],
        *,
        reason,
    ) -> None:
        current = str(decision.get("reason") or "").strip()

        if not current:
            return

        internal = {
            reason("noTabularData"),
            reason("explanatoryNoTable"),
        }

        if current in internal:
            decision["reason"] = ""

    @classmethod
    def _apply_text_first_and_integrated_stack(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        path: str | None,
        entity: str | None,
        effective_preference: str | None,
        user_message: str | None,
    ) -> None:
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        reason = ChatPresentationVocabularyService.decision_reason

        if ChatPresentationTextFirstPolicyService.should_default_to_text_only(
            path=path,
            entity=entity,
            explicit_format=effective_preference,
            user_message=user_message,
        ):
            latent = ChatPresentationTextFirstPolicyService.latent_available_views(
                path=path,
                entity=entity,
                has_text=bool(metadata.get("textPresentation")),
            )
            merged_views = ChatPresentationDecisionBuilderService.merge_views(
                metadata.get("availableFormats"),
                latent,
            )
            decision["selected"] = "text"
            decision["layoutMode"] = "single"
            decision["visualOrder"] = ["text"] if "text" in merged_views else merged_views[:1]
            decision["availableViews"] = merged_views

            cls._sanitize_zero_row_reason(decision, reason=reason)

            if not str(decision.get("reason") or "").strip():
                decision["reason"] = reason("textFirstDefault")

        if (
            not effective_preference
            and ChatPresentationTextFirstPolicyService.looks_like_integrated_stack_request(
                user_message,
            )
        ):
            merged_views = ChatPresentationDecisionBuilderService.merge_views(
                metadata.get("availableFormats"),
                decision.get("availableViews"),
            )

            if len(merged_views) >= 2:
                decision["selected"] = "text"
                decision["availableViews"] = merged_views
                decision["layoutMode"] = "stack"
                decision["visualOrder"] = ChatPresentationDecisionBuilderService.visual_order_for_stack(
                    merged_views,
                )
                decision["reason"] = reason("integratedStack")
