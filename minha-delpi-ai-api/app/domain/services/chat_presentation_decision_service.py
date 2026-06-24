"""Escolha automática do formato de apresentação — Playbook 09 Fase 1."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_chart_type_selection_service import (
    ChatChartTypeSelectionService,
)
from app.domain.services.chat_presentation_chart_policy_service import (
    ChatPresentationChartPolicyService,
)
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
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
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

_SELECTED_TO_CHART_TYPE = {
    "line_chart": "line",
    "area_chart": "area",
    "bar_chart": "bar",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo_chart": "combo",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
    "chart": "bar",
}

_CHART_TYPE_TO_SELECTED = {
    "line": "line_chart",
    "multi_line": "line_chart",
    "area": "area_chart",
    "bar": "bar_chart",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "pie": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo": "combo_chart",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
}

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
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())
        preferred = cls._normalize_user_preference(user_preference, message)
        intent_token = str(intent or "").strip().lower()

        if preferred:
            return cls._decision_for_preference(
                preferred,
                rows=rows,
                user_message=message,
                available_formats=available_formats,
                intent=intent,
                tree_presentation=tree_presentation,
                primary_presentation=primary_presentation,
            )

        intent_decision = cls._decision_for_operational_intent(
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

        if cls._looks_like_checklist(message):
            return cls._build(
                selected="checklist",
                fallback="text",
                reason=cls._reason("checklist"),
                available_views=["checklist", "text", "canvas"],
                rows=rows,
                intent=intent,
            )

        if cls._looks_like_canvas(message):
            return cls._build(
                selected="canvas",
                fallback="text",
                reason=cls._reason("canvas"),
                available_views=["canvas", "text"],
                rows=rows,
                intent=intent,
            )

        if cls._effective_tree_presentation(
            tree_presentation=tree_presentation,
            primary_presentation=primary_presentation,
        ) and not cls._should_default_analyser_stack_to_text(
            path=path,
            text_presentation=text_presentation,
            user_preference=preferred,
        ):
            return cls._build(
                selected="tree",
                fallback="table",
                reason=cls._reason("treeHierarchy"),
                available_views=cls._merge_views(
                    available_formats,
                    ["tree", "table", "text"],
                ),
                rows=rows,
                intent=intent,
            )

        if dashboard_presentation or (
            primary_presentation and primary_presentation.get("type") == "dashboard"
        ):
            return cls._build(
                selected="dashboard",
                fallback="table",
                reason=cls._reason("dashboard"),
                available_views=cls._merge_views(
                    available_formats,
                    ["dashboard", "table", "chart", "kpi"],
                ),
                rows=rows,
                intent=intent,
            )

        kpi_presentation = cls._resolve_kpi_presentation(
            primary_presentation=primary_presentation,
            metadata=metadata,
        )

        if kpi_presentation:
            return cls._build(
                selected="kpi",
                fallback="table",
                reason=cls._reason("kpiSingle"),
                available_views=cls._merge_views(
                    available_formats,
                    ["kpi", "table", "chart", "text", "dashboard"],
                ),
                rows=rows,
                intent=intent,
            )

        table_rows = rows or cls._rows_from_metadata_tables(
            metadata if isinstance(metadata, dict) else None,
        ) or cls._rows_from_presentation(
            table_presentation or (
                primary_presentation
                if primary_presentation and primary_presentation.get("type") == "table"
                else None
            )
        )

        shape = ChatPresentationDataShapeAnalyzer.analyze(rows=table_rows)

        if shape["rows"] == 0:
            return cls._build(
                selected="text",
                fallback="text",
                reason=cls._reason("noTabularData"),
                available_views=["text"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        entity = cls._entity_from_metadata(metadata if isinstance(metadata, dict) else None)

        if not entity and path:
            from app.domain.services.chat_operational_response_profile_service import (
                ChatOperationalResponseProfileService,
            )

            resolved_entity = str(
                ChatOperationalResponseProfileService.resolve(
                    metadata if isinstance(metadata, dict) else {},
                    path=path,
                ).entity
                or ""
            ).strip()

            if resolved_entity:
                entity = resolved_entity

        from app.domain.services.chat_presentation_view_intent_service import (
            ChatPresentationViewIntentService,
        )

        prefer_table = ChatPresentationViewIntentService.prefers_table_for_automatic(
            path=path,
            entity=entity,
            data_shape=shape,
            user_message=message,
            has_table=bool(table_rows),
        )

        if prefer_table:
            return cls._build(
                selected="table",
                fallback="text",
                reason=cls._reason("auditableList"),
                available_views=cls._merge_views(
                    available_formats,
                    ["table", "chart", "text", "kpi"],
                ),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if (chart_presentation or (
            primary_presentation and primary_presentation.get("type") == "chart"
        )) and not prefer_table:
            chart_type = cls._resolve_chart_type(
                table_rows=table_rows,
                shape=shape,
                user_message=message,
                fallback_chart=str(
                    (chart_presentation or primary_presentation or {}).get("chartType") or "bar"
                ),
            )
            selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "chart")

            return cls._build(
                selected=selected,
                fallback="table",
                reason=cls._chart_reason(chart_type, shape),
                available_views=cls._merge_views(
                    available_formats,
                    [selected, "table", "chart", "text"],
                ),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["rows"] == 1 and shape["hasNumeric"] and len(shape.get("numericKeys") or []) == 1:
            if prefer_table:
                return cls._build(
                    selected="table",
                    fallback="text",
                    reason=cls._reason("auditableList"),
                    available_views=cls._merge_views(
                        available_formats,
                        ["table", "chart", "text", "kpi"],
                    ),
                    rows=table_rows,
                    intent=intent,
                    data_shape=shape,
                )

            return cls._build(
                selected="kpi",
                fallback="table",
                reason=cls._reason("singleNumericKpi"),
                available_views=["kpi", "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["hasHierarchy"]:
            return cls._build(
                selected="tree",
                fallback="table",
                reason=cls._reason("hierarchyDetected"),
                available_views=["tree", "table"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        numeric_keys = list(shape.get("numericKeys") or [])

        if len(numeric_keys) >= 2 and table_rows:
            lowered = {key.lower() for key in numeric_keys}
            has_target = any(
                any(token in key for token in ("meta", "target", "goal", "objetivo"))
                for key in lowered
            )
            has_actual = any(
                any(token in key for token in ("realizado", "actual", "atual", "valor"))
                for key in lowered
            )

            if has_target and has_actual or any(
                token in message for token in ("versus", " vs ", "meta", "compar")
            ):
                label_key = shape.get("labelKey") or "label"
                chart_type = ChatChartTypeSelectionService.resolve(
                    rows=table_rows[:24],
                    label_key=str(label_key),
                    numeric_keys=numeric_keys[:3],
                    user_message=message or None,
                )
                selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "grouped_bar")

                return cls._build(
                    selected=selected,
                    fallback="table",
                    reason=cls._reason("targetVsActual"),
                    available_views=cls._merge_views(
                        available_formats,
                        [selected, "kpi", "table", "chart"],
                    ),
                    rows=table_rows,
                    intent=intent,
                    data_shape=shape,
                )

        if shape["hasDate"] and shape["hasNumeric"] and table_rows:
            label_key = shape.get("labelKey") or "label"
            chart_type = ChatChartTypeSelectionService.resolve(
                rows=table_rows[:24],
                label_key=str(label_key),
                numeric_keys=numeric_keys or ["value"],
                user_message=message or None,
            )
            selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "line_chart")

            return cls._build(
                selected=selected,
                fallback="table",
                reason=cls._reason("temporalNumeric"),
                available_views=cls._merge_views(
                    available_formats,
                    [selected, "table", "chart"],
                ),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if (
            shape["hasNumeric"]
            and shape["categoryCardinality"] > 6
            and table_rows
        ):
            return cls._build(
                selected="horizontal_bar",
                fallback="table",
                reason=cls._reason("manyCategoriesRanking"),
                available_views=["horizontal_bar", "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if (
            shape["hasNumeric"]
            and 3 <= shape["categoryCardinality"] <= 6
            and table_rows
        ):
            label_key = shape.get("labelKey") or "label"
            numeric_keys = list(shape.get("numericKeys") or ["value"])
            chart_type = ChatChartTypeSelectionService.resolve(
                rows=table_rows[:12],
                label_key=str(label_key),
                numeric_keys=numeric_keys,
                user_message=message or None,
            )
            selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "donut")

            return cls._build(
                selected=selected,
                fallback="table",
                reason=cls._reason("categoryParticipation"),
                available_views=[selected, "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if text_presentation and not table_rows:
            return cls._build(
                selected="text",
                fallback="text",
                reason=cls._reason("explanatoryNoTable"),
                available_views=["text"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        return cls._build(
            selected="table",
            fallback="text",
            reason=cls._reason("auditableList"),
            available_views=cls._merge_views(
                available_formats,
                ["table", "chart", "text"],
            ),
            rows=table_rows,
            intent=intent,
            data_shape=shape,
        )

    @classmethod
    def _resolve_effective_user_preference(
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

    @staticmethod
    def _resolve_kpi_presentation(
        *,
        primary_presentation: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if isinstance(primary_presentation, dict) and primary_presentation.get("type") == "kpi":
            return primary_presentation

        if not isinstance(metadata, dict):
            return None

        kpi_slot = metadata.get("kpiPresentation")

        if isinstance(kpi_slot, dict) and kpi_slot.get("type") == "kpi":
            return kpi_slot

        return None

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
        from app.domain.services.chat_chart_data_aggregation_service import (
            ChatChartDataAggregationService,
        )

        for key in ("chartPresentation", "presentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "chart":
                continue

            ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

        dashboard = metadata.get("presentation")

        if not isinstance(dashboard, dict) or dashboard.get("type") != "dashboard":
            return

        for panel in dashboard.get("panels") or []:
            if not isinstance(panel, dict):
                continue

            chart = panel.get("chartPresentation")

            if isinstance(chart, dict) and chart.get("type") == "chart":
                ChatChartDataAggregationService.apply_to_chart_presentation(chart)

            presentation = panel.get("presentation")

            if isinstance(presentation, dict) and presentation.get("type") == "chart":
                ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

    @classmethod
    def _apply_chart_policy_to_metadata(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        user_message: str | None = None,
    ) -> str | None:
        selected = str(decision.get("selected") or "")
        chart_type = _SELECTED_TO_CHART_TYPE.get(selected)

        if not chart_type:
            return None

        notices: list[str] = []

        for key in ("presentation", "chartPresentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "chart":
                continue

            config = presentation.get("config")

            if not isinstance(config, dict):
                config = {}
                presentation["config"] = config

            label_key = str(config.get("xAxis") or decision.get("dataShape", {}).get("labelKey") or "")
            y_axis = config.get("yAxis")
            value_key = y_axis[0] if isinstance(y_axis, list) and y_axis else None

            original = presentation.get("data") or []
            original_count = len(original) if isinstance(original, list) else 0

            capped = ChatPresentationChartPolicyService.apply(
                original if isinstance(original, list) else [],
                chart_type,
                label_key=label_key or None,
                value_key=str(value_key) if value_key else None,
            )

            presentation["chartType"] = chart_type
            config["recommendedChartType"] = chart_type
            presentation["data"] = capped

            from app.domain.services.chat_presentation_axis_preference_service import (
                ChatPresentationAxisPreferenceService,
            )

            ChatPresentationAxisPreferenceService.apply_to_chart_config(
                presentation,
                user_message=user_message,
            )

            from app.domain.services.chat_chart_data_aggregation_service import (
                ChatChartDataAggregationService,
            )

            ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

            notice = ChatPresentationChartPolicyService.fallback_notice(
                chart_type,
                original_count,
                len(capped),
            )

            if notice:
                notices.append(notice)

        return notices[0] if notices else None

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
        normalized_views = {
            cls._view_from_legacy_format(str(token))
            for token in (available_formats or [])
        }
        resolved = preferred

        effective_tree = cls._effective_tree_presentation(
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
            and cls._is_product_field_value_table(rows)
            and "text" in normalized_views
        ):
            from app.domain.services.chat_product_overview_intent_service import (
                ChatProductOverviewIntentService,
            )

            if ChatProductOverviewIntentService.is_product_overview_message(user_message):
                resolved = "text"

        fallback = "table" if rows else "text"
        views = cls._merge_views(available_formats, [resolved, fallback, "text"])
        reason = (
            cls._reason("formatUnavailableFallback")
            if resolved != preferred
            else cls._reason("formatUserRequested")
        )

        return cls._build(
            selected=resolved,
            fallback=fallback,
            reason=reason,
            available_views=views,
            rows=rows,
            intent=intent,
        )

    @classmethod
    def _normalize_user_preference(
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
        if table_rows and shape.get("hasNumeric"):
            label_key = str(shape.get("labelKey") or "label")
            numeric_keys = list(shape.get("numericKeys") or ["value"])

            return ChatChartTypeSelectionService.resolve(
                rows=table_rows[:24],
                label_key=label_key,
                numeric_keys=numeric_keys,
                user_message=user_message or None,
            )

        return str(fallback_chart or "bar").strip() or "bar"

    @classmethod
    def _chart_reason(cls, chart_type: str, shape: dict[str, Any]) -> str:
        if chart_type in {"line", "multi_line", "area"}:
            return cls._reason("temporalNumeric")

        if chart_type in {"donut", "pie"}:
            return cls._reason("categoryParticipation")

        if chart_type == "horizontal_bar":
            return cls._reason("chartRankingLongNames")

        if shape.get("rows", 0) > 6:
            return cls._reason("chartCategoryVolume")

        return cls._reason("chartComparableNumeric")

    @classmethod
    def _looks_like_checklist(cls, message: str) -> bool:
        if not message:
            return False

        return any(
            token in message
            for token in ChatPresentationVocabularyService.intent_markers("checklist")
        )

    @classmethod
    def _looks_like_canvas(cls, message: str) -> bool:
        if not message:
            return False

        return any(
            token in message
            for token in ChatPresentationVocabularyService.intent_markers("canvas")
        )
