"""Pipeline de metadata de apresentação — Playbook 12 A9/R24."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from app.domain.services.chat_data_coverage_notice_service import (
    ChatDataCoverageNoticeService,
)
from app.domain.services.chat_presentation_title_normalization_service import (
    ChatPresentationTitleNormalizationService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationMetadataPipelineService:
    """Orquestra montagem e enriquecimento de metadata pós-execução de action."""

    @classmethod
    def build(
        cls,
        *,
        action: dict,
        sanitized_data,
        resolved_path: str,
        request_parameters: dict,
        presenter: ExternalActionResultPresenter,
        extract_response_meta: Callable[[Any], dict | None],
    ) -> dict:
        action_path = action.get("path") or ""
        user_message = str(request_parameters.get("userMessage") or "").strip() or None

        from app.domain.services.chat_presentation_data_only_prose_service import (
            ChatPresentationDataOnlyProseService,
        )

        data_only_prose = ChatPresentationDataOnlyProseService.should_apply(
            user_message,
            path=resolved_path,
        )

        presentation_data = presenter.prepare_presentation_data(
            sanitized_data,
            path=resolved_path,
        )
        text_presentation = None

        if not data_only_prose:
            text_presentation = presenter.build_text_presentation(
                presentation_data,
                path=resolved_path,
            )
        tree_presentation = presenter.build_tree_presentation(
            presentation_data,
            path=resolved_path,
        )
        dashboard_presentation = presenter.build_dashboard_presentation(
            presentation_data,
            path=resolved_path,
        )
        presentation = presenter.build_presentation(
            presentation_data,
            path=resolved_path,
            response_schema=action.get("responseSchema"),
        )
        chart_presentation = presenter.build_chart_presentation(
            presentation_data,
            path=resolved_path,
        )

        table_presentation = None
        kpi_presentation = None

        if isinstance(presentation, dict) and presentation.get("type") == "markdown":
            if not text_presentation:
                text_presentation = presentation
            presentation = None
        elif isinstance(presentation, dict) and presentation.get("type") == "table":
            table_presentation = presentation
        elif isinstance(presentation, dict) and presentation.get("type") == "kpi":
            kpi_presentation = presentation
        elif isinstance(presentation, dict) and presentation.get("type") == "chart":
            chart_presentation = chart_presentation or presentation
        elif isinstance(presentation, dict) and presentation.get("type") == "tree":
            tree_presentation = tree_presentation or presentation
        elif isinstance(presentation, dict) and presentation.get("type") == "table":
            table_presentation = presentation
        elif presentation:
            table_presentation = presentation

        auxiliaries = presenter.apply_schema_driven_auxiliaries(
            presentation_data,
            path=resolved_path,
            text_presentation=text_presentation,
            tree_presentation=tree_presentation,
            table_presentation=table_presentation,
            chart_presentation=chart_presentation,
            kpi_presentation=kpi_presentation,
        )
        text_presentation = auxiliaries["text_presentation"]
        tree_presentation = auxiliaries["tree_presentation"]
        table_presentation = auxiliaries["table_presentation"]
        chart_presentation = auxiliaries["chart_presentation"]
        kpi_presentation = auxiliaries["kpi_presentation"]

        available_formats: list[str] = []

        if dashboard_presentation:
            available_formats.append("dashboard")

        if kpi_presentation:
            available_formats.append("kpi")

        if text_presentation:
            available_formats.append("text")
            available_formats.append("canvas")

        if tree_presentation:
            available_formats.append("tree")

        if table_presentation:
            available_formats.append("table")

        if chart_presentation:
            available_formats.append("chart")
        elif table_presentation:
            from app.domain.services.chat_presentation_profile_service import (
                ChatPresentationProfileService,
            )
            from app.domain.services.chat_presentation_text_first_policy_service import (
                ChatPresentationTextFirstPolicyService,
            )

            user_message = str(request_parameters.get("userMessage") or "").strip() or None
            session_format = str(request_parameters.get("sessionResponseFormat") or "").strip().lower()
            explicit_preference = ChatPresentationTextFirstPolicyService.normalize_explicit_format(
                session_format,
            )

            if not explicit_preference and user_message:
                from app.application.services.chat_tool_context_format_service import (
                    ChatToolContextFormatService,
                )

                explicit_preference = ChatToolContextFormatService.detect_requested_format(
                    user_message,
                )

            if (
                ChatPresentationProfileService.should_auto_force_chart(
                    resolved_path,
                    entity=None,
                    has_tree=bool(tree_presentation),
                    has_chart=bool(chart_presentation),
                )
                and ChatPresentationTextFirstPolicyService.should_build_visual_bundle(
                    path=resolved_path,
                    explicit_format=explicit_preference,
                    user_message=user_message,
                )
            ):
                forced_chart = presenter.build_chart_presentation(
                    presentation_data,
                    path=resolved_path or action_path,
                    force=True,
                )

                if forced_chart:
                    chart_presentation = forced_chart
                    available_formats.append("chart")

        if dashboard_presentation:
            primary_presentation = dashboard_presentation
        elif tree_presentation:
            primary_presentation = tree_presentation
        elif kpi_presentation:
            primary_presentation = kpi_presentation
        elif chart_presentation:
            primary_presentation = chart_presentation
        elif table_presentation:
            primary_presentation = table_presentation
        else:
            primary_presentation = None

        session_format = str(request_parameters.get("sessionResponseFormat") or "").strip().lower()

        root_payload = presenter._unwrap_data(presentation_data)

        from app.domain.services.chat_operational_response_profile_service import (
            ChatOperationalResponseProfileService,
        )
        from app.domain.services.chat_presentation_table_assembly_service import (
            ChatPresentationTableAssemblyService,
        )

        resolved_entity = ChatOperationalResponseProfileService.resolve(
            sanitized_data,
            path=resolved_path,
        )
        entity = str(resolved_entity.entity or "").strip() or None

        assembly = ChatPresentationTableAssemblyService.assemble(
            presenter,
            root_payload if isinstance(root_payload, dict) else None,
            resolved_path,
            entity=entity,
            table_presentation=table_presentation,
            tree_presentation=tree_presentation,
            session_format=session_format,
        )

        table_presentations_list = assembly.table_presentations
        profile_table_presentation = assembly.profile_table_presentation
        inspection_table_presentation = assembly.inspection_table_presentation

        if assembly.table_presentation is not None:
            table_presentation = assembly.table_presentation

        preferred_format = None

        if session_format == "canvas":
            preferred_format = "canvas"
        elif session_format == "topics":
            preferred_format = "text"
        elif session_format in {"table", "text", "tree", "chart", "dashboard"}:
            preferred_format = session_format
        elif dashboard_presentation:
            preferred_format = "dashboard"
        elif kpi_presentation and not session_format:
            preferred_format = "kpi"
        else:
            from app.domain.services.chat_presentation_route_policy_service import (
                ChatPresentationRoutePolicyService,
            )

            preferred_format = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
                path=resolved_path,
                session_format=session_format or None,
                entity=entity,
                has_tree=bool(tree_presentation),
                has_table=bool(table_presentation or table_presentations_list),
                has_chart=bool(chart_presentation),
                has_text=bool(text_presentation),
                has_kpi=bool(kpi_presentation),
            )

        data_coverage_notice = ChatDataCoverageNoticeService.build(
            sanitized_data,
            path=resolved_path,
            parameters=request_parameters,
            presentation=primary_presentation,
            table_presentation=table_presentation,
            response_meta=extract_response_meta(sanitized_data),
        )

        metadata = {
            "presentation": primary_presentation,
            "tablePresentations": table_presentations_list or None,
            "inspectionTablePresentation": inspection_table_presentation,
            "profileTablePresentation": profile_table_presentation,
            "tablePresentation": (
                table_presentation
                if table_presentation is not None
                and table_presentation is not primary_presentation
                else None
            ),
            "treePresentation": (
                tree_presentation
                if tree_presentation is not None
                and tree_presentation is not primary_presentation
                else None
            ),
            "chartPresentation": (
                chart_presentation
                if chart_presentation is not None
                and chart_presentation is not primary_presentation
                else None
            ),
            "kpiPresentation": (
                kpi_presentation
                if kpi_presentation is not None
                and kpi_presentation is not primary_presentation
                else None
            ),
            "dashboardPresentation": (
                dashboard_presentation
                if dashboard_presentation is not None
                and dashboard_presentation is not primary_presentation
                else None
            ),
            "textPresentation": text_presentation,
            "availableFormats": available_formats,
            "preferredFormat": preferred_format,
            "dataCoverageNotice": data_coverage_notice,
            "path": resolved_path,
            "apiDelpiResponseMeta": extract_response_meta(sanitized_data),
        }

        if data_only_prose:
            ChatPresentationDataOnlyProseService.mark_metadata(metadata)

        user_message = str(request_parameters.get("userMessage") or "").strip() or None

        from app.application.services.chat_tool_context_format_service import (
            ChatToolContextFormatService,
        )
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        explicit_preference = ChatPresentationTextFirstPolicyService.normalize_explicit_format(
            session_format,
        )

        if not explicit_preference and user_message:
            explicit_preference = ChatToolContextFormatService.detect_requested_format(
                user_message,
            )

        from app.domain.services.chat_presentation_visual_bundle_service import (
            ChatPresentationVisualBundleService,
        )

        ChatPresentationVisualBundleService.enrich_metadata(
            metadata,
            path=resolved_path,
            data=sanitized_data,
            presenter=presenter,
            explicit_format=explicit_preference,
            user_message=user_message,
            entity=entity,
        )

        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        if session_format in {"text", "table", "tree", "chart", "canvas", "dashboard"}:
            ChatPresentationPrimaryViewService.apply_session_preference(
                metadata,
                session_format,
                data=sanitized_data,
                path=resolved_path,
                presenter=presenter,
            )
            explicit_preference = ChatPresentationTextFirstPolicyService.normalize_explicit_format(
                session_format,
            )

        if not str(metadata.get("explicitSessionFormat") or "").strip():
            ChatPresentationTextFirstPolicyService.apply_text_primary_metadata(
                metadata,
                path=resolved_path,
                entity=entity,
                explicit_format=explicit_preference,
                user_message=user_message,
            )

        schema_labels = presenter._column_labels.merge_meta_field_labels(
            presenter._column_labels.resolve_schema_labels(action.get("responseSchema")),
            sanitized_data,
        )
        schema_formats = presenter._column_labels.merge_meta_field_formats(
            {},
            sanitized_data,
        )

        from app.domain.services.chat_presentation_field_normalization_service import (
            ChatPresentationFieldNormalizationService,
        )

        ChatPresentationFieldNormalizationService.normalize_metadata(
            metadata,
            path=resolved_path,
            schema_labels=schema_labels,
            schema_formats=schema_formats,
        )

        from app.domain.services.chat_presentation_decision_service import (
            ChatPresentationDecisionService,
        )

        user_message = str(request_parameters.get("userMessage") or "").strip() or None

        behavior_format = session_format or None

        from app.application.services.chat_tool_context_format_service import (
            ChatToolContextFormatService,
        )

        if not explicit_preference and user_message:
            explicit_preference = ChatToolContextFormatService.detect_requested_format(
                user_message,
            )

        metadata["path"] = resolved_path

        from app.domain.services.chat_presentation_structure_dedup_service import (
            ChatPresentationStructureDedupService,
        )

        ChatPresentationStructureDedupService.dedupe_metadata(metadata)

        if not str(metadata.get("explicitSessionFormat") or "").strip():
            ChatPresentationPrimaryViewService.apply_session_preference(
                metadata,
                session_format,
                data=sanitized_data,
                path=resolved_path,
                presenter=presenter,
            )

        if not explicit_preference:
            explicit_preference = (
                ChatPresentationTextFirstPolicyService.normalize_explicit_format(
                    metadata.get("explicitSessionFormat"),
                )
            )

        from app.domain.services.chat_operational_commentary_enrichment_service import (
            ChatDataInsightEnrichmentService,
        )
        from app.domain.services.chat_presentation_humanized_narrative_service import (
            ChatPresentationHumanizedNarrativeService,
        )
        from app.domain.services.chat_presentation_stack_order_service import (
            ChatPresentationStackOrderService,
        )

        operational_root = presenter._unwrap_data(sanitized_data)

        if isinstance(operational_root, dict):
            ChatDataInsightEnrichmentService.enrich_metadata(
                metadata,
                data=operational_root,
                format_quantity=lambda value, field_key=None: presenter._format_field_value(
                    str(field_key or "available_quantity"),
                    value,
                ),
                user_message=user_message,
            )

        ChatPresentationDecisionService.enrich_metadata(
            metadata,
            intent=str(action.get("intent") or action.get("name") or "").strip() or None,
            user_message=user_message,
            user_preference=explicit_preference,
            axis_user_message=user_message,
        )

        from app.domain.services.chat_presentation_evidence_first_layout_service import (
            ChatPresentationEvidenceFirstLayoutService,
        )

        ChatPresentationEvidenceFirstLayoutService.activate(metadata)
        ChatPresentationStackOrderService.enrich_metadata(metadata)

        if not data_only_prose:
            ChatPresentationEvidenceFirstLayoutService.compose(metadata)

            if not ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
                ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)

            from app.domain.services.chat_rich_presentation_text_service import (
                ChatRichPresentationTextService,
            )

            ChatRichPresentationTextService.compact_metadata_text(metadata)

            from app.domain.services.chat_presentation_tree_markdown_service import (
                ChatPresentationTreeMarkdownService,
            )

            ChatPresentationTreeMarkdownService.embed_outline_in_text_presentation(metadata)

            from app.domain.services.chat_presentation_table_markdown_service import (
                ChatPresentationTableMarkdownService,
            )

            ChatPresentationTableMarkdownService.embed_tables_in_text_presentation(metadata)

            from app.domain.services.chat_presentation_chart_markdown_service import (
                ChatPresentationChartMarkdownService,
            )

            ChatPresentationChartMarkdownService.embed_charts_in_text_presentation(metadata)

            ChatPresentationEvidenceFirstLayoutService.finalize_narrative_after_embeds(
                metadata,
            )

        ChatPresentationTitleNormalizationService.normalize_metadata(
            metadata,
            path=resolved_path,
            presenter=presenter,
        )
        ChatPresentationPrimaryViewService.finalize_decision_alignment(
            metadata,
            kpi_presentation=kpi_presentation,
        )

        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        ChatPresentationTextModeService.finalize_explicit_text_mode(metadata)

        ChatPresentationPrimaryViewService.finalize_explicit_native_single_view(metadata)

        from app.domain.services.chat_presentation_stack_markdown_service import (
            ChatPresentationStackMarkdownService,
        )

        stack_plan = metadata.get("stackPresentationPlan")

        if isinstance(stack_plan, dict) and not data_only_prose:
            ChatPresentationStackMarkdownService.apply_section_markers(metadata, stack_plan)

        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )

        ChatPresentationRenderPipelineService.finalize(metadata)

        if data_only_prose:
            ChatPresentationDataOnlyProseService.finalize_metadata(metadata)

        from app.domain.services.chat_pagination_consolidation_service import (
            ChatPaginationConsolidationService,
        )

        refinement_cache = ChatPaginationConsolidationService.extract_cached_payload(sanitized_data)

        if isinstance(refinement_cache, dict) and refinement_cache.get("items"):
            consolidation = metadata.get("paginationConsolidation")

            if not isinstance(consolidation, dict):
                metadata["paginationConsolidation"] = {
                    "completed": True,
                    "mergedCount": len(refinement_cache["items"]),
                    "consolidatedPayload": refinement_cache,
                }
            elif not consolidation.get("consolidatedPayload"):
                consolidation["consolidatedPayload"] = refinement_cache
                consolidation.setdefault("completed", True)
                consolidation.setdefault("mergedCount", len(refinement_cache["items"]))

        return metadata


