"""Metadata mínima — dados como a API entrega (Playbook 22)."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from app.domain.services.chat_data_coverage_notice_service import (
    ChatDataCoverageNoticeService,
)
from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_title_normalization_service import (
    ChatPresentationTitleNormalizationService,
)
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationApiDeliveredMetadataService:
    """Ponto de conexão simplificado: schema-driven + metadata mínima para o MFE."""

    @classmethod
    def build(
        cls,
        *,
        action: dict,
        sanitized_data: Any,
        resolved_path: str,
        request_parameters: dict,
        presenter: ExternalActionResultPresenter,
        extract_response_meta: Callable[[Any], dict | None],
    ) -> dict[str, Any]:
        session_format = str(request_parameters.get("sessionResponseFormat") or "").strip().lower()
        profile = ChatOperationalResponseProfileService.resolve(sanitized_data, path=resolved_path)
        entity = str(profile.entity or "").strip() or None
        response_schema = action.get("responseSchema")
        response_meta = extract_response_meta(sanitized_data)
        response_shape = str((response_meta or {}).get("shape") or "").strip().lower() if isinstance(response_meta, dict) else ""
        response_sections = (response_meta or {}).get("sections") if isinstance(response_meta, dict) else None
        operational_root = presenter._unwrap_data(sanitized_data)

        composite_tables: list[Any] = []
        dashboard_presentation: dict[str, Any] | None = None
        primary = None

        is_composite = ChatSchemaDrivenPresentationService.is_composite_shape(
            shape=response_shape,
            root=operational_root,
            sections=response_sections if isinstance(response_sections, list) else None,
        )

        if is_composite:
            composite = ChatSchemaDrivenPresentationService.build_composite_bundle(
                presenter,
                sanitized_data,
                path=resolved_path,
                entity=entity,
                sections=response_sections if isinstance(response_sections, list) else None,
            )
            text_presentation = composite.text
            table_presentation = composite.table
            kpi_presentation = composite.kpi
            chart_presentation = None
            tree_presentation = composite.tree
            composite_tables = list(composite.tables)
            dashboard_presentation = composite.dashboard
        else:
            primary = ChatSchemaDrivenPresentationService.finish_schema_first_primary(
                presenter,
                sanitized_data,
                path=resolved_path,
                entity=entity,
                response_schema=response_schema,
            )

            bundle = ChatSchemaDrivenPresentationService.build_bundle(
                presenter,
                sanitized_data,
                path=resolved_path,
                entity=entity,
            )

            text_presentation = bundle.text
            table_presentation = bundle.table
            kpi_presentation = bundle.kpi
            chart_presentation = bundle.chart
            tree_presentation = bundle.tree

            if isinstance(primary, dict):
                primary_type = str(primary.get("type") or "").strip().lower()

                if primary_type == "markdown" and text_presentation is None:
                    text_presentation = primary
                elif primary_type == "table":
                    table_presentation = primary
                elif primary_type == "kpi":
                    kpi_presentation = primary
                elif primary_type in {"chart", "line_chart", "bar_chart"}:
                    chart_presentation = primary
                elif primary_type == "tree":
                    tree_presentation = primary

        available_formats: list[str] = []

        if text_presentation:
            available_formats.extend(["text", "canvas"])

        if table_presentation or composite_tables:
            available_formats.append("table")

        if tree_presentation:
            available_formats.append("tree")

        if chart_presentation:
            available_formats.append("chart")

        if kpi_presentation:
            available_formats.append("kpi")

        if dashboard_presentation:
            available_formats.append("dashboard")

        if is_composite:
            primary_presentation = (
                text_presentation
                or dashboard_presentation
                or table_presentation
                or kpi_presentation
            )
        else:
            primary_presentation = (
                primary
                or table_presentation
                or text_presentation
                or kpi_presentation
            )

        preferred_format = cls._resolve_preferred_format(
            session_format=session_format,
            has_text=bool(text_presentation),
            has_table=bool(table_presentation),
            has_kpi=bool(kpi_presentation),
        )

        delpi_metadata = action.get("delpiMetadata")

        data_coverage_notice = ChatDataCoverageNoticeService.build(
            sanitized_data,
            path=resolved_path,
            parameters=request_parameters,
            presentation=primary_presentation,
            table_presentation=table_presentation,
            response_meta=response_meta,
        )

        metadata: dict[str, Any] = {
            "presentation": primary_presentation,
            "textPresentation": text_presentation,
            "tablePresentation": (
                table_presentation
                if table_presentation is not primary_presentation
                else None
            ),
            "treePresentation": (
                tree_presentation
                if tree_presentation is not primary_presentation
                else None
            ),
            "chartPresentation": (
                chart_presentation
                if chart_presentation is not primary_presentation
                else None
            ),
            "kpiPresentation": (
                kpi_presentation
                if kpi_presentation is not primary_presentation
                else None
            ),
            "availableFormats": available_formats,
            "preferredFormat": preferred_format,
            "dataCoverageNotice": data_coverage_notice,
            "path": resolved_path,
            "apiDelpiResponseMeta": response_meta,
        }

        if composite_tables:
            metadata["tablePresentations"] = composite_tables

        if dashboard_presentation:
            metadata["dashboardPresentation"] = dashboard_presentation

        if delpi_metadata:
            metadata["delpiMetadata"] = delpi_metadata

        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        ChatPresentationProfileService.cache_presentation_profile(metadata)

        if session_format:
            from app.domain.services.chat_presentation_primary_view_service import (
                ChatPresentationPrimaryViewService,
            )

            ChatPresentationPrimaryViewService.apply_session_preference(
                metadata,
                session_format,
                data=sanitized_data,
                path=resolved_path,
                presenter=presenter,
            )

        schema_labels = presenter._column_labels.merge_meta_field_labels(
            presenter._column_labels.resolve_schema_labels(response_schema),
            sanitized_data,
        )
        schema_formats = presenter._column_labels.merge_meta_field_formats(
            {},
            sanitized_data,
        )

        from app.domain.services.chat_presentation_field_normalization_service import (
            ChatPresentationFieldNormalizationService,
        )
        from app.domain.services.chat_presentation_decision_service import (
            ChatPresentationDecisionService,
        )
        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )

        ChatPresentationFieldNormalizationService.normalize_metadata(
            metadata,
            path=resolved_path,
            schema_labels=schema_labels,
            schema_formats=schema_formats,
        )

        user_message = str(request_parameters.get("userMessage") or "").strip() or None

        ChatPresentationDecisionService.enrich_metadata(
            metadata,
            intent=str(action.get("intent") or action.get("name") or "").strip() or None,
            user_message=user_message,
            user_preference=preferred_format if session_format else None,
            axis_user_message=user_message,
        )

        ChatPresentationTitleNormalizationService.normalize_metadata(
            metadata,
            path=resolved_path,
            presenter=presenter,
        )

        if isinstance(operational_root, dict):
            from app.domain.services.chat_operational_commentary_enrichment_service import (
                ChatDataInsightEnrichmentService,
            )

            ChatDataInsightEnrichmentService.enrich_metadata(
                metadata,
                data=operational_root,
                format_quantity=lambda value, field_key=None: presenter._format_field_value(
                    str(field_key or "available_quantity"),
                    value,
                ),
                user_message=user_message,
            )

        explicit_text_mode = str(
            metadata.get("explicitSessionFormat") or ""
        ).strip().lower() in {"text", "topics"}

        if is_composite and explicit_text_mode:
            from app.domain.services.chat_presentation_text_mode_service import (
                ChatPresentationTextModeService,
            )

            ChatPresentationTextModeService.align_explicit_session_decision(metadata)

        decision_layout = str(
            (metadata.get("presentationDecision") or {}).get("layoutMode") or ""
        ).strip().lower()

        if decision_layout == "stack":
            from app.domain.services.chat_presentation_stack_order_service import (
                ChatPresentationStackOrderService,
            )

            ChatPresentationStackOrderService.enrich_metadata(metadata)

        if is_composite and explicit_text_mode:
            from app.domain.services.chat_presentation_text_mode_service import (
                ChatPresentationTextModeService,
            )

            ChatPresentationTextModeService.embed_and_finalize_explicit_text(metadata)

        ChatPresentationRenderPipelineService.finalize(metadata)

        from app.domain.services.chat_presentation_data_only_prose_service import (
            ChatPresentationDataOnlyProseService,
        )

        ChatPresentationDataOnlyProseService.apply_pipeline(
            metadata,
            user_message=user_message,
            path=resolved_path,
        )

        return metadata

    @staticmethod
    def _resolve_preferred_format(
        *,
        session_format: str,
        has_text: bool,
        has_table: bool,
        has_kpi: bool,
    ) -> str | None:
        if session_format in {"text", "table", "tree", "chart", "canvas", "dashboard", "kpi"}:
            return session_format

        if has_table:
            return "table"

        if has_kpi:
            return "kpi"

        if has_text:
            return "text"

        return None
