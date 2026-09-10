"""Resolução de action + parâmetros + reason — registry operacional."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ProductionOperationalIntentKind,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
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

        # E9.S12.C — authority = operationIds canônicos (OpenAPI).
        # Compat: operationIdMarkers/pathMarkers ainda lidos se presentes (testes/KPI virtual).
        operation_ids = [
            str(item).strip()
            for item in (route_spec.get("operationIds") or [])
            if str(item).strip()
        ]
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
            not operation_ids
            and not path_markers
            and not operation_markers
            and not path_exact_end
            and not path_suffix
        ):
            return None

        if candidates is None:
            if operation_ids and hasattr(
                self._catalog, "find_allowed_actions_by_operation_ids"
            ):
                candidates = self._catalog.find_allowed_actions_by_operation_ids(
                    operation_ids=operation_ids,
                    allowed_action_ids=allowed_action_ids,
                    method=str(route_spec.get("method") or "GET"),
                )
            if not candidates:
                candidates = self._catalog.find_allowed_actions_by_markers(
                    path_markers=path_markers
                    or ([path_exact_end] if path_exact_end else []),
                    operation_markers=operation_markers
                    or [oid.lower() for oid in operation_ids],
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
        operation_id_set = {oid.lower() for oid in operation_ids}

        normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")
        matching: list[tuple[dict, dict, str]] = []

        for action in candidates:
            if str(action.get("method") or "GET").upper() != expected_method:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if operation_id_set:
                if operation_id not in operation_id_set:
                    continue
            else:
                if path_exact_end and not path.rstrip("/").endswith(
                    path_exact_end.rstrip("/")
                ):
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

                if exclude_path_markers and any(
                    marker in path for marker in exclude_path_markers
                ):
                    continue

                if operation_markers and not any(
                    marker in operation_id for marker in operation_markers
                ):
                    if path_markers or path_exact_end or path_suffix:
                        if not path_markers or not any(
                            marker in path for marker in path_markers
                        ):
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

                if (
                    "search" in path
                    and not path_markers
                    and not path_exact_end
                    and not path_suffix
                ):
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

        action, parameters, reason = self._prefer_branch_capable_match(matching)

        result = {
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
        strategy = str((route.get("parameters") or {}).get("strategy") or "").strip()
        if not strategy:
            from app.domain.services.parameter_strategy_inference_service import (
                ParameterStrategyInferenceService,
            )

            strategy = ParameterStrategyInferenceService.infer_from_action(
                action if isinstance(action, dict) else {},
                route=route,
            )
        from app.domain.services.parameter_strategy_shadow_service import (
            ParameterStrategyShadowService,
        )

        shadow = ParameterStrategyShadowService.compare(
            strategy=strategy,
            legacy_parameters=parameters if isinstance(parameters, dict) else {},
            action=action if isinstance(action, dict) else {},
            message=message,
            previous_messages=previous_messages,
            catalog=self._catalog,
            identifier=identifier,
            conversation_context=conversation_context,
            memory_snapshot=memory_snapshot,
            production_kind=production_kind,
            route=route,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            description_override=description_override,
        )
        if shadow is not None:
            result["metadata"] = {"parameterStrategyShadow": shadow}
        return result

    @staticmethod
    def _prefer_branch_capable_match(
        matching: list[tuple[dict, dict, str]],
    ) -> tuple[dict, dict, str]:
        """Quando várias actions batem o mesmo path (ex.: ROL summary), preferir a que
        carrega `branch` — evita head-office ganhar só por ordem em allowed_action_ids.
        """
        if len(matching) <= 1:
            return matching[0]

        with_branch = [
            item
            for item in matching
            if str((item[1] or {}).get("branch") or "").strip()
        ]

        if not with_branch:
            return matching[0]

        for action, parameters, reason in with_branch:
            names = {
                str(param.get("name") or "").lower()
                for param in (action.get("parametersSchema") or [])
                if isinstance(param, dict)
            }
            if "branch" in names:
                return action, parameters, reason

        return with_branch[0]

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
            "actionSelectionCopy",
            "routeClarification",
            "invoiceInboundLabel",
            default="Notas fiscais de entrada",
        )
        outbound_label = ExternalActionResponseContentService.get(
            "actionSelectionCopy",
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
            "actionSelectionCopy",
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
        from app.domain.services.parameter_strategy_inference_service import (
            ParameterStrategyInferenceService,
        )

        strategy = ParameterStrategyInferenceService.infer_from_action(
            action,
            route=route,
        ).lower()
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
        """Bind parameters via ParameterStrategyShadowService (E1.S5/S6 + E9.S12.E).

        Strategy é inferida do OpenAPI (path/operationId); JSON registry não é authority.
        """
        from app.domain.services.parameter_strategy_inference_service import (
            ParameterStrategyInferenceService,
        )
        from app.domain.services.parameter_strategy_shadow_service import (
            ParameterStrategyShadowService,
        )

        strategy = ParameterStrategyInferenceService.infer_from_action(
            action,
            route=route,
        )
        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message or ""
        )

        if strategy not in ParameterStrategyShadowService.cutover_strategies():
            return None

        return ParameterStrategyShadowService.bind_via_openapi(
            action,
            message,
            previous_messages=previous_messages,
            strategy=strategy,
            catalog=self._catalog,
            identifier=identifier,
            conversation_context=conversation_context,
            memory_snapshot=memory_snapshot,
            production_kind=production_kind,
            route=route,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            description_override=description_override,
            normalized=normalized_text,
        )

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
