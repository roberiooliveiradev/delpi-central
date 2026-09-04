"""Resolução de action + parâmetros + reason — registry operacional."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)
from app.domain.services.chat_tool_grounding_context_service import (
    ChatToolGroundingContextService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.operational_route_query_defaults_service import (
    OperationalRouteQueryDefaultsService,
)
from app.domain.services.chat_operational_pagination_defaults_service import (
    ChatOperationalPaginationDefaultsService,
)


class OperationalRouteActionResolverService:
    def __init__(self, catalog) -> None:
        self._catalog = catalog

    def resolve_route_action(
        self,
        route: dict,
        message: str,
        allowed_action_ids: list[str],
        *,
        identifier: str | None = None,
        candidates: list[dict] | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        production_kind: ProductionOperationalIntentKind | None = None,
        conversation_context: str | None = None,
        description_override: str | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict | None:
        route_spec = route.get("route")

        if not isinstance(route_spec, dict):
            return None

        path_markers = [
            str(marker).lower()
            for marker in (route_spec.get("pathMarkers") or [])
            if str(marker).strip()
        ]
        operation_markers = [
            str(marker).lower()
            for marker in (route_spec.get("operationIdMarkers") or [])
            if str(marker).strip()
        ]
        exclude_path_markers = [
            str(marker).lower()
            for marker in (route_spec.get("excludePathMarkers") or [])
            if str(marker).strip()
        ]
        path_exact_end = str(route_spec.get("pathExactEnd") or "").strip().lower()
        path_suffix = str(route_spec.get("pathSuffix") or "").strip().lower()

        if (
            not path_markers
            and not operation_markers
            and not path_exact_end
            and not path_suffix
        ):
            return None

        if candidates is None:
            candidates = self._catalog.find_allowed_actions_by_markers(
                path_markers=path_markers or ([path_exact_end] if path_exact_end else []),
                operation_markers=operation_markers,
                allowed_action_ids=allowed_action_ids,
            )

            if not candidates:
                candidates = self._catalog.load_candidates(
                    message,
                    allowed_action_ids=allowed_action_ids,
                    candidates_loader=candidates_loader,
                )

        candidates = self._catalog.stable_sort_by_allowed_action_ids(
            candidates or [],
            allowed_action_ids,
        )

        expected_method = str(route_spec.get("method") or "GET").upper()

        normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")
        matching: list[tuple[dict, dict, str]] = []

        for action in candidates:
            if str(action.get("method") or "GET").upper() != expected_method:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if path_exact_end and not path.rstrip("/").endswith(path_exact_end.rstrip("/")):
                continue

            if path_suffix and not path.rstrip("/").endswith(path_suffix.rstrip("/")):
                if not operation_markers or not any(
                    marker in operation_id for marker in operation_markers
                ):
                    continue

            if path_markers and not any(marker in path for marker in path_markers):
                if not (
                    path_suffix
                    and path.rstrip("/").endswith(path_suffix.rstrip("/"))
                ):
                    if not operation_markers or not any(
                        marker in operation_id for marker in operation_markers
                    ):
                        continue

            if exclude_path_markers and any(marker in path for marker in exclude_path_markers):
                continue

            if operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                if path_markers or path_exact_end or path_suffix:
                    if not path_markers or not any(marker in path for marker in path_markers):
                        if not path_suffix or not path.rstrip("/").endswith(
                            path_suffix.rstrip("/")
                        ):
                            continue

            if (
                not path_markers
                and not path_exact_end
                and not path_suffix
                and operation_markers
                and not any(marker in operation_id for marker in operation_markers)
            ):
                continue

            if "search" in path and not path_markers and not path_exact_end and not path_suffix:
                continue

            if not self._action_fits_route_affinity(route, action, path=path):
                continue

            parameters = self.build_parameters(
                route,
                action,
                message=message,
                identifier=identifier,
                normalized=normalized,
                previous_messages=previous_messages,
                build_date_branch_parameters=build_date_branch_parameters,
                merge_date_parameters=merge_date_parameters,
                production_kind=production_kind,
                conversation_context=conversation_context,
                description_override=description_override,
                memory_snapshot=memory_snapshot,
            )

            if parameters is None:
                continue

            from app.domain.services.chat_operational_date_parameter_service import (
                ChatOperationalDateParameterService,
            )

            if (
                ChatOperationalDateParameterService.action_requires_explicit_date(action)
                and not ChatOperationalDateParameterService.parameters_have_date(
                    action,
                    parameters,
                )
            ):
                continue

            reason = self.resolve_presentation_reason(
                route,
                parameters,
                message=message,
                normalized=normalized,
                description_override=description_override,
            )

            if not reason:
                continue

            matching.append((action, parameters, reason))

        if not matching:
            return None

        if (
            str(route.get("onMultipleMatches") or "").strip().lower() == "clarify"
            and len(matching) >= 2
        ):
            clarification = self._build_multiple_match_clarification(matching)

            if clarification is not None:
                return clarification

        action, parameters, reason = matching[0]

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "parameters": parameters,
            },
            "reason": reason,
            "routePresentation": (
                dict(route.get("presentation"))
                if isinstance(route.get("presentation"), dict)
                else {}
            ),
        }

    def _build_multiple_match_clarification(
        self,
        matching: list[tuple[dict, dict, str]],
    ) -> dict | None:
        from app.application.services.external_actions.external_action_score_gap_clarification_service import (
            ExternalActionScoreGapClarificationService,
        )

        top = matching[0][0]
        rival = matching[1][0]
        label_a = ExternalActionScoreGapClarificationService._label(top)
        label_b = ExternalActionScoreGapClarificationService._label(rival)
        operation_a = str(top.get("operationId") or top.get("actionId") or "").strip()
        operation_b = str(rival.get("operationId") or rival.get("actionId") or "").strip()

        inbound_label = ExternalActionResponseContentService.get(
            "actionSelection",
            "routeClarification",
            "invoiceInboundLabel",
            default="Notas fiscais de entrada",
        )
        outbound_label = ExternalActionResponseContentService.get(
            "actionSelection",
            "routeClarification",
            "invoiceOutboundLabel",
            default="Notas fiscais de saída",
        )

        path_a = str(top.get("path") or "").lower()
        path_b = str(rival.get("path") or "").lower()

        if "inbound" in path_a:
            label_a = inbound_label
        elif "outbound" in path_a:
            label_a = outbound_label

        if "inbound" in path_b:
            label_b = inbound_label
        elif "outbound" in path_b:
            label_b = outbound_label

        direct_answer = ExternalActionResponseContentService.format(
            "actionSelection",
            "routeClarification",
            "invoiceDirectionDirectAnswer",
            labelA=label_a,
            labelB=label_b,
            default=(
                f"Quer consultar **{label_a}** ou **{label_b}**?\n\n"
                "Responda indicando a opção ou reformule com «entrada» ou «saída»."
            ),
        )

        return {
            "name": ExternalActionScoreGapClarificationService.clarification_tool_name(),
            "arguments": {
                "directAnswer": direct_answer,
                "rivalIds": [
                    str(top.get("actionId") or ""),
                    str(rival.get("actionId") or ""),
                ],
                "operationIds": [operation_a, operation_b],
                "suggestions": [
                    {
                        "label": label_a,
                        "query": label_a,
                        "operationId": operation_a,
                    },
                    {
                        "label": label_b,
                        "query": label_b,
                        "operationId": operation_b,
                    },
                ],
            },
            "reason": ExternalActionResponseContentService.get(
                "selectionReasons",
                "invoiceDirectionClarification",
                default="Notas fiscais sem direção — clarificação entrada/saída.",
            ),
        }

    @staticmethod
    def _action_fits_route_affinity(route: dict, action: dict, *, path: str) -> bool:
        """Rejeita action cujo path não combina com a classe da rota do registry.

        Evita shadowing clássico: marker ``/customers`` casando ``/customers/search``
        quando a rota exige identificador de produto, ou ``product_search`` em
        ``/customers/search``.
        """
        parameters_spec = route.get("parameters") or {}
        strategy = str(parameters_spec.get("strategy") or "").strip().lower()
        match_spec = route.get("match") if isinstance(route.get("match"), dict) else {}
        requires_product = bool(match_spec.get("requiresProductIdentifier"))
        route_segment = str(route.get("routeSegment") or "").strip()
        domain = str(route.get("domain") or "").strip()

        if strategy == "product_search" or domain == "domainProductSearch":
            return "/products/" in path and "search" in path

        if strategy == "supplier_part_number":
            return "/products/" in path and "by-supplier-part-number" in path

        if strategy == "product_code" or requires_product or route_segment:
            if "{code}" in path or "{identifier}" in path:
                return "/products/" in path

            return "/products/" in path

        return True

    def build_parameters(
        self,
        route: dict,
        action: dict,
        *,
        message: str,
        identifier: str | None,
        normalized: str | None = None,
        previous_messages: list | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        production_kind: ProductionOperationalIntentKind | None = None,
        conversation_context: str | None = None,
        description_override: str | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict | None:
        parameters_spec = route.get("parameters") or {}
        strategy = str(parameters_spec.get("strategy") or "").strip()
        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message or ""
        )

        if strategy == "product_search":
            from app.application.services.external_actions.external_action_product_search_route_selection_service import (
                ExternalActionProductSearchRouteSelectionService,
            )

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if "/products/" not in path:
                return None

            if "search" not in path and "search" not in operation_id:
                return None

            return ExternalActionProductSearchRouteSelectionService.build_search_parameters(
                message,
                normalized_text,
                action,
                description_override=description_override,
            )

        if strategy == "lmp":
            from app.domain.services.operational_route_matcher_service import (
                OperationalRouteMatcherService,
            )

            path = str(action.get("path") or "")
            sale_number = OperationalRouteMatcherService.extract_lmp_sale_number(
                message
            ) or OperationalRouteMatcherService.extract_lmp_sale_number(conversation_context)

            if "{sale_number}" in path and not sale_number:
                return None

            if sale_number and "{sale_number}" in path:
                for parameter in action.get("parametersSchema") or []:
                    name = parameter.get("name")

                    if name and name.lower() in {"sale_number", "ordem", "ov"}:
                        return {name: sale_number}

                return {"sale_number": sale_number}

            parameters: dict = {}

            for parameter in action.get("parametersSchema") or []:
                name = parameter.get("name")

                if not name:
                    continue

                lowered = name.lower()

                if lowered in {"page"}:
                    parameters[name] = 1
                elif lowered in {"page_size", "pagesize", "limit"}:
                    parameters[name] = ChatOperationalPaginationDefaultsService.standard()
                elif lowered == "status" and "/dashboard" in path:
                    parameters[name] = "Todos"

            if not parameters:
                if "/dashboard" in path.lower():
                    parameters = {}
                else:
                    parameters = {
                        "page": 1,
                        "page_size": ChatOperationalPaginationDefaultsService.standard(),
                    }

            if merge_date_parameters:
                return merge_date_parameters(action, message, parameters)

            return parameters

        if strategy == "supplier_part_number":
            from app.domain.services.chat_operational_identifier_resolution_service import (
                ChatOperationalIdentifierResolutionService,
            )

            part_number = ChatOperationalIdentifierResolutionService.primary_supplier_part_number(
                message or ""
            )
            if not part_number:
                return None

            parameters: dict = {
                "supplier_part_number": part_number,
                "page": 1,
                "page_size": ChatOperationalPaginationDefaultsService.standard(),
            }
            return self._catalog.filter_parameters_to_schema(action, parameters)

        if strategy == "product_code":
            if not identifier:
                identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                identifier = ChatProductQueryIntentService.resolve_product_code(
                    message or "",
                    conversation_context,
                    previous_messages=previous_messages,
                    memory_snapshot=memory_snapshot
                    or ChatToolGroundingContextService.current_memory_snapshot(),
                )

            if not identifier:
                return None

            return self._catalog.build_product_parameters(
                action,
                identifier,
                message=message,
                previous_messages=previous_messages,
            )

        if strategy == "exclusive_catalog":
            normalized = message.lower()

            return self._catalog.build_exclusive_catalog_parameters(
                action,
                message=message,
                normalized=normalized,
            )

        if strategy == "date_branch":
            parameters: dict = {}

            if build_date_branch_parameters:
                parameters = build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                )

            if production_kind in {
                ProductionOperationalIntentKind.LOSSES_TOP,
                ProductionOperationalIntentKind.LOSSES_RECORDS,
            }:
                loss_type = ChatProductionOperationalIntentService.infer_loss_type(
                    ChatMessageNormalizationService.normalize_for_matching(message)
                )

                if loss_type:
                    parameters["loss_type"] = loss_type

            if production_kind == ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM:
                product_code = ChatProductQueryIntentService.extract_product_code(message)

                if product_code:
                    parameters["code"] = product_code

            if production_kind == ProductionOperationalIntentKind.SCHEDULE_TODAY:
                filter_code = ChatProductQueryIntentService.resolve_schedule_product_filter_code(
                    message,
                    product_code=ChatProductQueryIntentService.extract_product_code(message),
                )

                if filter_code:
                    parameters["presentationDetailFilter"] = {
                        "product_code_prefix": filter_code,
                    }

            if not parameters:
                parameters = {}

            parameters = OperationalRouteQueryDefaultsService.apply(
                action,
                parameters,
                route=route,
            )

            parameters = self._catalog.filter_parameters_to_schema(
                action,
                parameters,
            )

            return parameters

        if strategy == "department_idd":
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            parameters = OperationalApiParameterBuilderService().build_department_idd(
                action,
                message,
                previous_messages=previous_messages,
            )
            parameters = OperationalRouteQueryDefaultsService.apply(
                action,
                parameters,
                route=route,
            )
            return self._catalog.filter_parameters_to_schema(action, parameters)

        if strategy == "sale_orders":
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            return OperationalApiParameterBuilderService().build_sale_orders(
                action,
                message,
                previous_messages=previous_messages,
            )

        if strategy == "system_metadata":
            from app.domain.services.chat_system_metadata_intent_service import (
                ChatSystemMetadataIntentService,
            )

            return ChatSystemMetadataIntentService.build_parameters(message, action)

        if strategy == "supplies_stock":
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            return OperationalApiParameterBuilderService.build_supplies_stock(action)

        if strategy in {"none", "semantic"}:
            return {}

        return None

    def resolve_presentation_reason(
        self,
        route: dict,
        parameters: dict,
        *,
        message: str,
        normalized: str,
        description_override: str | None = None,
    ) -> str:
        presentation = route.get("presentation") or {}
        reason_format_key = str(presentation.get("reasonFormatKey") or "").strip()

        if reason_format_key:
            reason_format_param = str(presentation.get("reasonFormatParam") or "").strip()

            if reason_format_param == "group_code":
                group_code = parameters.get("group_code") or parameters.get("groupCode")

                if group_code:
                    return ExternalActionResponseContentService.format(
                        "selectionReasons",
                        reason_format_key,
                        group_code=group_code,
                    )
            elif reason_format_param == "description_query":
                from app.application.services.external_actions.external_action_product_search_route_selection_service import (
                    ExternalActionProductSearchRouteSelectionService,
                )

                description_query = (
                    parameters.get("description")
                    or parameters.get("query")
                    or parameters.get("q")
                    or description_override
                    or ExternalActionProductSearchRouteSelectionService.extract_search_description(
                        message
                    )
                )

                if description_query:
                    return ExternalActionResponseContentService.format(
                        "selectionReasons",
                        reason_format_key,
                        description_query=description_query,
                    )

        reason_key = str(presentation.get("reasonKey") or route.get("id") or "").strip()

        if not reason_key:
            return ""

        return ExternalActionResponseContentService.get(
            "selectionReasons",
            reason_key,
        )
