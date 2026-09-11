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
            route_spec = {}

        # E11.S5 — operationIds/pathMarkers são observer/telemetry, não authority.
        # Seleção: allowlist completo + affinity/schema; preferred ids só ordenam.
        preferred_operation_ids = [
            str(item).strip().lower()
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

        has_semantic_route = bool(
            str(route.get("id") or "").strip()
            or str(route.get("domain") or "").strip()
            or str(route.get("intentBinding") or "").strip()
            or (isinstance(route.get("match"), dict) and route.get("match"))
        )
        if (
            not preferred_operation_ids
            and not path_markers
            and not operation_markers
            and not path_exact_end
            and not path_suffix
            and not has_semantic_route
        ):
            return None

        if candidates is None:
            candidates = self._catalog.load_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
            )

        candidates = self._catalog.stable_sort_by_allowed_action_ids(
            candidates or [],
            allowed_action_ids,
        )

        preferred_set = {oid for oid in preferred_operation_ids}
        preferred_candidates = [
            action
            for action in candidates
            if str(action.get("operationId") or "").strip().lower() in preferred_set
        ] if preferred_set else []

        expected_method = str(route_spec.get("method") or "GET").upper()
        normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")

        matching = self._match_actions_for_route(
            route,
            preferred_candidates or candidates,
            message=message,
            identifier=identifier,
            normalized=normalized,
            expected_method=expected_method,
            previous_messages=previous_messages,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            production_kind=production_kind,
            conversation_context=conversation_context,
            description_override=description_override,
            memory_snapshot=memory_snapshot,
            path_markers=path_markers,
            operation_markers=operation_markers,
            exclude_path_markers=exclude_path_markers,
            path_exact_end=path_exact_end,
            path_suffix=path_suffix,
            has_semantic_route=has_semantic_route,
            apply_soft_markers=not preferred_set,
        )
        # Observer preferred ids miss → OpenAPI allowlist completo (E11.S5).
        if not matching and preferred_candidates and preferred_candidates != candidates:
            matching = self._match_actions_for_route(
                route,
                candidates,
                message=message,
                identifier=identifier,
                normalized=normalized,
                expected_method=expected_method,
                previous_messages=previous_messages,
                build_date_branch_parameters=build_date_branch_parameters,
                merge_date_parameters=merge_date_parameters,
                production_kind=production_kind,
                conversation_context=conversation_context,
                description_override=description_override,
                memory_snapshot=memory_snapshot,
                path_markers=path_markers,
                operation_markers=operation_markers,
                exclude_path_markers=exclude_path_markers,
                path_exact_end=path_exact_end,
                path_suffix=path_suffix,
                has_semantic_route=has_semantic_route,
                apply_soft_markers=False,
            )

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
        strategy = "schema"
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

    def _match_actions_for_route(
        self,
        route: dict,
        candidates: list[dict],
        *,
        message: str,
        identifier: str | None,
        normalized: str,
        expected_method: str,
        previous_messages: list | None,
        build_date_branch_parameters: Callable[..., dict] | None,
        merge_date_parameters: Callable[..., dict] | None,
        production_kind: ProductionOperationalIntentKind | None,
        conversation_context: str | None,
        description_override: str | None,
        memory_snapshot: dict | None,
        path_markers: list[str],
        operation_markers: list[str],
        exclude_path_markers: list[str],
        path_exact_end: str,
        path_suffix: str,
        has_semantic_route: bool,
        apply_soft_markers: bool,
    ) -> list[tuple[dict, dict, str]]:
        matching: list[tuple[dict, dict, str]] = []

        for action in candidates:
            if str(action.get("method") or "GET").upper() != expected_method:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            # Soft technical hints (observer): never exclusive when semantic route exists.
            # J-R7: never use `"search" in path` as a semantic gate.
            if apply_soft_markers and not has_semantic_route:
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

        return matching

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
        """Rejeita action cujo contrato semântico não combina com a rota.

        J-R7 / A11-07: path/operationId NÃO são authority. Usa domain,
        intentBinding/continuity facets, parametersSchema, summary/description/tags.
        ``path`` permanece só para assinatura/compat; não entra na decisão.
        """
        _ = path  # execução/observabilidade — não authority semântica
        from app.domain.services.operational_route_registry_service import (
            OperationalRouteRegistryService,
        )
        from app.domain.services.route_segment_inference_service import (
            RouteSegmentInferenceService,
        )

        match_spec = route.get("match") if isinstance(route.get("match"), dict) else {}
        requires_product = bool(match_spec.get("requiresProductIdentifier"))
        domain = str(route.get("domain") or "").strip()
        domain_l = domain.lower()
        route_id = str(route.get("id") or "").strip().lower()
        is_product_domain = domain_l in {
            "product",
            "domainproductsearch",
            "product_search",
        } or route_id.startswith("product")

        schema_params = action.get("parametersSchema") or action.get("parameters_schema") or []
        schema_names = {
            str(item.get("name") or "").strip().lower()
            for item in schema_params
            if isinstance(item, dict) and item.get("name")
        }
        summary_l = str(action.get("summary") or "").lower()
        description_l = str(action.get("description") or "").lower()
        when_to_use_l = str(action.get("whenToUse") or action.get("when_to_use") or "").lower()
        tags_blob = " ".join(
            str(tag).strip().lower() for tag in (action.get("tags") or []) if tag
        )
        operation_id_l = str(
            action.get("operationId") or action.get("operation_id") or ""
        ).lower()
        # Catalog identity (summary/tags/schema/operationId) — never HTTP path fragments.
        semantic_blob = (
            f"{summary_l} {description_l} {when_to_use_l} {tags_blob} "
            f"{operation_id_l} {' '.join(sorted(schema_names))}"
        )

        def _facet_hits_semantic(facet: str) -> bool:
            token = str(facet or "").strip().lower()
            if not token:
                return False
            if token in semantic_blob:
                return True
            compact = token.replace("-", "").replace("_", "")
            blob_compact = (
                semantic_blob.replace("-", "").replace("_", "").replace(" ", "")
            )
            return bool(compact) and compact in blob_compact

        is_search_route = (
            domain in {"domainProductSearch", "product_search"}
            or "search" in route_id
            or "productsearch" in route_id
        )
        if is_search_route:
            search_schema = schema_names & {
                "q",
                "query",
                "description",
                "search",
                "term",
                "group_code",
                "groupcode",
                "text",
            }
            return bool(search_schema) or "search" in semantic_blob

        if "supplier_part_number" in schema_names or "supplierpartnumber" in schema_names:
            # Schema already proves supplier capability — do not require path fragment.
            return True

        facets = RouteSegmentInferenceService.continuity_keys_for_route(
            route,
            aliases=OperationalRouteRegistryService.continuity_facet_aliases(),
        )
        weak_facets = {
            "full",
            "summary",
            "analyser",
            "analyzer",
            "description",
            "detail",
            "list",
            "generic",
        }
        strong_facets = {
            str(item).strip().lower()
            for item in facets
            if str(item).strip() and str(item).strip().lower() not in weak_facets
        }

        product_shaped = requires_product or is_product_domain or (
            {"code", "productcode", "product_code"} & schema_names
        )
        if product_shaped:
            if strong_facets and not any(_facet_hits_semantic(f) for f in strong_facets):
                return False
            return True

        if strong_facets and not any(_facet_hits_semantic(f) for f in strong_facets):
            if (
                str(route.get("id") or "").strip()
                or str(route.get("domain") or "").strip()
                or str(route.get("intentBinding") or "").strip()
            ):
                return False

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
        """Bind parameters via schema OpenAPI (E11.S3) — sem path→strategy."""
        from app.domain.services.parameter_strategy_shadow_service import (
            ParameterStrategyShadowService,
        )

        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message or ""
        )

        return ParameterStrategyShadowService.bind_schema_first(
            action,
            message,
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
