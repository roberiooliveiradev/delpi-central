"""Decisão por intenção operacional — rich stack, árvore, narrativas por perfil."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_decision_builder_service import (
    ChatPresentationDecisionBuilderService,
)
from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_operational_decision_service import (
    ChatPresentationOperationalDecisionService,
)
from app.domain.services.chat_presentation_rich_stack_policy_service import (
    ChatPresentationRichStackPolicyService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from app.domain.services.chat_presentation_view_intent_service import (
    ChatPresentationViewIntentService,
)


class ChatPresentationOperationalIntentDecisionService:
    @classmethod
    def should_default_analyser_stack_to_text(
        cls,
        *,
        path: str | None,
        text_presentation: dict[str, Any] | None,
        user_preference: str | None,
    ) -> bool:
        if user_preference:
            return False

        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        if not ChatPresentationProfileService.has_flag(path, "analyser"):
            return False

        if not isinstance(text_presentation, dict):
            return False

        return bool(str(text_presentation.get("markdown") or "").strip())

    @classmethod
    def resolve(
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
        rich_metadata = metadata if isinstance(metadata, dict) else {
            "path": path,
            "textPresentation": text_presentation,
            "treePresentation": tree_presentation,
            "chartPresentation": chart_presentation,
            "tablePresentation": table_presentation,
            "presentation": primary_presentation,
        }
        entity = ChatPresentationDecisionMetadataService.entity_from_metadata(rich_metadata)
        reason = ChatPresentationVocabularyService.decision_reason

        if ChatPresentationRichStackPolicyService.should_default_to_text_stack(
            path=path,
            metadata=rich_metadata,
            entity=entity,
            user_preference=user_preference,
            user_message=message,
        ):
            table_rows = rows or ChatPresentationDecisionMetadataService.rows_from_metadata_tables(
                rich_metadata,
            ) or ChatPresentationDecisionMetadataService.rows_from_presentation(
                table_presentation
                or (
                    primary_presentation
                    if isinstance(primary_presentation, dict)
                    and primary_presentation.get("type") == "table"
                    else None
                )
            )
            views = ChatPresentationRichStackPolicyService.resolve_available_views(
                rich_metadata,
                path=path,
                entity=entity,
                available_formats=available_formats,
            )

            decision = ChatPresentationDecisionBuilderService.build(
                selected="text",
                fallback="table",
                reason=ChatPresentationRichStackPolicyService.stack_reason_for_route(
                    path,
                    entity=entity,
                ),
                available_views=views
                or ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["text", "table", "tree", "chart", "kpi", "dashboard"],
                ),
                rows=table_rows,
                intent=intent,
            )

            return ChatPresentationDecisionBuilderService.apply_rich_text_stack_layout(decision)

        if cls.should_default_analyser_stack_to_text(
            path=path,
            text_presentation=text_presentation,
            user_preference=user_preference,
        ):
            table_rows = rows or ChatPresentationDecisionMetadataService.rows_from_metadata_tables(
                rich_metadata,
            ) or ChatPresentationDecisionMetadataService.rows_from_presentation(
                table_presentation
                or (
                    primary_presentation
                    if isinstance(primary_presentation, dict)
                    and primary_presentation.get("type") == "table"
                    else None
                )
            )

            return ChatPresentationDecisionBuilderService.build(
                selected="text",
                fallback="table",
                reason=reason("analyserIntegratedStack"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["text", "table", "tree", "chart"],
                ),
                rows=table_rows,
                intent=intent,
            )

        has_tree = bool(
            ChatPresentationDecisionMetadataService.effective_tree_presentation(
                tree_presentation=tree_presentation,
                primary_presentation=primary_presentation,
            )
        )

        if has_tree and ChatPresentationOperationalDecisionService.should_prefer_tree_primary(
            path=path,
            entity=entity,
            intent_token=intent_token,
            message=message,
            has_tree=True,
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="tree",
                fallback="table",
                reason=reason("treePrimaryView"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["tree", "table", "text"],
                ),
                rows=rows,
                intent=intent,
            )

        table_rows = rows or ChatPresentationDecisionMetadataService.rows_from_metadata_tables(
            metadata if isinstance(metadata, dict) else None,
        ) or ChatPresentationDecisionMetadataService.rows_from_presentation(
            table_presentation
            or (
                primary_presentation
                if isinstance(primary_presentation, dict)
                and primary_presentation.get("type") == "table"
                else None
            )
        )
        row_count = len(table_rows or [])

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if (
            text_presentation
            and ChatProductOverviewIntentService.is_product_overview_message(message)
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="text",
                fallback="table",
                reason=reason("productOverviewNarrative"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["text", "table", "tree", "chart"],
                ),
                rows=table_rows,
                intent=intent,
            )

        if ChatPresentationOperationalDecisionService.should_prefer_pricing_narrative(
            path=path,
            entity=entity,
            intent_token=intent_token,
            message=message,
            row_count=row_count,
            has_text=bool(text_presentation),
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="text",
                fallback="table",
                reason=reason("pricingNarrativeFirst"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["text", "table"],
                ),
                rows=table_rows,
                intent=intent,
            )

        if ChatPresentationOperationalDecisionService.should_prefer_stock_narrative(
            path=path,
            entity=entity,
            intent_token=intent_token,
            message=message,
            row_count=row_count,
            has_text=bool(text_presentation),
            has_chart=bool(chart_presentation),
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="text",
                fallback="table",
                reason=reason("stockFewPositionsText"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["text", "table", "chart"],
                ),
                rows=table_rows,
                intent=intent,
            )

        if ChatPresentationOperationalDecisionService.should_prefer_stock_table_over_chart(
            path=path,
            entity=entity,
            intent_token=intent_token,
            row_count=row_count,
            has_chart=bool(chart_presentation),
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="table",
                fallback="text",
                reason=reason("stockFewRowsTable"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["table", "text", "chart"],
                ),
                rows=table_rows,
                intent=intent,
            )

        if ChatPresentationViewIntentService.prefers_table_for_automatic(
            path=path,
            entity=entity,
            data_shape=ChatPresentationDataShapeAnalyzer.analyze(rows=table_rows),
            user_message=message,
            has_table=bool(table_rows),
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="table",
                fallback="text",
                reason=reason("auditableList"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["table", "chart", "text"],
                ),
                rows=table_rows,
                intent=intent,
            )

        if ChatPresentationOperationalDecisionService.should_prefer_analyser_text_stack(
            path=path,
            entity=entity,
            has_text=bool(text_presentation),
        ):
            return ChatPresentationDecisionBuilderService.build(
                selected="text",
                fallback="table",
                reason=reason("analyserFullStack"),
                available_views=ChatPresentationDecisionBuilderService.merge_views(
                    available_formats,
                    ["text", "table", "tree", "chart"],
                ),
                rows=table_rows,
                intent=intent,
            )

        return None
