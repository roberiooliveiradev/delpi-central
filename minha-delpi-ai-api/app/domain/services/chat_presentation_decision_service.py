"""Escolha automática do formato de apresentação — Playbook 09 Fase 1."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_insight_service import (
    ChatPresentationInsightService,
)
from app.domain.services.chat_presentation_automatic_score_service import (
    ChatPresentationAutomaticScoreService,
)
from app.domain.services.chat_presentation_decision_builder_service import (
    ChatPresentationDecisionBuilderService,
)
from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_operational_intent_decision_service import (
    ChatPresentationOperationalIntentDecisionService,
)
from app.domain.services.chat_presentation_chart_decision_service import (
    ChatPresentationChartDecisionService,
)
from app.domain.services.chat_presentation_generic_decision_service import (
    ChatPresentationGenericDecisionService,
)
from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)



class ChatPresentationDecisionService:
    @classmethod
    def _reason(cls, key: str) -> str:
        return ChatPresentationVocabularyService.decision_reason(key)

    @classmethod
    def _route_reason(cls, key: str) -> str:
        return ChatPresentationVocabularyService.route_policy_reason(key)

    @classmethod
    def _tree_node_count(cls, tree_presentation: dict[str, Any] | None) -> int | bool:
        return ChatPresentationDecisionMetadataService.tree_node_count(tree_presentation)

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

    @classmethod
    def _attach_scores_and_reading_layers(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        table_rows: list[dict[str, Any]] | None,
        user_message: str | None,
    ) -> None:
        ChatPresentationAutomaticScoreService.attach_scores_and_reading_layers(
            decision,
            metadata=metadata,
            table_rows=table_rows,
            user_message=user_message,
        )

    @classmethod
    def _score_bucket_for_view(cls, view: str) -> str:
        return ChatPresentationAutomaticScoreService.score_bucket_for_view(view)

    @classmethod
    def _score_for_view(cls, view: str, scores: dict[str, int]) -> int:
        return ChatPresentationAutomaticScoreService.score_for_view(view, scores)

    @classmethod
    def _resolve_chart_selected_token(
        cls,
        decision: dict[str, Any],
        available_views: list[str],
    ) -> str:
        return ChatPresentationAutomaticScoreService.resolve_chart_selected_token(
            decision,
            available_views,
        )

    @classmethod
    def _should_skip_automatic_score_selection(
        cls,
        *,
        metadata: dict[str, Any],
        effective_preference: str | None,
        user_message: str | None,
        path: str | None,
        entity: str | None,
        decision: dict[str, Any] | None = None,
    ) -> bool:
        return ChatPresentationAutomaticScoreService.should_skip_automatic_score_selection(
            metadata=metadata,
            effective_preference=effective_preference,
            user_message=user_message,
            path=path,
            entity=entity,
            decision=decision,
        )

    @classmethod
    def _apply_automatic_score_selection(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        effective_preference: str | None,
        user_message: str | None,
        path: str | None,
        entity: str | None,
    ) -> None:
        ChatPresentationAutomaticScoreService.apply_automatic_score_selection(
            decision,
            metadata=metadata,
            effective_preference=effective_preference,
            user_message=user_message,
            path=path,
            entity=entity,
        )

    @classmethod
    def _entity_from_metadata(cls, metadata: dict[str, Any] | None) -> str | None:
        return ChatPresentationDecisionMetadataService.entity_from_metadata(metadata)

    @classmethod
    def _view_has_presentation(cls, metadata: dict[str, Any], view: str) -> bool:
        return ChatPresentationDecisionMetadataService.view_has_presentation(metadata, view)

    @classmethod
    def _metadata_has_visual(cls, metadata: dict[str, Any]) -> bool:
        return ChatPresentationDecisionMetadataService.metadata_has_visual(metadata)

    @classmethod
    def _rows_from_metadata_tables(cls, metadata: dict[str, Any] | None) -> list[dict[str, Any]]:
        return ChatPresentationDecisionMetadataService.rows_from_metadata_tables(metadata)

    @classmethod
    def _ensure_purpose(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        user_message: str | None,
    ) -> None:
        ChatPresentationAutomaticScoreService.ensure_purpose(
            decision,
            metadata=metadata,
            user_message=user_message,
        )

    @classmethod
    def _message_from_metadata(cls, metadata: dict[str, Any]) -> str:
        return ChatPresentationDecisionMetadataService.message_from_metadata(metadata)

    @classmethod
    def _stack_commentary_insight(cls, metadata: dict[str, Any]) -> str:
        return ChatPresentationDecisionMetadataService.stack_commentary_insight(metadata)

    @classmethod
    def _effective_tree_presentation(
        cls,
        *,
        tree_presentation: dict[str, Any] | None = None,
        primary_presentation: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return ChatPresentationDecisionMetadataService.effective_tree_presentation(
            tree_presentation=tree_presentation,
            primary_presentation=primary_presentation,
        )

    @classmethod
    def _resolve_dashboard_presentation(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        return ChatPresentationDecisionMetadataService.resolve_dashboard_presentation(metadata)

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

    @classmethod
    def _resolve_effective_user_preference(
        cls,
        metadata: dict[str, Any],
        user_preference: str | None,
    ) -> str | None:
        return ChatPresentationUserFormatPreferenceService.resolve_effective(
            metadata,
            user_preference,
        )

    @staticmethod
    def _resolve_kpi_presentation(
        *,
        primary_presentation: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        return ChatPresentationGenericDecisionService.resolve_kpi_presentation(
            primary_presentation=primary_presentation,
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
        primary_presentation = metadata.get("presentation")
        tree_presentation = cls._effective_tree_presentation(
            tree_presentation=metadata.get("treePresentation"),
            primary_presentation=primary_presentation,
        )

        path = str(metadata.get("path") or "").strip()
        effective_preference = cls._resolve_effective_user_preference(
            metadata,
            user_preference,
        )

        decision = cls.decide(
            intent=intent,
            rows=cls._rows_from_metadata_tables(metadata),
            user_message=user_message,
            user_preference=effective_preference,
            primary_presentation=primary_presentation,
            table_presentation=metadata.get("tablePresentation"),
            chart_presentation=metadata.get("chartPresentation"),
            tree_presentation=tree_presentation,
            dashboard_presentation=cls._resolve_dashboard_presentation(metadata),
            text_presentation=metadata.get("textPresentation"),
            available_formats=metadata.get("availableFormats"),
            path=path or None,
            metadata=metadata,
        )

        table_rows = cls._rows_from_metadata_tables(metadata)
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        if not entity and path:
            from app.domain.services.chat_operational_response_profile_service import (
                ChatOperationalResponseProfileService,
            )

            resolved_entity = str(
                ChatOperationalResponseProfileService.resolve(metadata, path=path).entity or ""
            ).strip()

            if resolved_entity:
                entity = resolved_entity

        cls._attach_scores_and_reading_layers(
            decision,
            metadata=metadata,
            table_rows=table_rows,
            user_message=user_message,
        )
        cls._apply_automatic_score_selection(
            decision,
            metadata=metadata,
            effective_preference=effective_preference,
            user_message=user_message,
            path=path or None,
            entity=entity,
        )
        cls._ensure_purpose(
            decision,
            metadata=metadata,
            user_message=user_message,
        )
        shape = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}
        narrative_markdown = ""

        if isinstance(metadata.get("textPresentation"), dict):
            narrative_markdown = str(metadata["textPresentation"].get("markdown") or "").strip()

        insight_shape = {
            **shape,
            "labelKey": shape.get("labelKey"),
            "treeNodes": cls._tree_node_count(tree_presentation),
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
            commentary_insight = cls._stack_commentary_insight(metadata)

            decision["insight"] = commentary_insight

        policy_notice = cls._apply_chart_policy_to_metadata(
            metadata,
            decision,
            user_message=axis_user_message or user_message,
        )

        if policy_notice:
            decision["policyNotice"] = policy_notice
            decision["insight"] = f"{decision['insight']} {policy_notice}".strip()

        chart_presentation = metadata.get("chartPresentation") or metadata.get("presentation")

        if (
            isinstance(chart_presentation, dict)
            and chart_presentation.get("type") == "chart"
        ):
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

        dashboard_presentation = metadata.get("presentation")

        if (
            isinstance(dashboard_presentation, dict)
            and dashboard_presentation.get("type") == "dashboard"
        ):
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

        cls._apply_chart_category_aggregation(metadata)

        cls._apply_route_visual_policy(metadata, decision)

        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        if ChatPresentationTextFirstPolicyService.should_default_to_text_only(
            path=path or None,
            entity=entity,
            explicit_format=effective_preference,
            user_message=user_message,
        ):
            latent = ChatPresentationTextFirstPolicyService.latent_available_views(
                path=path or None,
                entity=entity,
                has_text=bool(metadata.get("textPresentation")),
            )
            merged_views = cls._merge_views(metadata.get("availableFormats"), latent)
            decision["selected"] = "text"
            decision["layoutMode"] = "single"
            decision["visualOrder"] = ["text"] if "text" in merged_views else merged_views[:1]
            decision["availableViews"] = merged_views
            if not str(decision.get("reason") or "").strip():
                decision["reason"] = cls._reason("textFirstDefault")

        if (
            not effective_preference
            and ChatPresentationTextFirstPolicyService.looks_like_integrated_stack_request(
                user_message,
            )
        ):
            merged_views = cls._merge_views(
                metadata.get("availableFormats"),
                decision.get("availableViews"),
            )

            if len(merged_views) >= 2:
                decision["selected"] = "text"
                decision["availableViews"] = merged_views
                decision["layoutMode"] = "stack"
                decision["visualOrder"] = cls._visual_order_for_stack(merged_views)
                decision["reason"] = cls._reason("integratedStack")

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

        metadata["presentationDecision"] = decision

        legacy = cls._legacy_preferred_format(decision.get("selected"))

        if legacy:
            metadata["preferredFormat"] = legacy

        views = decision.get("availableViews") or []

        if views:
            metadata["availableFormats"] = cls._legacy_available_formats(views)

        return metadata

    @classmethod
    def _build(
        cls,
        *,
        selected: str,
        fallback: str,
        reason: str,
        available_views: list[str],
        rows: list[dict[str, Any]] | None,
        intent: str | None,
        data_shape: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationDecisionBuilderService.build(
            selected=selected,
            fallback=fallback,
            reason=reason,
            available_views=available_views,
            rows=rows,
            intent=intent,
            data_shape=data_shape,
        )

    @classmethod
    def _apply_rich_text_stack_layout(cls, decision: dict[str, Any]) -> dict[str, Any]:
        return ChatPresentationDecisionBuilderService.apply_rich_text_stack_layout(decision)

    @classmethod
    def _apply_chart_category_aggregation(cls, metadata: dict[str, Any]) -> None:
        ChatPresentationChartDecisionService.apply_category_aggregation(metadata)

    @classmethod
    def _apply_chart_policy_to_metadata(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        user_message: str | None = None,
    ) -> str | None:
        return ChatPresentationChartDecisionService.apply_policy_to_metadata(
            metadata,
            decision,
            user_message=user_message,
        )

    @classmethod
    def _should_default_analyser_stack_to_text(
        cls,
        *,
        path: str | None,
        text_presentation: dict[str, Any] | None,
        user_preference: str | None,
    ) -> bool:
        return ChatPresentationOperationalIntentDecisionService.should_default_analyser_stack_to_text(
            path=path,
            text_presentation=text_presentation,
            user_preference=user_preference,
        )

    @classmethod
    def _decision_for_operational_intent(
        cls,
        *,
        intent_token: str,
        message: str,
        rows: list[dict[str, Any]] | None,
        available_formats: list[str] | None,
        intent: str | None,
        tree_presentation: dict[str, Any] | None,
        primary_presentation: dict[str, Any] | None,
        text_presentation: dict[str, Any] | None,
        table_presentation: dict[str, Any] | None,
        chart_presentation: dict[str, Any] | None,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
        user_preference: str | None = None,
    ) -> dict[str, Any] | None:
        return ChatPresentationOperationalIntentDecisionService.resolve(
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

    @classmethod
    def _is_product_field_value_table(cls, rows: list[dict[str, Any]] | None) -> bool:
        return ChatPresentationDecisionMetadataService.is_product_field_value_table(rows)

    @classmethod
    def _decision_for_preference(
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
        return ChatPresentationUserFormatPreferenceService.build_decision(
            preferred,
            rows=rows,
            user_message=user_message,
            available_formats=available_formats,
            intent=intent,
            tree_presentation=tree_presentation,
            primary_presentation=primary_presentation,
        )

    @classmethod
    def _normalize_user_preference(
        cls,
        user_preference: str | None,
        message: str,
    ) -> str | None:
        return ChatPresentationUserFormatPreferenceService.normalize_from_message(
            user_preference,
            message,
        )

    @classmethod
    def _rows_from_presentation(
        cls,
        presentation: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        return ChatPresentationDecisionMetadataService.rows_from_presentation(presentation)

    @classmethod
    def _visual_order_for_stack(cls, available_views: list[str]) -> list[str]:
        return ChatPresentationDecisionBuilderService.visual_order_for_stack(available_views)

    @classmethod
    def _apply_route_visual_policy(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
    ) -> None:
        from app.domain.services.chat_presentation_route_policy_service import (
            ChatPresentationRoutePolicyService,
        )

        path = str(metadata.get("path") or "")
        views = list(decision.get("availableViews") or [])

        if views:
            ChatPresentationRoutePolicyService.apply_visual_order(
                decision,
                path=path,
                metadata=metadata,
            )

        has_tree = bool(
            cls._effective_tree_presentation(
                tree_presentation=metadata.get("treePresentation"),
                primary_presentation=metadata.get("presentation"),
            )
        )

        preferred = str(metadata.get("preferredFormat") or "").strip().lower()

        if (
            has_tree
            and preferred == "tree"
            and ChatPresentationRoutePolicyService.is_tree_route(path)
            and not ChatPresentationRoutePolicyService.is_analyser_route(path)
            and decision.get("selected") in {None, "text", "table"}
        ):
            decision["selected"] = "tree"
            decision["reason"] = cls._reason("treePrimaryView")

        if (
            ChatPresentationRoutePolicyService.is_stock_route(path)
            and preferred in {"chart", "table", "tree"}
            and preferred in set(views)
            and str(decision.get("selected") or "").strip().lower() != "text"
            and str(decision.get("layoutMode") or "").strip().lower() != "stack"
        ):
            decision["selected"] = preferred
            if preferred == "chart":
                decision["reason"] = cls._route_reason("stockChart")
            elif preferred == "table":
                decision["reason"] = cls._route_reason("stockTable")
            else:
                decision["reason"] = cls._reason("treePrimaryView")

        if (
            ChatPresentationRoutePolicyService.is_table_route(path)
            and not ChatPresentationRoutePolicyService.is_tree_route(path)
            and not ChatPresentationRoutePolicyService.is_analyser_route(path)
            and preferred == "table"
            and "table" in views
        ):
            decision["selected"] = "table"
            decision["reason"] = cls._reason("operationalTableNative")

    @classmethod
    def _merge_views(
        cls,
        available_formats: list[str] | None,
        defaults: list[str],
    ) -> list[str]:
        return ChatPresentationDecisionBuilderService.merge_views(available_formats, defaults)

    @classmethod
    def _view_from_legacy_format(cls, token: str) -> str:
        return ChatPresentationDecisionBuilderService.view_from_legacy_format(token)

    @classmethod
    def _legacy_preferred_format(cls, selected: str | None) -> str | None:
        return ChatPresentationDecisionBuilderService.legacy_preferred_format(selected)

    @classmethod
    def _legacy_available_formats(cls, views: list[str]) -> list[str]:
        return ChatPresentationDecisionBuilderService.legacy_available_formats(views)

    @classmethod
    def _resolve_chart_type(
        cls,
        *,
        table_rows: list[dict[str, Any]],
        shape: dict[str, Any],
        user_message: str,
        fallback_chart: str,
    ) -> str:
        return ChatPresentationChartDecisionService.resolve_chart_type(
            table_rows=table_rows,
            shape=shape,
            user_message=user_message,
            fallback_chart=fallback_chart,
        )

    @classmethod
    def _chart_reason(cls, chart_type: str, shape: dict[str, Any]) -> str:
        return ChatPresentationChartDecisionService.chart_reason(chart_type, shape)

    @classmethod
    def _looks_like_checklist(cls, message: str) -> bool:
        return ChatPresentationGenericDecisionService.looks_like_checklist(message)

    @classmethod
    def _looks_like_canvas(cls, message: str) -> bool:
        return ChatPresentationGenericDecisionService.looks_like_canvas(message)
