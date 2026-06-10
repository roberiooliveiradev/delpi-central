from urllib.parse import quote
from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)
from app.domain.services.chat_data_coverage_notice_service import (
    ChatDataCoverageNoticeService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


class ExecuteExternalActionUseCase:
    INTERNAL_PARAMETER_NAMES = {
        "message",
        "prompt",
        "question",
        "input",
        "text",
        "queryText",
        "query_text",
        "userMessage",
        "user_message",
    }

    def __init__(
        self,
        repository,
        gateway,
        policy: ExternalActionExecutionPolicy,
        audit_repository: AuditRepositoryPort,
    ):
        self.repository = repository
        self.gateway = gateway
        self.policy = policy
        self.audit_repository = audit_repository
        self.presenter = ExternalActionResultPresenter()

    def execute(
        self,
        user_id: str,
        access_token: str,
        action_id: str,
        arguments: dict,
    ) -> dict:
        action_bundle = self.repository.get_action_for_execution(action_id)

        if not action_bundle:
            raise ValueError("Action not found")

        provider = action_bundle["provider"]
        action = action_bundle["action"]
        arguments = self._normalize_arguments_for_method(action, arguments)
        arguments = self._drop_internal_unknown_parameters(action, arguments)

        self.policy.validate(provider, action, arguments)

        request_parameters = self._clamp_hierarchical_query_parameters(
            action.get("path") or "",
            arguments.get("parameters") or {},
        )

        result = self.gateway.execute(
            provider=provider,
            action=action,
            parameters=request_parameters,
            body=arguments.get("body"),
            access_token=access_token,
        )

        sanitized_data = self.policy.sanitize_response(result["data"])
        action_path = action.get("path") or ""
        resolved_path = self._resolve_action_path(action_path, request_parameters)
        from app.domain.services.chat_sql_execution_error_interpretation_service import (
            ChatSqlExecutionErrorInterpretationService,
        )

        logical_failure = ChatSqlExecutionErrorInterpretationService.has_logical_failure(
            sanitized_data,
            path=resolved_path,
        )
        effective_ok = bool(result["ok"]) and not logical_failure

        self.audit_repository.log(
            user_id=UUID(user_id),
            action="external_action.called",
            context="external_action",
            tool_calls=[
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "provider": provider["providerKey"],
                        "actionId": action["actionId"],
                        "method": action["method"],
                        "path": resolved_path,
                        "statusCode": result["statusCode"],
                        "durationMs": result["durationMs"],
                        "sensitivity": action["sensitivity"],
                    },
                }
            ],
            metadata={
                "provider": provider["providerKey"],
                "action_id": action["actionId"],
                "method": action["method"],
                "path": resolved_path,
                "status_code": result["statusCode"],
                "duration_ms": result["durationMs"],
                "sensitivity": action["sensitivity"],
            },
        )

        presentation_metadata = self._build_presentation_metadata(
            action=action,
            sanitized_data=sanitized_data,
            resolved_path=resolved_path,
            request_parameters=request_parameters,
        )

        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )

        execution_metadata = {
            "durationMs": result["durationMs"],
            "sensitivity": action["sensitivity"],
            "apiRouteDomain": ChatOperationalApiDomainService.classify_path(resolved_path),
            **presentation_metadata,
        }

        api_delpi_meta = self._extract_api_delpi_response_meta(sanitized_data)
        if api_delpi_meta:
            execution_metadata["apiDelpiResponseMeta"] = api_delpi_meta

        if not effective_ok:
            api_error = self._extract_api_error_message(sanitized_data)

            if api_error:
                execution_metadata["error"] = api_error

        return {
            "provider": provider["providerKey"],
            "actionId": action["actionId"],
            "method": action["method"],
            "path": resolved_path,
            "statusCode": result["statusCode"],
            "ok": effective_ok,
            "data": sanitized_data,
            "metadata": execution_metadata,
        }

    @staticmethod
    def _extract_api_error_message(data) -> str | None:
        from app.domain.services.chat_sql_execution_error_interpretation_service import (
            ChatSqlExecutionErrorInterpretationService,
        )

        text = ChatSqlExecutionErrorInterpretationService.extract_error_text(data)

        return text or None

    @staticmethod
    def _extract_api_delpi_response_meta(data) -> dict | None:
        if not isinstance(data, dict):
            return None
        if "meta" not in data:
            return None
        if "success" not in data and "data" not in data:
            return None
        meta = data.get("meta")
        return meta if isinstance(meta, dict) else None

    def build_metadata_for_data(
        self,
        *,
        action_id: str,
        data,
        parameters: dict | None = None,
    ) -> dict:
        action_bundle = self.repository.get_action_for_execution(action_id)

        if not action_bundle:
            raise ValueError("Action not found")

        action = action_bundle["action"]
        sanitized_data = self.policy.sanitize_response(data)
        action_path = action.get("path") or ""
        request_parameters = dict(parameters or {})
        resolved_path = self._resolve_action_path(action_path, request_parameters)

        return self._build_presentation_metadata(
            action=action,
            sanitized_data=sanitized_data,
            resolved_path=resolved_path,
            request_parameters=request_parameters,
        )

    def _build_presentation_metadata(
        self,
        *,
        action: dict,
        sanitized_data,
        resolved_path: str,
        request_parameters: dict,
    ) -> dict:
        action_path = action.get("path") or ""
        presentation_data = self.presenter.prepare_presentation_data(
            sanitized_data,
            path=resolved_path,
        )
        text_presentation = self.presenter.build_text_presentation(
            presentation_data,
            path=resolved_path,
        )
        tree_presentation = self.presenter.build_tree_presentation(
            presentation_data,
            path=resolved_path,
        )
        dashboard_presentation = self.presenter.build_dashboard_presentation(
            presentation_data,
            path=resolved_path,
        )
        presentation = self.presenter.build_presentation(
            presentation_data,
            path=resolved_path,
            response_schema=action.get("responseSchema"),
        )
        chart_presentation = self.presenter.build_chart_presentation(
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
        elif presentation:
            table_presentation = presentation

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
        elif (
            table_presentation
            and not tree_presentation
            and not chart_presentation
            and not any(
                token in str(resolved_path or "").lower()
                for token in ("/structure", "/parents", "/analyser")
            )
        ):
            forced_chart = self.presenter.build_chart_presentation(
                presentation_data,
                path=resolved_path or action_path,
                force=True,
            )

            if forced_chart:
                chart_presentation = forced_chart
                available_formats.append("chart")

        path_lower = str(resolved_path or "").lower()
        stock_like = "/stock" in path_lower

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

        price_like = "/prices" in path_lower or "/pricing" in path_lower

        session_format = str(request_parameters.get("sessionResponseFormat") or "").strip().lower()

        from app.domain.services.chat_presentation_route_policy_service import (
            ChatPresentationRoutePolicyService,
        )

        table_presentations_list: list[dict] = []
        profile_table_presentation = None
        inspection_table_presentation = None
        root_payload = self.presenter._unwrap_data(presentation_data)

        if isinstance(root_payload, dict):
            if "/analyser" in path_lower and isinstance(root_payload.get("product"), dict):
                table_presentations_list = (
                    self.presenter.build_analyser_auxiliary_table_presentations(root_payload)
                )

                if table_presentations_list:
                    for candidate in table_presentations_list:
                        title = str(candidate.get("title") or "")

                        if title.startswith("Produto "):
                            profile_table_presentation = candidate
                        elif "inspeção" in title.lower() or "inspecao" in title.lower():
                            inspection_table_presentation = candidate
                        elif "roteiro" in title.lower() and table_presentation is None:
                            table_presentation = candidate

                    if table_presentation is None and table_presentations_list:
                        table_presentation = table_presentations_list[0]
            elif "/stock" in path_lower and isinstance(root_payload, dict):
                stock_items = root_payload.get("items")

                if isinstance(stock_items, list) and stock_items:
                    table_presentations_list = self.presenter.build_stock_table_presentations(
                        root_payload,
                        resolved_path,
                    )

                    if table_presentations_list:
                        profile_table_presentation = table_presentations_list[0]

                        if len(table_presentations_list) > 1:
                            table_presentation = table_presentations_list[1]
                        else:
                            table_presentation = table_presentations_list[0]
            elif "/factory-status" in path_lower and isinstance(root_payload, dict):
                table_presentations_list = self.presenter.build_factory_status_table_presentations(
                    root_payload,
                    resolved_path,
                )

                if table_presentations_list:
                    table_presentation = table_presentations_list[0]
            elif "/production-status" in path_lower and isinstance(root_payload, dict):
                table_presentations_list = (
                    self.presenter.build_production_status_table_presentations(
                        root_payload,
                        resolved_path,
                    )
                )

                if table_presentations_list:
                    profile_table_presentation = table_presentations_list[0]

                    if len(table_presentations_list) > 1:
                        table_presentation = table_presentations_list[1]
                    else:
                        table_presentation = table_presentations_list[0]
            elif "/shipping-status" in path_lower and isinstance(root_payload, dict):
                table_presentations_list = self.presenter.build_shipping_status_table_presentations(
                    root_payload,
                    resolved_path,
                )

                if table_presentations_list:
                    profile_table_presentation = table_presentations_list[0]

                    if len(table_presentations_list) > 1:
                        table_presentation = table_presentations_list[1]
                    else:
                        table_presentation = table_presentations_list[0]
            elif "/structure/exclusivity" in path_lower and isinstance(root_payload, dict):
                table_presentations_list = (
                    self.presenter.build_structure_exclusivity_table_presentations(
                        root_payload,
                        resolved_path,
                    )
                )

                if table_presentations_list:
                    profile_table_presentation = table_presentations_list[0]

                    if len(table_presentations_list) > 1:
                        table_presentation = table_presentations_list[1]
                    else:
                        table_presentation = table_presentations_list[0]
            elif "/raw-material-price-intelligence" in path_lower and isinstance(root_payload, dict):
                table_presentations_list = (
                    self.presenter.build_raw_material_price_intelligence_table_presentations(
                        root_payload,
                        resolved_path,
                    )
                )

                if table_presentations_list:
                    profile_table_presentation = table_presentations_list[0]
                    table_presentation = table_presentations_list[0]
            elif "/cost-impact-simulation" in path_lower and isinstance(root_payload, dict):
                table_presentations_list = (
                    self.presenter.build_cost_impact_simulation_table_presentations(
                        root_payload,
                        resolved_path,
                    )
                )

                if table_presentations_list:
                    profile_table_presentation = table_presentations_list[0]
                    table_presentation = table_presentations_list[0]
            elif "/last-purchase" in path_lower and isinstance(root_payload, dict):
                last_purchase_table = self.presenter.build_last_purchase_table_presentation(
                    root_payload,
                    resolved_path,
                )

                if last_purchase_table:
                    table_presentation = last_purchase_table
            elif (
                ChatPresentationRoutePolicyService.is_tree_route(resolved_path)
                and tree_presentation
                and not table_presentation
                and session_format == "table"
            ):
                structure_table = self.presenter._build_analyser_structure_components_table(
                    root_payload,
                )

                if structure_table:
                    table_presentation = structure_table

        preferred_format = None

        if session_format in {"table", "text", "tree", "chart", "topics", "canvas"}:
            preferred_format = session_format if session_format != "topics" else "text"
        elif dashboard_presentation:
            preferred_format = "dashboard"
        elif price_like and text_presentation and not session_format:
            preferred_format = "text"
        elif kpi_presentation and not session_format:
            preferred_format = "kpi"
        else:
            preferred_format = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
                path=resolved_path,
                session_format=session_format or None,
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
            response_meta=self._extract_api_delpi_response_meta(sanitized_data),
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
        }

        from app.domain.services.chat_presentation_visual_bundle_service import (
            ChatPresentationVisualBundleService,
        )

        ChatPresentationVisualBundleService.enrich_metadata(
            metadata,
            path=resolved_path,
            data=sanitized_data,
            presenter=self.presenter,
        )

        schema_labels = self.presenter._column_labels.merge_meta_field_labels(
            self.presenter._column_labels.resolve_schema_labels(action.get("responseSchema")),
            sanitized_data,
        )
        schema_formats = self.presenter._column_labels.merge_meta_field_formats(
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

        explicit_preference = behavior_format

        if not explicit_preference and user_message:
            explicit_preference = ChatToolContextFormatService.detect_requested_format(
                user_message,
            )

        metadata["path"] = resolved_path

        from app.domain.services.chat_presentation_structure_dedup_service import (
            ChatPresentationStructureDedupService,
        )

        ChatPresentationStructureDedupService.dedupe_metadata(metadata)

        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        ChatPresentationPrimaryViewService.apply_session_preference(
            metadata,
            session_format,
            data=sanitized_data,
            path=resolved_path,
            presenter=self.presenter,
        )

        from app.domain.services.chat_presentation_stack_order_service import (
            ChatPresentationStackOrderService,
        )

        ChatPresentationStackOrderService.enrich_metadata(metadata)

        ChatPresentationDecisionService.enrich_metadata(
            metadata,
            intent=str(action.get("intent") or action.get("name") or "").strip() or None,
            user_message=user_message,
            user_preference=explicit_preference,
            axis_user_message=user_message,
        )

        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        ChatRichPresentationTextService.compact_metadata_text(metadata)

        self._normalize_eficiencia_fabril_titles(metadata, resolved_path)
        self._align_presentation_with_decision(metadata, kpi_presentation=kpi_presentation)

        return metadata

    @staticmethod
    def _align_presentation_with_decision(
        metadata: dict,
        *,
        kpi_presentation: dict | None,
    ) -> None:
        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        ChatPresentationPrimaryViewService.finalize_decision_alignment(
            metadata,
            kpi_presentation=kpi_presentation,
        )

    @staticmethod
    def _normalize_eficiencia_fabril_titles(metadata: dict, path: str) -> None:
        lowered = str(path or "").lower()

        if "eficiencia-fabril" not in lowered and "eficiencia_fabril" not in lowered:
            return

        title = ExternalActionResultPresenter()._infer_items_title([], path) or "Eficiência fabril"
        wrong_titles = {"Lista de LMPs", "LMPs", "Visualização dos dados"}

        for key in ("tablePresentation", "chartPresentation", "textPresentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict):
                continue

            current = str(presentation.get("title") or "").strip()

            if not current or current in wrong_titles:
                presentation["title"] = title

        dashboard = metadata.get("presentation")

        if isinstance(dashboard, dict) and dashboard.get("type") == "dashboard":
            for panel in dashboard.get("panels") or []:
                if not isinstance(panel, dict):
                    continue

                for nested_key in ("presentation", "chartPresentation"):
                    nested = panel.get(nested_key)

                    if not isinstance(nested, dict):
                        continue

                    current = str(nested.get("title") or "").strip()

                    if nested.get("type") in {"table", "chart"} and (
                        not current or current in wrong_titles
                    ):
                        nested["title"] = (
                            title
                            if nested.get("type") == "chart"
                            else panel.get("title") or "Itens do painel"
                        )

    @staticmethod
    def _resolve_action_path(path: str, parameters: dict) -> str:
        resolved = str(path or "")

        for key, value in (parameters or {}).items():
            if value in (None, ""):
                continue

            token = "{" + str(key) + "}"

            if token in resolved:
                resolved = resolved.replace(
                    token,
                    quote(str(value), safe=""),
                )

        return resolved

    @staticmethod
    def _clamp_hierarchical_query_parameters(path: str, parameters: dict) -> dict:
        lowered = str(path or "").lower()

        if "/structure" not in lowered and "/parents" not in lowered:
            return dict(parameters or {})

        clamped = dict(parameters or {})
        depth_keys = {"max_depth", "maxdepth", "depth", "nivel", "levels"}

        for key, value in list(clamped.items()):
            if str(key).lower() not in depth_keys:
                continue

            try:
                depth = int(value)
            except (TypeError, ValueError):
                continue

            clamped[key] = min(max(depth, 1), 15)

        return clamped

    def _drop_internal_unknown_parameters(self, action: dict, arguments: dict) -> dict:
        normalized = dict(arguments or {})
        parameters = dict(normalized.get("parameters") or {})

        if not parameters:
            normalized["parameters"] = parameters
            return normalized

        allowed_parameter_names = {
            parameter.get("name")
            for parameter in action.get("parametersSchema") or []
            if parameter.get("name")
        }

        cleaned_parameters = {}

        for key, value in parameters.items():
            if key in allowed_parameter_names:
                cleaned_parameters[key] = value
                continue

            if key in self.INTERNAL_PARAMETER_NAMES:
                continue

            cleaned_parameters[key] = value

        normalized["parameters"] = cleaned_parameters
        return normalized

    def _normalize_arguments_for_method(self, action: dict, arguments: dict) -> dict:
        normalized = dict(arguments or {})
        method = str(action.get("method") or "").upper()

        parameters = dict(normalized.get("parameters") or {})
        body = normalized.get("body")

        if method not in {"GET", "HEAD", "DELETE"}:
            normalized["parameters"] = parameters
            return normalized

        if body in (None, "", {}, []):
            normalized["parameters"] = parameters
            normalized["body"] = None
            return normalized

        if isinstance(body, dict):
            for key, value in body.items():
                if value in (None, ""):
                    continue

                parameters.setdefault(key, value)

        normalized["parameters"] = parameters
        normalized["body"] = None

        return normalized
