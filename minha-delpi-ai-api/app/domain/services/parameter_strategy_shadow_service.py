"""E1.S5 — parameterStrategy: shadow e cutover completo para binder/domínio canônico."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Fila completa E1.S5 (resolver). sql fica só em domains / fora do resolver.
_CUTOVER_STRATEGIES = frozenset(
    {
        "schema",
        "none",
        "semantic",
        "sale_orders",
        "supplier_part_number",
        "supplies_stock",
        "exclusive_catalog",
        "lmp",
        "product_search",
        "system_metadata",
        "department_idd",
        "product_code",
        "date_branch",
    }
)

# Strategies em que o OpenAPI binder é authority; demais usam domain binder via este serviço.
_BINDER_AUTHORITY = frozenset(
    {
        "schema",
        "none",
        "semantic",
        "sale_orders",
        "supplier_part_number",
        "supplies_stock",
        "product_code",
        "date_branch",
    }
)


class ParameterStrategyShadowObservabilityService:
    @classmethod
    def record(cls, shadow: dict[str, Any] | None) -> None:
        if not isinstance(shadow, dict):
            return
        logger.info(
            "parameter_strategy_shadow",
            extra={
                "metric": "parameter_strategy_shadow",
                "strategy": str(shadow.get("strategy") or ""),
                "authority": str(shadow.get("authority") or ""),
                "agree": bool(shadow.get("agree")),
                "agreeExact": bool(shadow.get("agreeExact")),
                "agreeCompatible": bool(shadow.get("agreeCompatible")),
                "legacyKeyCount": int(shadow.get("legacyKeyCount") or 0),
                "candidateKeyCount": int(shadow.get("candidateKeyCount") or 0),
                "error": str(shadow.get("error") or "") or None,
            },
        )


class ParameterStrategyShadowService:
    """Cutover E1.S5: authority no binder OpenAPI ou domain binder canônico (não no switch do resolver)."""

    @classmethod
    def cutover_strategies(cls) -> frozenset[str]:
        return _CUTOVER_STRATEGIES

    @classmethod
    def shadowable_strategies(cls) -> frozenset[str]:
        return _CUTOVER_STRATEGIES

    @classmethod
    def cutover_enabled(cls) -> bool:
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        return OpenApiToolRoutingContentService.bool_setting(
            "parameterStrategyShadow",
            "cutoverEnabled",
            default=False,
        )

    @classmethod
    def shadow_enabled(cls) -> bool:
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        return OpenApiToolRoutingContentService.bool_setting(
            "parameterStrategyShadow",
            "enabled",
            default=False,
        )

    @classmethod
    def uses_openapi_authority(cls, strategy: str) -> bool:
        return str(strategy or "").strip() in _CUTOVER_STRATEGIES and cls.cutover_enabled()

    @classmethod
    def bind_schema_first(
        cls,
        action: dict[str, Any],
        message: str,
        *,
        previous_messages: list | None = None,
        catalog: Any = None,
        identifier: str | None = None,
        conversation_context: str | None = None,
        memory_snapshot: dict | None = None,
        production_kind: Any = None,
        route: dict | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        description_override: str | None = None,
        normalized: str | None = None,
    ) -> dict[str, Any] | None:
        """E11.S3 — bind only from OpenAPI schema + message grounding (no path→strategy)."""
        _ = (merge_date_parameters, description_override, normalized)
        from app.application.services.plan_external_actions_service import (
            PlanExternalActionsService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_tool_grounding_context_service import (
            ChatToolGroundingContextService,
        )

        schema_params = action.get("parametersSchema") or action.get("parameters_schema") or []
        schema_names = {
            str(item.get("name") or "").strip()
            for item in schema_params
            if isinstance(item, dict) and item.get("name")
        }
        schema_names_lower = {name.lower() for name in schema_names}
        product_names = {"code", "productcode", "product_code"} & schema_names_lower
        supplier_names = {
            "supplier_part_number",
            "supplierpartnumber",
        } & schema_names_lower
        date_names = {
            "branch",
            "start_date",
            "end_date",
            "date_start",
            "date_end",
            "startdate",
            "enddate",
            "granularity",
        } & schema_names_lower

        context_parameters: dict[str, Any] = {}
        if product_names:
            code = str(identifier or "").strip()
            if not code:
                code = ChatProductQueryIntentService.extract_product_code(message or "") or ""
            if not code:
                code = (
                    ChatProductQueryIntentService.resolve_product_code(
                        message or "",
                        conversation_context,
                        previous_messages=previous_messages,
                        memory_snapshot=memory_snapshot
                        or ChatToolGroundingContextService.current_memory_snapshot(),
                    )
                    or ""
                )
            # Required path/query code without value → cannot bind this action.
            required_code = False
            for item in schema_params:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip().lower()
                if name in product_names and bool(item.get("required")):
                    required_code = True
                    break
            if required_code and not code:
                return None
            if code:
                context_parameters = {"code": code, "productCode": code, "product_code": code}

        parameters, _body, _missing = PlanExternalActionsService._bind_arguments(
            message,
            action,
            context_parameters=context_parameters,
            previous_messages=previous_messages,
        )
        params = dict(parameters) if isinstance(parameters, dict) else {}
        params = cls._apply_cutover_schema_defaults(action, params)

        if supplier_names:
            part = str(
                params.get("supplier_part_number") or params.get("supplierPartNumber") or ""
            ).strip()
            if not part:
                return None

        if product_names and catalog is not None and hasattr(catalog, "build_product_parameters"):
            code = str(
                params.get("code")
                or params.get("productCode")
                or context_parameters.get("code")
                or ""
            ).strip()
            if code:
                built = catalog.build_product_parameters(
                    action,
                    code,
                    message=message,
                    previous_messages=previous_messages,
                )
                if isinstance(built, dict):
                    params = built

        if date_names:
            params = cls._enrich_date_branch(
                action,
                message,
                params,
                previous_messages=previous_messages,
                production_kind=production_kind,
                route=route,
                catalog=catalog,
                build_date_branch_parameters=build_date_branch_parameters,
            )

        if catalog is not None and hasattr(catalog, "filter_parameters_to_schema"):
            params = catalog.filter_parameters_to_schema(action, params)
        return params

    @classmethod
    def bind_via_openapi(
        cls,
        action: dict[str, Any],
        message: str,
        *,
        previous_messages: list | None = None,
        strategy: str | None = None,
        catalog: Any = None,
        identifier: str | None = None,
        conversation_context: str | None = None,
        memory_snapshot: dict | None = None,
        production_kind: Any = None,
        route: dict | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        description_override: str | None = None,
        normalized: str | None = None,
    ) -> dict[str, Any] | None:
        strategy_name = str(strategy or "").strip()
        if strategy_name in _BINDER_AUTHORITY:
            return cls._bind_openapi_authority(
                action,
                message,
                previous_messages=previous_messages,
                strategy=strategy_name,
                catalog=catalog,
                identifier=identifier,
                conversation_context=conversation_context,
                memory_snapshot=memory_snapshot,
                production_kind=production_kind,
                route=route,
                build_date_branch_parameters=build_date_branch_parameters,
            )
        # Domain binders canônicos (ainda tipados por strategy até E1.S6 remover o campo).
        return cls.legacy_strategy_parameters(
            strategy=strategy_name,
            action=action,
            message=message,
            previous_messages=previous_messages,
            catalog=catalog,
            identifier=identifier,
            conversation_context=conversation_context,
            memory_snapshot=memory_snapshot,
            production_kind=production_kind,
            route=route,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            description_override=description_override,
            normalized=normalized,
        )

    @classmethod
    def _bind_openapi_authority(
        cls,
        action: dict[str, Any],
        message: str,
        *,
        previous_messages: list | None,
        strategy: str,
        catalog: Any,
        identifier: str | None,
        conversation_context: str | None,
        memory_snapshot: dict | None,
        production_kind: Any,
        route: dict | None,
        build_date_branch_parameters: Callable[..., dict] | None,
    ) -> dict[str, Any] | None:
        from app.application.services.plan_external_actions_service import (
            PlanExternalActionsService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_tool_grounding_context_service import (
            ChatToolGroundingContextService,
        )

        context_parameters: dict[str, Any] = {}
        if strategy == "product_code":
            code = str(identifier or "").strip()
            if not code:
                code = ChatProductQueryIntentService.extract_product_code(message or "") or ""
            if not code:
                code = (
                    ChatProductQueryIntentService.resolve_product_code(
                        message or "",
                        conversation_context,
                        previous_messages=previous_messages,
                        memory_snapshot=memory_snapshot
                        or ChatToolGroundingContextService.current_memory_snapshot(),
                    )
                    or ""
                )
            if not code:
                return None
            context_parameters = {"code": code, "productCode": code, "product_code": code}

        parameters, _body, _missing = PlanExternalActionsService._bind_arguments(
            message,
            action,
            context_parameters=context_parameters,
            previous_messages=previous_messages,
        )
        params = dict(parameters) if isinstance(parameters, dict) else {}
        params = cls._apply_cutover_schema_defaults(action, params)

        if strategy == "supplier_part_number":
            part = str(
                params.get("supplier_part_number") or params.get("supplierPartNumber") or ""
            ).strip()
            if not part:
                return None

        if strategy == "product_code" and catalog is not None:
            code = str(
                params.get("code")
                or params.get("productCode")
                or context_parameters.get("code")
                or ""
            ).strip()
            if not code:
                return None
            built = catalog.build_product_parameters(
                action,
                code,
                message=message,
                previous_messages=previous_messages,
            )
            return built if isinstance(built, dict) else params

        if strategy == "date_branch":
            params = cls._enrich_date_branch(
                action,
                message,
                params,
                previous_messages=previous_messages,
                production_kind=production_kind,
                route=route,
                catalog=catalog,
                build_date_branch_parameters=build_date_branch_parameters,
            )

        if catalog is not None and hasattr(catalog, "filter_parameters_to_schema"):
            params = catalog.filter_parameters_to_schema(action, params)
        return params

    @classmethod
    def _enrich_date_branch(
        cls,
        action: dict[str, Any],
        message: str,
        parameters: dict[str, Any],
        *,
        previous_messages: list | None,
        production_kind: Any,
        route: dict | None,
        catalog: Any,
        build_date_branch_parameters: Callable[..., dict] | None,
    ) -> dict[str, Any]:
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
        from app.domain.services.operational_route_query_defaults_service import (
            OperationalRouteQueryDefaultsService,
        )

        params = dict(parameters)
        if build_date_branch_parameters and not any(
            key in params
            for key in ("start_date", "end_date", "date_start", "date_end", "branch")
        ):
            built = build_date_branch_parameters(
                action,
                message,
                previous_messages=previous_messages,
            )
            if isinstance(built, dict):
                for key, value in built.items():
                    if key not in params and value is not None:
                        params[key] = value

        if production_kind in {
            ProductionOperationalIntentKind.LOSSES_TOP,
            ProductionOperationalIntentKind.LOSSES_RECORDS,
        }:
            loss_type = ChatProductionOperationalIntentService.infer_loss_type(
                ChatMessageNormalizationService.normalize_for_matching(message)
            )
            if loss_type:
                params["loss_type"] = loss_type

        if production_kind == ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM:
            product_code = ChatProductQueryIntentService.extract_product_code(message)
            if product_code:
                params["code"] = product_code

        if production_kind == ProductionOperationalIntentKind.SCHEDULE_TODAY:
            filter_code = ChatProductQueryIntentService.resolve_schedule_product_filter_code(
                message,
                product_code=ChatProductQueryIntentService.extract_product_code(message),
            )
            if filter_code:
                params["presentationDetailFilter"] = {"product_code_prefix": filter_code}

        params = OperationalRouteQueryDefaultsService.apply(
            action,
            params,
            route=route or {},
        )
        return params

    @classmethod
    def _apply_cutover_schema_defaults(
        cls,
        action: dict[str, Any],
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        from app.domain.services.chat_operational_pagination_defaults_service import (
            ChatOperationalPaginationDefaultsService,
        )

        schema_params = action.get("parametersSchema") or action.get("parameters_schema") or []
        if not isinstance(schema_params, list):
            return parameters
        schema_names_lower = {
            str(item.get("name") or "").strip().lower()
            for item in schema_params
            if isinstance(item, dict) and item.get("name")
        }
        merged = dict(parameters)
        for parameter in schema_params:
            if not isinstance(parameter, dict):
                continue
            name = str(parameter.get("name") or "").strip()
            if not name or name in merged:
                continue
            lowered = name.lower()
            if lowered == "page":
                merged[name] = 1
            elif lowered in {"page_size", "pagesize"}:
                merged[name] = ChatOperationalPaginationDefaultsService.standard()
            elif lowered in {"top_limit", "toplimit"}:
                merged[name] = ChatOperationalPaginationDefaultsService.supplies_stock_top_limit()
            elif lowered == "limit" and "top_limit" in schema_names_lower:
                merged[name] = ChatOperationalPaginationDefaultsService.supplies_stock_top_limit()
            elif lowered == "limit" and "page_size" not in schema_names_lower:
                merged[name] = ChatOperationalPaginationDefaultsService.supplies_stock_top_limit()
        return merged

    @classmethod
    def legacy_strategy_parameters(
        cls,
        *,
        strategy: str,
        action: dict[str, Any],
        message: str,
        previous_messages: list | None = None,
        catalog: Any = None,
        identifier: str | None = None,
        conversation_context: str | None = None,
        memory_snapshot: dict | None = None,
        production_kind: Any = None,
        route: dict | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        description_override: str | None = None,
        normalized: str | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )
        from app.domain.services.chat_operational_pagination_defaults_service import (
            ChatOperationalPaginationDefaultsService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_tool_grounding_context_service import (
            ChatToolGroundingContextService,
        )
        from app.domain.services.operational_route_query_defaults_service import (
            OperationalRouteQueryDefaultsService,
        )

        name = str(strategy or "").strip()
        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message or ""
        )

        if name in {"none", "semantic"}:
            return {}

        if name == "sale_orders":
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            return OperationalApiParameterBuilderService().build_sale_orders(
                action,
                message,
                previous_messages=previous_messages,
            )

        if name == "supplier_part_number":
            from app.domain.services.chat_operational_identifier_resolution_service import (
                ChatOperationalIdentifierResolutionService,
            )

            part_number = ChatOperationalIdentifierResolutionService.primary_supplier_part_number(
                message or ""
            )
            if not part_number:
                return None
            parameters = {
                "supplier_part_number": part_number,
                "page": 1,
                "page_size": ChatOperationalPaginationDefaultsService.standard(),
            }
            if catalog is not None and hasattr(catalog, "filter_parameters_to_schema"):
                return catalog.filter_parameters_to_schema(action, parameters)
            return parameters

        if name == "supplies_stock":
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            return OperationalApiParameterBuilderService.build_supplies_stock(action)

        if name == "product_search":
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

        if name == "lmp":
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
                    param_name = parameter.get("name")
                    if param_name and str(param_name).lower() in {"sale_number", "ordem", "ov"}:
                        return {param_name: sale_number}
                return {"sale_number": sale_number}
            parameters: dict[str, Any] = {}
            for parameter in action.get("parametersSchema") or []:
                param_name = parameter.get("name")
                if not param_name:
                    continue
                lowered = str(param_name).lower()
                if lowered == "page":
                    parameters[param_name] = 1
                elif lowered in {"page_size", "pagesize", "limit"}:
                    parameters[param_name] = ChatOperationalPaginationDefaultsService.standard()
                elif lowered == "status" and "/dashboard" in path.lower():
                    parameters[param_name] = "Todos"
            if not parameters:
                parameters = (
                    {}
                    if "/dashboard" in path.lower()
                    else {
                        "page": 1,
                        "page_size": ChatOperationalPaginationDefaultsService.standard(),
                    }
                )
            if merge_date_parameters:
                return merge_date_parameters(action, message, parameters)
            return parameters

        if name == "exclusive_catalog":
            if catalog is None or not hasattr(catalog, "build_exclusive_catalog_parameters"):
                return {}
            return catalog.build_exclusive_catalog_parameters(
                action,
                message=message,
                normalized=normalized_text or message.lower(),
            )

        if name == "system_metadata":
            from app.domain.services.chat_system_metadata_intent_service import (
                ChatSystemMetadataIntentService,
            )

            return ChatSystemMetadataIntentService.build_parameters(message, action)

        if name == "department_idd":
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
                route=route or {},
            )
            if catalog is not None and hasattr(catalog, "filter_parameters_to_schema"):
                return catalog.filter_parameters_to_schema(action, parameters)
            return parameters

        if name == "product_code":
            code = str(identifier or "").strip()
            if not code:
                code = ChatProductQueryIntentService.extract_product_code(message or "") or ""
            if not code:
                code = (
                    ChatProductQueryIntentService.resolve_product_code(
                        message or "",
                        conversation_context,
                        previous_messages=previous_messages,
                        memory_snapshot=memory_snapshot
                        or ChatToolGroundingContextService.current_memory_snapshot(),
                    )
                    or ""
                )
            if not code or catalog is None:
                return None if not code else {"code": code}
            return catalog.build_product_parameters(
                action,
                code,
                message=message,
                previous_messages=previous_messages,
            )

        if name == "date_branch":
            parameters: dict[str, Any] = {}
            if build_date_branch_parameters:
                parameters = build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                ) or {}
            parameters = cls._enrich_date_branch(
                action,
                message,
                parameters if isinstance(parameters, dict) else {},
                previous_messages=previous_messages,
                production_kind=production_kind,
                route=route,
                catalog=catalog,
                build_date_branch_parameters=None,
            )
            if catalog is not None and hasattr(catalog, "filter_parameters_to_schema"):
                return catalog.filter_parameters_to_schema(action, parameters)
            return parameters

        return {}

    @classmethod
    def compare(
        cls,
        *,
        strategy: str,
        legacy_parameters: dict[str, Any] | None,
        action: dict[str, Any],
        message: str,
        previous_messages: list | None = None,
        catalog: Any = None,
        identifier: str | None = None,
        conversation_context: str | None = None,
        memory_snapshot: dict | None = None,
        production_kind: Any = None,
        route: dict | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        description_override: str | None = None,
        normalized: str | None = None,
    ) -> dict[str, Any] | None:
        strategy_name = str(strategy or "").strip()
        if strategy_name not in _CUTOVER_STRATEGIES:
            return None
        if not cls.shadow_enabled():
            return None

        try:
            binder_or_domain = cls.bind_via_openapi(
                action,
                message,
                previous_messages=previous_messages,
                strategy=strategy_name,
                catalog=catalog,
                identifier=identifier,
                conversation_context=conversation_context,
                memory_snapshot=memory_snapshot,
                production_kind=production_kind,
                route=route,
                build_date_branch_parameters=build_date_branch_parameters,
                merge_date_parameters=merge_date_parameters,
                description_override=description_override,
                normalized=normalized,
            )
            if binder_or_domain is None:
                binder_or_domain = {}
            # Observer: sempre o path legado tipado (mesmo método com cutover mental off).
            strategy_params = cls.legacy_strategy_parameters(
                strategy=strategy_name,
                action=action,
                message=message,
                previous_messages=previous_messages,
                catalog=catalog,
                identifier=identifier,
                conversation_context=conversation_context,
                memory_snapshot=memory_snapshot,
                production_kind=production_kind,
                route=route,
                build_date_branch_parameters=build_date_branch_parameters,
                merge_date_parameters=merge_date_parameters,
                description_override=description_override,
                normalized=normalized,
            )
            if strategy_params is None:
                strategy_params = {}
        except Exception:
            shadow = {
                "strategy": strategy_name,
                "authority": "error",
                "legacyParameters": cls._normalize_params(legacy_parameters),
                "candidateParameters": {},
                "agree": False,
                "agreeExact": False,
                "agreeCompatible": False,
                "legacyKeyCount": 0,
                "candidateKeyCount": 0,
                "error": "bind_failed",
            }
            ParameterStrategyShadowObservabilityService.record(shadow)
            return shadow

        cutover = cls.cutover_enabled()
        if cutover:
            if strategy_name in _BINDER_AUTHORITY:
                authority_params = binder_or_domain
                observer_params = strategy_params
                authority = "openapi_binder"
            else:
                authority_params = binder_or_domain
                observer_params = strategy_params
                authority = "domain_binder"
        else:
            authority_params = (
                legacy_parameters if legacy_parameters is not None else strategy_params
            )
            observer_params = binder_or_domain
            authority = "strategy"

        authority_n = cls._normalize_params(authority_params)
        observer_n = cls._normalize_params(observer_params)
        agree_exact = authority_n == observer_n
        agree_compatible = all(
            observer_n.get(key) == value for key, value in authority_n.items()
        )
        if strategy_name in {"none", "semantic"}:
            agree = agree_exact
        else:
            agree = agree_compatible

        shadow = {
            "strategy": strategy_name,
            "authority": authority,
            "cutover": cutover,
            "legacyParameters": observer_n if cutover else authority_n,
            "candidateParameters": authority_n if cutover else observer_n,
            "agree": agree,
            "agreeExact": agree_exact,
            "agreeCompatible": agree_compatible,
            "legacyKeyCount": len(observer_n if cutover else authority_n),
            "candidateKeyCount": len(authority_n if cutover else observer_n),
        }
        ParameterStrategyShadowObservabilityService.record(shadow)
        return shadow

    @staticmethod
    def _normalize_params(parameters: dict[str, Any] | None) -> dict[str, str]:
        normalized: dict[str, str] = {}
        if not isinstance(parameters, dict):
            return normalized
        for key, value in parameters.items():
            name = str(key or "").strip()
            if not name or value is None:
                continue
            if isinstance(value, (dict, list)):
                text = str(value)
            else:
                text = str(value).strip()
            if not text:
                continue
            normalized[name] = text
        return normalized
