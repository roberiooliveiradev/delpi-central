import re

from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_route_context_service import ChatRouteContextService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionSelectionService:
    HIERARCHICAL_PRODUCT_MAX_DEPTH = 15
    def __init__(self, repository, semantic_ranker=None):
        self.repository = repository
        self.semantic_ranker = semantic_ranker

    def select_action_for_product(
        self,
        message: str,
        *,
        product_code: str,
        allowed_action_ids: list[str] | None = None,
        intent: str | None = None,
        route_segment: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        code = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not code or ChatAnalysisIntentService.looks_like_path_placeholder(code):
            return None

        resolved_intent = intent or ChatProductQueryIntentService.detect(message)
        resolved_segment = route_segment or ChatRouteContextService.resolve_product_route_segment(
            message
        )
        preferred_action_id = None

        if previous_messages and resolved_intent == ChatProductQueryIntent.STOCK:
            preferred_action_id = self._resolve_previous_external_action_id(
                previous_messages,
                path_fragment="/stock",
            )

        return self._select_product_action(
            message,
            code,
            allowed_action_ids=allowed_action_ids or [],
            intent=resolved_intent,
            route_segment=resolved_segment,
            preferred_action_id=preferred_action_id,
        )

    def select_action(
        self,
        message: str,
        allowed_action_ids: list[str] | None = None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        allowed_action_ids = allowed_action_ids or []

        if ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ) and ChatConversationContextService.has_recent_tool_data(previous_messages):
            return None

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            return None

        if ChatCanvasIntentService.blocks_external_action_selection(message):
            return None

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return None

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            from app.domain.services.chat_sql_production_query_service import (
                ChatSqlProductionQueryService,
            )

            if not ChatSqlIntentService.is_authoring_request(message):
                resolution = ChatSqlProductionQueryService.resolve(message)
                if resolution and resolution.mode == "execute":
                    selected = self._select_sql_or_data_action(
                        message,
                        allowed_action_ids=allowed_action_ids,
                        sql=resolution.sql,
                    )
                    if selected:
                        return selected

            return None

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return None

        refinement = ChatOperationalRefinementService.detect(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if refinement and refinement.kind in {"stock_refinement", "stock_reset"}:
            previous_stock_action_id = self._resolve_previous_external_action_id(
                previous_messages,
                path_fragment="/stock",
            )
            selected = self._select_product_action(
                message,
                str(refinement.product_code or ""),
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STOCK,
                preferred_action_id=previous_stock_action_id,
            )

            if selected:
                return selected

        if refinement and refinement.kind in {"metric_refinement", "metric_reset"}:
            selected = self._select_metric_refinement_action(
                message,
                refinement,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if refinement and refinement.kind == "pagination_refinement":
            selected = self._select_pagination_refinement_action(
                refinement,
                allowed_action_ids=allowed_action_ids,
                message=message,
            )

            if selected:
                return selected

        if refinement and refinement.kind == "depth_refinement":
            selected = self._select_depth_refinement_action(
                refinement,
                allowed_action_ids=allowed_action_ids,
                message=message,
            )

            if selected:
                return selected

        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        sql_refinement = ChatSqlQueryRefinementService.resolve(
            message,
            previous_messages=previous_messages,
        )

        if sql_refinement and sql_refinement.mode == "execute":
            selected = self._select_sql_or_data_action(
                message,
                allowed_action_ids=allowed_action_ids,
                sql=sql_refinement.sql,
            )

            if selected:
                selected["reason"] = ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "sqlRefinement",
                )
                return selected

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        group_search_code = self._extract_search_group_code(message, normalized)

        if group_search_code and self._looks_like_product_search(normalized):
            selected = self._select_product_search_action(
                message,
                normalized,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        from app.domain.services.chat_product_description_resolution_service import (
            ChatProductDescriptionResolutionService,
        )

        description_lookup = ChatProductDescriptionResolutionService.extract_description_query(
            message,
        )

        if description_lookup and not ChatProductDescriptionResolutionService.extract_code_from_drilldown_message(
            message,
        ):
            resolved_from_history = ChatProductDescriptionResolutionService.resolve_code_from_history(
                description_lookup,
                previous_messages=previous_messages,
            )

            if not resolved_from_history:
                selected = self._select_product_search_action(
                    message,
                    normalized,
                    allowed_action_ids=allowed_action_ids,
                    description_override=description_lookup,
                )

                if selected:
                    return selected

        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
            previous_messages=previous_messages,
        )
        product_intent = ChatProductQueryIntentService.resolve_product_intent(
            message,
            previous_messages=previous_messages,
        )
        product_route_segment = ChatRouteContextService.resolve_product_route_segment(
            message,
            previous_messages=previous_messages,
        )

        if self._looks_like_sale_orders_list_question(normalized):
            selected = self._select_sale_orders_action(
                message,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        if self._looks_like_transforma_question(normalized):
            selected = self._select_transforma_action(
                message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if self._looks_like_lmp_question(normalized):
            selected = self._select_lmp_action(
                message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
            )

            if selected:
                return selected

        if (
            self._looks_like_system_metadata_question(normalized)
            and not product_code
            and not ChatSqlQueryRefinementService.is_sql_follow_up(
                message,
                previous_messages=previous_messages,
            )
        ):
            selected = self._select_system_metadata_action(
                message,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        if self._looks_like_cpv_question(normalized) and not product_code:
            selected = self._select_supplies_metric_action(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="cpv",
                operation_token="cpv",
                reason="A pergunta solicita o indicador CPV de suprimentos.",
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if self._looks_like_otd_question(normalized) and not product_code:
            selected = self._select_supplies_metric_action(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="otd",
                operation_token="otd",
                reason="A pergunta solicita o indicador OTD de suprimentos.",
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if self._looks_like_inventory_turnover_question(normalized) and not product_code:
            selected = self._select_supplies_metric_action(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="inventory-turnover",
                operation_token="inventory_turnover",
                reason="A pergunta solicita giro de estoque (IDD) em suprimentos.",
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if self._looks_like_supplies_stock_kpi(normalized) and not product_code:
            selected = self._select_supplies_stock_value_action(
                message,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        if product_code and product_intent == ChatProductQueryIntent.PARENTS:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.PARENTS,
            )

            if selected:
                return selected

        if product_code and product_intent == ChatProductQueryIntent.STRUCTURE:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STRUCTURE,
            )

            if selected:
                return selected

        if product_code and product_intent == ChatProductQueryIntent.STOCK:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STOCK,
            )

            if selected:
                return selected

        if product_code and product_intent == ChatProductQueryIntent.SUMMARY:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.SUMMARY,
            )

            if selected:
                return selected

        if product_code and product_intent == ChatProductQueryIntent.ANALYSER:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.ANALYSER,
            )

            if selected:
                return selected

        if product_code and product_intent == ChatProductQueryIntent.DESCRIPTION:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.DESCRIPTION,
            )

            if selected:
                return selected

        if product_code and (
            self._looks_like_product_question(normalized)
            or ChatProductQueryIntentService.extract_product_code(message)
            or product_route_segment
            or ChatProductDescriptionResolutionService.looks_like_description_lookup(message)
        ):
            return self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.FULL,
                route_segment=product_route_segment,
            )

        if not product_code and self._looks_like_product_search(normalized):
            selected = self._select_product_search_action(
                message,
                normalized,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        department_kpi = ChatDepartmentKpiIntentService.resolve(message)

        if department_kpi and department_kpi.domain_prefix.startswith("/quality/audit-5s/") and not product_code:
            selected = self._select_department_kpi_action(
                message,
                allowed_action_ids=allowed_action_ids,
                match=department_kpi,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if self._looks_like_sql_or_data_query(message):
            if ChatSqlIntentService.should_auto_execute_sql(message):
                return self._select_sql_or_data_action(
                    message,
                    allowed_action_ids=allowed_action_ids,
                )

        from app.domain.services.chat_operational_parameter_service import (
            ChatOperationalParameterService,
        )

        if ChatOperationalParameterService.should_block_semantic_action_fallback(
            message,
            conversation_context=conversation_context,
        ):
            return None

        department_kpi = ChatDepartmentKpiIntentService.resolve(message)

        if department_kpi and not product_code:
            selected = self._select_department_kpi_action(
                message,
                allowed_action_ids=allowed_action_ids,
                match=department_kpi,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        return self._select_generic_allowed_action(
            message,
            allowed_action_ids=allowed_action_ids,
        )

    def _looks_like_product_question(self, value: str) -> bool:
        terms = [
            "produto",
            "product",
            "item",
            "código",
            "codigo",
            "referência",
            "referencia",
            "ref ",
            " sku",
            "material",
            "insumo",
            "mp ",
            "informações do produto",
            "informacoes do produto",
            "dados do produto",
            "busque as informações do produto",
            "busque informacoes do produto",
            "consulta produto",
            "api delpi",
            "compra",
            "compras",
            "venda",
            "vendas",
            "faturamento",
            "carteira",
            "estrutura",
            "composição",
            "composicao",
            "componentes",
            "bom",
            "roteiro",
            "fornecedor",
            "fornecedores",
            "supplier",
            "preço",
            "preco",
            "pricing",
            "movimenta",
            "inspeç",
            "inspec",
            "nota",
            "fiscal",
            "nfe",
            "clientes",
            "customer",
            "onde é usado",
            "onde e usado",
            "produto pai",
            "pai do",
            "parent",
            "where used",
            "quanto custa",
            "custo do",
            "notas de entrada",
            "notas de saída",
            "notas de saida",
            "nota de entrada",
            "nota de saída",
            "nota de saida",
        ]

        return any(term in value for term in terms)

    def _looks_like_cpv_question(self, value: str) -> bool:
        return any(
            term in value
            for term in (
                "cpv",
                "custo de produção vendido",
                "custo de producao vendido",
                "custo producao vendido",
            )
        )

    def _looks_like_otd_question(self, value: str) -> bool:
        return any(
            term in value
            for term in (
                " otd",
                "otd ",
                "on-time delivery",
                "entrega no prazo",
                "entregas no prazo",
            )
        ) or value.strip().startswith("otd")

    def _looks_like_inventory_turnover_question(self, value: str) -> bool:
        return any(
            term in value
            for term in (
                "giro de estoque",
                "giro do estoque",
                "giro estoque",
                " rotatividade",
                "idd",
                "inventory-turnover",
            )
        )

    def _looks_like_supplies_stock_kpi(self, value: str) -> bool:
        terms = [
            "valor total",
            "valor de estoque",
            "valor do estoque",
            "valor em estoque",
        ]

        return any(term in value for term in terms)

    def _select_metric_refinement_action(
        self,
        message: str,
        refinement,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
    ) -> dict | None:
        if refinement.metric_kind == "supplies" and refinement.metric_path_token:
            return self._select_supplies_metric_action(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token=str(refinement.metric_path_token),
                operation_token=str(refinement.metric_path_token),
                reason=refinement.reason or "Refino de indicador de suprimentos.",
                previous_messages=previous_messages,
            )

        if refinement.metric_kind == "department_kpi" and refinement.metric_path_token:
            from app.domain.services.chat_department_kpi_intent_service import (
                DepartmentKpiMatch,
            )

            match = DepartmentKpiMatch(
                path_token=str(refinement.metric_path_token),
                domain_prefix=str(refinement.metric_domain_prefix or ""),
                reason=refinement.reason or "Refino de KPI departamental.",
            )

            return self._select_department_kpi_action(
                message,
                allowed_action_ids,
                match=match,
                previous_messages=previous_messages,
            )

        return None

    def _select_department_kpi_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        match,
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        path_token = str(match.path_token or "").lower()
        domain_prefix = str(match.domain_prefix or "").lower()

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()

            if domain_prefix and domain_prefix not in path:
                continue

            if path_token and path_token not in path:
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": self._build_date_branch_parameters(
                        action,
                        message,
                        previous_messages=previous_messages,
                    ),
                },
                "reason": match.reason,
            }

        return None

    def _select_pagination_refinement_action(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
    ) -> dict | None:
        action_id = str(refinement.action_id or "").strip()
        allowed = set(allowed_action_ids or [])

        if action_id and action_id in allowed:
            selected = self._build_pagination_refinement_action(
                refinement,
                action_id=action_id,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        product_code = str(refinement.product_code or "").strip()
        route_segment = str(refinement.route_segment or "").strip()

        if not product_code or not route_segment:
            return None

        intent_by_segment = {
            "parents": ChatProductQueryIntent.PARENTS,
            "structure": ChatProductQueryIntent.STRUCTURE,
            "stock": ChatProductQueryIntent.STOCK,
        }
        intent = intent_by_segment.get(route_segment)

        if not intent:
            return None

        selected = self._select_product_action(
            message or "paginação",
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
        )

        if not selected:
            return None

        resolved_action_id = str(
            (selected.get("arguments") or {}).get("actionId") or ""
        ).strip()

        if not resolved_action_id:
            return None

        return self._build_pagination_refinement_action(
            refinement,
            action_id=resolved_action_id,
            allowed_action_ids=allowed_action_ids,
            base_parameters=dict(
                refinement.previous_parameters
                or (selected.get("arguments") or {}).get("parameters")
                or {}
            ),
            fallback_reason=selected.get("reason"),
        )

    def _select_depth_refinement_action(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
    ) -> dict | None:
        action_id = str(refinement.action_id or "").strip()
        allowed = set(allowed_action_ids or [])

        if action_id and action_id in allowed:
            selected = self._build_depth_refinement_action(
                refinement,
                action_id=action_id,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        product_code = str(refinement.product_code or "").strip()
        route_segment = str(refinement.route_segment or "").strip()

        if not product_code or route_segment not in {"parents", "structure"}:
            return None

        intent_by_segment = {
            "parents": ChatProductQueryIntent.PARENTS,
            "structure": ChatProductQueryIntent.STRUCTURE,
        }
        intent = intent_by_segment.get(route_segment)

        if not intent:
            return None

        selected = self._select_product_action(
            message or "profundidade",
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
        )

        if not selected:
            return None

        resolved_action_id = str(
            (selected.get("arguments") or {}).get("actionId") or ""
        ).strip()

        if not resolved_action_id:
            return None

        return self._build_depth_refinement_action(
            refinement,
            action_id=resolved_action_id,
            allowed_action_ids=allowed_action_ids,
            base_parameters=dict(
                refinement.previous_parameters
                or (selected.get("arguments") or {}).get("parameters")
                or {}
            ),
            fallback_reason=selected.get("reason"),
        )

    def _build_depth_refinement_action(
        self,
        refinement,
        *,
        action_id: str,
        allowed_action_ids: list[str],
        base_parameters: dict | None = None,
        fallback_reason: str | None = None,
    ) -> dict | None:
        selected = self._build_pagination_refinement_action(
            refinement,
            action_id=action_id,
            allowed_action_ids=allowed_action_ids,
            base_parameters=base_parameters,
            fallback_reason=fallback_reason,
        )

        if not selected or refinement.max_depth is None:
            return selected

        candidates = self.repository.find_candidate_actions(
            "",
            limit=80,
            allowed_action_ids=allowed_action_ids,
        )

        action = next(
            (
                item
                for item in candidates
                if str(item.get("actionId") or "") == action_id
            ),
            None,
        )

        if not action:
            return selected

        parameters = dict((selected.get("arguments") or {}).get("parameters") or {})

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"max_depth", "maxdepth", "depth", "nivel", "levels"}:
                parameters[name] = self._clamp_max_depth_for_path(
                    refinement.max_depth,
                    str(action.get("path") or ""),
                )

        reason = fallback_reason or refinement.reason or (
            "A mensagem amplia a profundidade da consulta hierárquica já feita nesta conversa."
        )

        return {
            **selected,
            "arguments": {
                **(selected.get("arguments") or {}),
                "parameters": parameters,
            },
            "reason": reason,
        }

    def _build_pagination_refinement_action(
        self,
        refinement,
        *,
        action_id: str,
        allowed_action_ids: list[str],
        base_parameters: dict | None = None,
        fallback_reason: str | None = None,
    ) -> dict | None:
        candidates = self.repository.find_candidate_actions(
            "",
            limit=80,
            allowed_action_ids=allowed_action_ids,
        )

        action = next(
            (
                item
                for item in candidates
                if str(item.get("actionId") or "") == action_id
            ),
            None,
        )

        if not action:
            return None

        parameters = dict(base_parameters or refinement.previous_parameters or {})

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if refinement.page_size is not None and lowered in {
                "page_size",
                "pagesize",
                "limit",
            }:
                parameters[name] = refinement.page_size
            elif refinement.page is not None and lowered == "page":
                parameters[name] = refinement.page

        reason = fallback_reason or refinement.reason or (
            "A mensagem ajusta paginação da consulta operacional já feita nesta conversa."
        )

        if refinement.page_size is not None:
            reason = (
                f"A mensagem aumenta o limite da consulta para "
                f"{refinement.page_size} registro(s)."
            )
        elif refinement.page is not None:
            reason = f"A mensagem solicita a página {refinement.page} da consulta anterior."

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action_id,
                "parameters": parameters,
            },
            "reason": reason,
        }

    def _build_date_branch_parameters(
        self,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        parameters: dict = {}
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        branch_match = re.search(r"\bfilial\s+(\d{2})\b", normalized)
        branch = branch_match.group(1) if branch_match else None
        date_range = ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        )

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"branch", "filial", "branch_code"} and branch:
                parameters[name] = branch
            elif date_range and lowered in {
                "start_date",
                "startdate",
                "data_inicio",
                "data_inicial",
                "date_start",
                "datestart",
            }:
                parameters[name] = date_range.start_date
            elif date_range and lowered in {
                "end_date",
                "enddate",
                "data_fim",
                "data_final",
                "date_end",
                "dateend",
            }:
                parameters[name] = date_range.end_date
            elif lowered in {"page"}:
                parameters[name] = 1
            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 50
            elif lowered == "granularity":
                inferred = self._infer_granularity(normalized, date_range)
                if inferred:
                    parameters[name] = inferred

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name or name in parameters:
                continue

            if name.lower() != "granularity" or not parameter.get("required"):
                continue

            parameters[name] = self._infer_granularity(normalized, date_range) or "month"

        return parameters

    @staticmethod
    def _infer_granularity(normalized: str, date_range) -> str | None:
        if any(
            term in normalized
            for term in ("diario", "diaria", "por dia", " ao dia", " diaria")
        ):
            return "day"

        if any(
            term in normalized
            for term in ("semanal", "por semana", " semana ", "semanas")
        ):
            return "week"

        if any(
            term in normalized
            for term in ("anual", "por ano", " ano ", " anos ")
        ):
            return "year"

        if any(
            term in normalized
            for term in (
                "serie",
                "series",
                "evolucao",
                "no tempo",
                "temporal",
                "mes",
                "mensal",
                "trimestre",
                "marco",
                "janeiro",
                "fevereiro",
                "abril",
                "maio",
                "junho",
                "julho",
                "agosto",
                "setembro",
                "outubro",
                "novembro",
                "dezembro",
            )
        ):
            return "month"

        if date_range:
            return "month"

        return None

    def _select_supplies_metric_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        path_token: str,
        operation_token: str,
        reason: str,
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = self._find_allowed_actions_by_path_token(
            path_token=path_token,
            operation_token=operation_token,
            allowed_action_ids=allowed_action_ids,
        )

        if not candidates:
            candidates = self._list_allowed_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()
            token = str(path_token or "").lower()
            op_token = str(operation_token or "").lower()

            if token and token not in path and op_token not in operation_id:
                continue

            parameters = self._build_date_branch_parameters(
                action,
                message,
                previous_messages=previous_messages,
            )

            if not parameters:
                parameters = self._build_supplies_stock_parameters(action)

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": reason,
            }

        return None

    def _select_supplies_stock_value_action(
        self,
        message: str,
        allowed_action_ids: list[str],
    ) -> dict | None:
        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        for action in sorted(
            candidates,
            key=lambda item: self._score_supplies_stock_action(item),
            reverse=True,
        ):
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()

            if "stock-value" not in path and "stock_value" not in str(
                action.get("operationId") or ""
            ).lower():
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": self._build_supplies_stock_parameters(action),
                },
                "reason": "A pergunta solicita indicador agregado de valor de estoque (suprimentos).",
            }

        return None

    def _score_supplies_stock_action(self, action: dict) -> int:
        haystack = " ".join(
            str(action.get(key) or "")
            for key in ["path", "summary", "description", "operationId"]
        ).lower()
        value = 0

        if "stock-value" in haystack or "get_supplies_stock_value" in haystack:
            value += 100

        if "/supplies/" in haystack:
            value += 20

        if "/products/" in haystack:
            value -= 80

        return value

    def _build_supplies_stock_parameters(self, action: dict) -> dict:
        parameters = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"top_limit", "limit"}:
                parameters[name] = 10

        return parameters

    @staticmethod
    def _looks_like_sale_orders_list_question(value: str) -> bool:
        if any(term in value for term in ("lmp", "lmps", "amostra")):
            return False

        return any(
            term in value
            for term in (
                "ordens de venda",
                "pedidos de venda",
                "lista de ov",
                "listar ov",
                "listar as ov",
                "vendas do período",
                "vendas do periodo",
            )
        )

    def _select_sale_orders_action(
        self,
        message: str,
        allowed_action_ids: list[str],
    ) -> dict | None:
        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        best = None

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if not (
                path.rstrip("/").endswith("/sales")
                or "list_sale_orders" in operation_id
            ):
                continue

            if "/lmps" in path or "lmp" in path:
                continue

            if "/products/" in path or "{code}" in path:
                continue

            best = action

            if "list_sale_orders" in operation_id or "{" not in path:
                break

        if not best:
            return None

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": best["actionId"],
                "parameters": self._build_sale_orders_parameters(best, message),
            },
            "reason": "A pergunta solicita listagem de ordens de venda.",
        }

    def _build_sale_orders_parameters(self, action: dict, message: str) -> dict:
        parameters = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"page"}:
                parameters[name] = 1
            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 50

        return self._merge_date_parameters(action, message, parameters)

    def _looks_like_transforma_question(self, value: str) -> bool:
        return "transforma" in value

    def _looks_like_lmp_question(self, value: str) -> bool:
        if self._looks_like_transforma_question(value):
            return False

        terms = [
            "lmp",
            "lmps",
            "lista de materiais",
            "lista material",
            "lista de material",
            "amostra",
            " ov ",
        ]

        if any(term in value for term in terms):
            return True

        if "ordem de venda" in value or "ordem de vendas" in value:
            return any(
                marker in value
                for marker in ("lmp", "lmps", "amostra", "engenharia")
            ) or bool(self._extract_sale_number(value))

        return False

    def _looks_like_system_metadata_question(self, value: str) -> bool:
        return any(
            term in value
            for term in (
                "tabela",
                "tabelas",
                "coluna",
                "colunas",
                "protheus",
                "sx2",
                "sx3",
                "metadado",
                "schema da tabela",
                "indices da tabela",
                "índices da tabela",
                "relacionamento da tabela",
            )
        )

    def _select_transforma_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = [
            action
            for action in self._list_allowed_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )
            if action.get("method") == "GET"
            and "transforma-mais" in str(action.get("path") or "").lower()
        ]

        if not candidates:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        wants_summary = any(
            term in normalized
            for term in ("resumo", "summary", "indicadores", "kpis")
        )

        def score(action: dict) -> int:
            path = str(action.get("path") or "").lower()
            value = 0

            if wants_summary and "/summary" in path:
                value += 100

            if not wants_summary and "/processes" in path and "/summary" not in path:
                value += 80

            if "/summary" in path and not wants_summary:
                value -= 20

            return value

        action = sorted(candidates, key=score, reverse=True)[0]

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "parameters": self._build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                ),
            },
            "reason": "A pergunta solicita dados do programa Transforma Mais.",
        }

    def _select_system_metadata_action(
        self,
        message: str,
        allowed_action_ids: list[str],
    ) -> dict | None:
        candidates = [
            action
            for action in self._list_allowed_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )
            if action.get("method") == "GET"
            and str(action.get("path") or "").lower().startswith("/system/")
        ]

        if not candidates:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        table_name = self._extract_protheus_table_name(message)
        wants_columns = "coluna" in normalized
        wants_table_search = any(
            term in normalized
            for term in ("buscar tabela", "pesquisar tabela", "qual tabela", "tabelas do")
        )

        def score(action: dict) -> int:
            path = str(action.get("path") or "").lower()
            value = 0

            if wants_columns and table_name and "/tables/" in path and "/columns" in path:
                value += 120

            if wants_columns and not table_name and "/columns/search" in path:
                value += 110

            if wants_table_search and "/tables/search" in path:
                value += 110

            if table_name and path.endswith(f"/tables/{table_name.lower()}"):
                value += 90

            if wants_columns and "/columns/search" in path and table_name:
                value -= 30

            return value

        ranked = sorted(candidates, key=score, reverse=True)

        if ranked[0] and score(ranked[0]) <= 0:
            return None

        action = ranked[0]
        parameters = self._build_system_parameters(message, action)

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "parameters": parameters,
            },
            "reason": "A pergunta solicita metadados de tabelas/colunas do Protheus.",
        }

    def _extract_protheus_table_name(self, text: str | None) -> str | None:
        raw = str(text or "")
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        table_match = re.search(
            r"\btabela\s+([a-z]{2,4}\d{0,4})\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if table_match:
            return table_match.group(1).upper()

        inline_match = re.search(
            r"\bcolunas?\s+(?:da|de)\s+([a-z]{2,4}\d{0,4})\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if inline_match:
            return inline_match.group(1).upper()

        return None

    def _build_system_parameters(self, message: str, action: dict) -> dict:
        parameters: dict = {}
        path = str(action.get("path") or "")
        table_name = self._extract_protheus_table_name(message)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"tablename", "table_name", "table"} and table_name:
                parameters[name] = table_name
            elif lowered in {"page"}:
                parameters[name] = 1
            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 50
            elif lowered == "description":
                query_match = re.search(
                    r"(?:buscar|pesquisar|procurar)\s+(?:tabela|coluna)s?\s+(.+)$",
                    normalized,
                )

                if query_match:
                    parameters[name] = query_match.group(1).strip()[:120]

        if table_name and "{tableName}" in path and not parameters:
            parameters["tableName"] = table_name

        return parameters

    def _looks_like_product_search(self, value: str) -> bool:
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(value):
            return False

        if ChatSqlOperationalIntentService.requires_sql_knowledge(value):
            return False

        audit5s_terms = (
            "nc 5s",
            "nao conformidade 5s",
            "não conformidade 5s",
            "auditoria 5s",
            "auditorias 5s",
            "audit 5s",
            "candidatas a nc 5s",
        )

        if any(term in value for term in audit5s_terms):
            return False

        search_triggers = (
            "busque", "buscar", "pesquise", "pesquisar",
            "procure", "procurar", "encontre", "encontrar",
            "traga", "liste", "listar", "exemplos de",
            "existe algum", "existem", "tem algum",
            "quais produtos", "quais itens", "quais materiais",
            "mais informações sobre", "mais informacoes sobre",
            "informações sobre", "informacoes sobre",
            "detalhe de", "detalhes sobre",
            "search", "find",
        )
        product_context = (
            "produto", "item", "material", "cabo", "parafuso",
            "chapa", "tubo", "peça", "peca", "insumo", "mp",
            "componente", "motor", "válvula", "valvula",
            "rolamento", "filtro", "conector", "anel",
        )

        has_trigger = any(term in value for term in search_triggers)
        has_product_context = any(term in value for term in product_context)

        if has_trigger and has_product_context:
            return True

        if has_trigger and len(value.split()) >= 3:
            if not any(
                term in value
                for term in ("lmp", "ov", "cpv", "otd", "sql", "estoque total", "giro")
            ):
                return True

        return False

    def _extract_search_description(self, message: str) -> str:
        normalized = str(message or "").lower().strip()

        patterns = [
            r"(?:mais\s+)?informa(?:ç|c)(?:õ|o)es\s+sobre\s+(.+?)$",
            r"detalhes?\s+(?:sobre\s+)?(.+?)$",
            r"detalhe\s+de\s+(.+?)$",
            r"(?:busque|pesquise|procure|encontre|traga|liste)\s+(?:\d+\s+)?(?:exemplos?\s+de\s+)(.+?)(?:\s+na\s+api|\s+no\s+sistema)?$",
            r"(?:busque|pesquise|procure|encontre|traga|liste)\s+(?:\d+\s+)?(?:produtos?|itens?|materiais?)\s+(?:d[eoa]\s+(?:tipo\s+)?|com\s+(?:descri[çc][ãa]o\s+)?|tipo\s+)(.+?)(?:\s+na\s+api|\s+no\s+sistema)?$",
            r"(?:busque|pesquise|procure|encontre|traga|liste)\s+(?:\d+\s+)?(.+?)(?:\s+na\s+api|\s+no\s+sistema)?$",
            r"(?:quais|quantos?)\s+(?:produtos?|itens?|materiais?)\s+(?:existem?|tem|há)\s+(?:com\s+(?:descri[çc][ãa]o\s+)?|d[eoa]\s+(?:tipo\s+)?|tipo\s+)(.+?)$",
            r"(?:quais|quantos?)\s+(?:produtos?|itens?|materiais?)\s+(.+?)$",
            r"(?:existe|tem)\s+(?:algum|alguma)\s+(.+?)(?:\s+no\s+sistema|\s+cadastrado)?$",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                result = match.group(1).strip()
                result = re.sub(
                    r"^(produtos?|itens?|materiais?|exemplos?|tipo|com|de)\s+",
                    "",
                    result,
                )
                if result:
                    return result

        stop_words = {
            "busque", "buscar", "pesquise", "pesquisar", "procure", "procurar",
            "encontre", "encontrar", "traga", "liste", "listar", "exemplos",
            "de", "produtos", "produto", "itens", "item", "materiais", "material",
            "me", "para", "mim", "os", "as", "o", "a", "um", "uma", "no", "na",
            "do", "da", "com", "que", "são", "sao", "tipo", "descrição", "descricao",
        }

        words = normalized.split()
        description_words = []

        for word in words:
            cleaned = word.strip(",.!?;:")
            if cleaned.isdigit() and len(cleaned) <= 2:
                continue
            if cleaned not in stop_words:
                description_words.append(cleaned)

        return " ".join(description_words[-4:]) if description_words else normalized

    def _select_product_search_action(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        description_override: str | None = None,
    ) -> dict | None:
        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if "search" not in path and "search" not in operation_id:
                continue

            group_code = self._extract_search_group_code(message, normalized)
            description_query = description_override or self._extract_search_description(message)
            product_code_query = ChatProductQueryIntentService.extract_product_code(message)
            page_size = self._extract_search_limit(normalized)

            parameters = {}
            for parameter in action.get("parametersSchema") or []:
                name = parameter.get("name")
                if not name:
                    continue
                lowered = name.lower()
                if lowered in {"group_code", "groupcode", "grupo"} and group_code:
                    parameters[name] = group_code
                elif lowered == "code" and product_code_query and not group_code:
                    parameters[name] = product_code_query
                elif lowered in {"description", "descricao", "query", "q", "search", "term"}:
                    if description_query and not group_code:
                        parameters[name] = description_query
                elif lowered == "page":
                    parameters[name] = 1
                elif lowered in {"page_size", "pagesize", "limit"}:
                    parameters[name] = page_size

            if group_code and "group_code" not in parameters and "groupCode" not in parameters:
                parameters["group_code"] = group_code

            if not parameters:
                if group_code:
                    parameters = {"group_code": group_code, "page": 1, "page_size": page_size}
                else:
                    parameters = {"description": description_query, "page_size": page_size}

            reason = (
                f"Busca de produtos pelo grupo '{group_code}'."
                if group_code
                else f"Busca de produtos por descrição: '{description_query}'."
            )

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": reason,
            }

        return None

    def _extract_search_group_code(self, message: str, normalized: str) -> str | None:
        patterns = (
            r"\bgrupo\s+de\s+produtos?\s+([A-Za-z0-9]{1,12})\b",
            r"\bgrupo\s+([A-Za-z0-9]{1,12})\b",
            r"\bgroup_code\s+([A-Za-z0-9]{1,12})\b",
            r"\bdo\s+grupo\s+([A-Za-z0-9]{1,12})\b",
            r"\bpelo\s+grupo\s+([A-Za-z0-9]{1,12})\b",
        )

        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)

            if match:
                code = str(match.group(1)).strip().upper()

                if code.lower() in {"de", "do", "da", "produto", "produtos"}:
                    continue

                return code

        return None

    def _extract_search_limit(self, value: str) -> int:
        match = re.search(r"\b(\d{1,2})\s+(?:exemplos?|produtos?|itens?|resultados?)", value)
        if match:
            return min(int(match.group(1)), 20)

        match = re.search(r"(?:exemplos?|produtos?|itens?|resultados?)\s+(\d{1,2})\b", value)
        if match:
            return min(int(match.group(1)), 20)

        return 5

    def _looks_like_sql_or_data_query(self, message: str) -> bool:
        normalized = str(message or "").lower()

        return any(
            term in normalized
            for term in [
                "sql",
                "consulta sql",
                "consulta no banco",
                "rodar sql",
                "executar sql",
                "execute o sql",
                "execute essa consulta",
                "data/sql",
                "query",
                "select ",
            ]
        )

    def _extract_sql_query(self, message: str) -> str | None:
        raw = str(message or "").strip()

        quoted = re.search(r'["“](.+?)["”]', raw, flags=re.S)
        if quoted:
            return quoted.group(1).strip()

        marker = re.search(r"sql\s*:\s*(.+)$", raw, flags=re.I | re.S)
        if marker:
            return marker.group(1).strip().strip('"').strip("'")

        select_match = re.search(r"(select\s+.+)$", raw, flags=re.I | re.S)
        if select_match:
            return select_match.group(1).strip().strip('"').strip("'")

        return None

    def _select_sql_or_data_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        sql: str | None = None,
    ) -> dict | None:
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        if ChatSqlSafetyService.contains_destructive_sql(sql) or ChatSqlSafetyService.contains_destructive_sql(
            message
        ):
            return None

        if not allowed_action_ids:
            return None

        allowed = {str(item) for item in allowed_action_ids}

        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=120,
        )

        if (sql or "").strip():
            action = self._resolve_data_sql_action(allowed_action_ids)
        else:
            preferred = [
                action
                for action in candidates
                if any(
                    term
                    in " ".join(
                        [
                            str(action.get("path") or ""),
                            str(action.get("summary") or ""),
                            str(action.get("description") or ""),
                            str(action.get("operationId") or ""),
                        ]
                    ).lower()
                    for term in ["sql", "data", "query"]
                )
            ]

            ranked = self._rank_candidates(
                message,
                preferred or candidates,
                allowed_action_ids=allowed_action_ids,
            )
            action = ranked[0] if ranked else None

        if not action:
            return None

        sql_query = (sql or "").strip() or self._extract_sql_query(message)
        body = (
            ExternalActionSqlCapabilityService.build_sql_request_body(sql_query)
            if sql_query
            else {"message": message}
        )

        reason = (
            ExternalActionResponseContentService.get(
                "selectionReasons",
                "productionSqlFastPath",
            )
            if sql
            else ExternalActionResponseContentService.get(
                "selectionReasons",
                "genericSql",
            )
        )

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "body": body,
            },
            "reason": reason,
        }

    def _select_generic_allowed_action(
        self,
        message: str,
        allowed_action_ids: list[str],
    ) -> dict | None:
        if not allowed_action_ids:
            return None

        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=120,
        )

        if not candidates:
            return None

        ranked = self._rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed_action_ids,
        )

        if not ranked:
            return None

        action = ranked[0]

        if action.get("selectionScore") is None:
            return None

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "body": {
                    "message": message,
                },
            },
            "reason": action.get("selectionReason")
            or "Action OpenAPI autorizada selecionada por similaridade semântica com a pergunta.",
        }

    def _select_product_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
    ) -> dict | None:
        candidates = []

        if allowed_action_ids:
            candidates = self._list_allowed_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )

        if not candidates:
            candidates = self.repository.find_candidate_actions(
                message,
                limit=80,
            )

        if not candidates:
            return None

        candidates = [
            action
            for action in candidates
            if action.get("method") == "GET"
        ] or candidates

        ranked = self._rank_product_actions(
            candidates,
            intent=intent,
            message=message,
            route_segment=route_segment,
        )

        if preferred_action_id:
            preferred = next(
                (
                    action
                    for action in ranked
                    if str(action.get("actionId") or "") == preferred_action_id
                ),
                None,
            )

            if preferred:
                ranked = [preferred, *[
                    action
                    for action in ranked
                    if str(action.get("actionId") or "") != preferred_action_id
                ]]

        for action in ranked:
            parameters = self._build_product_parameters(
                action,
                product_code,
                message=message,
            )

            if parameters:
                reason = "A pergunta solicita informações operacionais de produto via OpenAPI."

                if branch_code := (
                    ChatOperationalRefinementService.extract_branch_code(
                        ChatMessageNormalizationService.normalize_for_matching(message)
                    )
                ):
                    reason = (
                        f"A mensagem refina o estoque do produto {product_code} "
                        f"para a filial {branch_code}."
                    )

                return {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": action["actionId"],
                        "parameters": parameters,
                    },
                    "reason": reason,
                }

        return None

    def _select_lmp_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
    ) -> dict | None:
        if not allowed_action_ids:
            return None

        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        getters = [action for action in candidates if action.get("method") == "GET"]

        if not getters:
            return None

        ranked = self._rank_lmp_actions(message, getters)
        action = ranked[0]
        parameters = self._build_lmp_parameters(
            message,
            action,
            conversation_context=conversation_context,
        )

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "parameters": parameters,
            },
            "reason": "A pergunta solicita consulta de LMP via OpenAPI.",
        }

    def _extract_sale_number(self, text: str | None) -> str | None:
        raw = str(text or "")

        patterns = [
            r"\bov\s*[#:\-]?\s*(\d{4,})\b",
            r"\bordem\s+de\s+venda\s*[#:\-]?\s*(\d{4,})\b",
            r"\blmp\s+(\d{4,})\b",
            r"\bamostra\s+(\d{4,})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, raw, flags=re.IGNORECASE)

            if match:
                return match.group(1)

        return None

    def _rank_lmp_actions(self, message: str, candidates: list[dict]) -> list[dict]:
        normalized = str(message or "").lower()
        sale_number = self._extract_sale_number(message)
        wants_dashboard = any(
            term in normalized
            for term in ("dashboard", "painel", "resumo gerencial", "visão gerencial")
        )
        wants_dashboard_summary = any(
            term in normalized
            for term in (
                "kpis do painel",
                "resumo do painel",
                "resumo do dashboard",
                "indicadores do painel",
                "dashboard/summary",
            )
        )
        wants_dashboard_items = any(
            term in normalized
            for term in ("itens do dashboard", "itens do painel", "lista do painel")
        )
        wants_dashboard_charts = any(
            term in normalized
            for term in ("grafico", "gráfico", "graficos", "gráficos", "charts")
        )
        wants_list = any(
            term in normalized
            for term in ("listar", "liste", "lista de", "quais lmps", "todas as lmp")
        )

        def score(action: dict) -> int:
            path = str(action.get("path") or "").lower()
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ["actionId", "operationId", "path", "summary", "description"]
            ).lower()
            value = 0

            if sale_number and "{sale_number}" in path:
                value += 120

            if wants_dashboard_summary and "/dashboard/summary" in path:
                value += 115

            if wants_dashboard_items and "/dashboard/items" in path:
                value += 115

            if wants_dashboard_charts and "/dashboard/charts" in path:
                value += 115

            if wants_dashboard and "dashboard" in path and not any(
                segment in path for segment in ("/summary", "/items", "/charts")
            ):
                value += 100

            if wants_list and path.endswith("/lmps") and "dashboard" not in path and "{" not in path:
                value += 90

            operation_id = str(action.get("operationId") or "").lower()

            if operation_id == "list_lmps":
                value += 40

            if "/lmps" in path and "lmp" in haystack:
                value += 25

            if "transforma" in path:
                value -= 50

            return value

        return sorted(candidates, key=score, reverse=True)

    def _build_lmp_parameters(
        self,
        message: str,
        action: dict,
        *,
        conversation_context: str | None = None,
    ) -> dict:
        path = str(action.get("path") or "")
        sale_number = self._extract_sale_number(message) or self._extract_sale_number(
            conversation_context
        )

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
                parameters[name] = 50
            elif lowered == "status" and "/dashboard" in path:
                parameters[name] = "Todos"

        if not parameters:
            parameters = {"page": 1, "page_size": 50}

        return self._merge_date_parameters(action, message, parameters)

    def _merge_date_parameters(
        self,
        action: dict,
        message: str,
        parameters: dict,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        date_range = ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        )

        if not date_range:
            return parameters

        merged = dict(parameters)

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if date_range and lowered in {
                "start_date",
                "startdate",
                "data_inicio",
                "data_inicial",
                "date_start",
                "datestart",
            }:
                merged[name] = date_range.start_date
            elif date_range and lowered in {
                "end_date",
                "enddate",
                "data_fim",
                "data_final",
                "date_end",
                "dateend",
            }:
                merged[name] = date_range.end_date

        return merged

    def _rank_product_actions(
        self,
        candidates: list[dict],
        *,
        intent: str = ChatProductQueryIntent.FULL,
        message: str | None = None,
        route_segment: str | None = None,
    ) -> list[dict]:
        normalized = str(message or "").lower()
        inherited_segment = str(route_segment or "").strip().lower()
        wants_purchases = any(
            term in normalized
            for term in (
                "compra",
                "compras",
                "ultimas compras",
                "últimas compras",
                "ultima compra",
                "última compra",
                "fornecedor comprou",
                "histórico de compra",
                "historico de compra",
            )
        )
        wants_billing = any(
            term in normalized for term in ("faturamento", "billing", "faturado")
        )
        wants_sales = any(
            term in normalized
            for term in (
                "venda",
                "vendas",
                "carteira",
                "pedidos em aberto",
                "pedido em aberto",
            )
        ) or (
            "faturamento" in normalized
            and not wants_billing
        )
        wants_product_summary = any(
            term in normalized
            for term in (
                "resumo do produto",
                "resumo sintetico",
                "resumo sintético",
                "visao resumida",
                "visão resumida",
            )
        ) or (
            "resumo" in normalized
            and "completo" not in normalized
            and "ficha" not in normalized
            and "kaizen" not in normalized
        )
        wants_full_analyser = any(
            term in normalized
            for term in (
                "ficha completa",
                "analisador",
                "analyzer",
                "analise completa",
                "análise completa",
                "informacoes completas",
                "informações completas",
                "tudo sobre o produto",
            )
        )
        wants_open_orders = any(
            term in normalized
            for term in ("carteira", "pedidos em aberto", "pedido em aberto", "open-orders")
        )
        wants_structure = any(
            term in normalized
            for term in ("estrutura", "bom", "bill of material", "composição", "composicao")
        )

        wants_guide = any(
            term in normalized
            for term in ("roteiro", "guide", "rota de fabricação", "rota de fabricacao")
        )
        wants_suppliers = any(
            term in normalized
            for term in ("fornecedor", "fornecedore", "supplier")
        )
        wants_pricing = any(
            term in normalized
            for term in ("preço", "preco", "pricing", "tabela de preço", "tabela de preco", "quanto custa", "custo do")
        )
        wants_customers = any(
            term in normalized
            for term in ("cliente", "customer")
        )
        wants_parents = any(
            term in normalized
            for term in (
                "produto pai", "produtos pai", "parent", "where used",
                "onde é usado", "onde e usado", "pai do", "pais do",
                "quais produtos usam", "quais itens usam", "produtos que usam",
            )
        )
        wants_movements = any(
            term in normalized
            for term in ("movimentaç", "movimentac", "internal-movement")
        )
        wants_invoices = any(
            term in normalized
            for term in (
                "nota fiscal", "notas fiscai", "nfe", "invoice",
                "nota de entrada", "notas de entrada", "nota de saída", "nota de saida",
                "notas de saída", "notas de saida",
            )
        )
        wants_inbound = any(
            term in normalized for term in ("entrada", "inbound", "recebimento")
        )
        wants_outbound = any(
            term in normalized for term in ("saída", "saida", "outbound", "expedição", "expedicao")
        )
        wants_inspection = any(
            term in normalized
            for term in ("inspeção", "inspecao", "inspection", "qualidade")
        )

        if inherited_segment == "purchases":
            wants_purchases = True
        elif inherited_segment == "suppliers":
            wants_suppliers = True
        elif inherited_segment == "sales":
            wants_sales = True
        elif inherited_segment == "pricing":
            wants_pricing = True
        elif inherited_segment == "guide":
            wants_guide = True
        elif inherited_segment == "customers":
            wants_customers = True
        elif inherited_segment == "internal-movements":
            wants_movements = True
        elif inherited_segment == "inspection":
            wants_inspection = True
        elif inherited_segment == "inbound-invoice":
            wants_invoices = True
            wants_inbound = True
        elif inherited_segment == "outbound-invoice":
            wants_invoices = True
            wants_outbound = True

        has_specific_sub_intent = (
            wants_purchases or wants_sales or wants_open_orders or wants_structure
            or wants_guide or wants_suppliers or wants_pricing or wants_customers
            or wants_parents or wants_movements or wants_invoices or wants_inspection
            or wants_billing or wants_product_summary or wants_full_analyser
        )

        def score(action: dict) -> int:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ["actionId", "operationId", "path", "summary", "description"]
            ).lower()
            path = str(action.get("path") or "").lower()

            value = 0

            if wants_purchases and "/purchases" in path:
                value += 110

            if wants_billing and "/sales/billing" in path:
                value += 125

            if wants_open_orders and "open-orders" in path:
                value += 115

            elif wants_sales and "/sales" in path and "open-orders" not in path and "billing" not in path:
                value += 100

            if wants_product_summary and "/summary" in path:
                value += 125

            if wants_full_analyser and "analyser" in path:
                value += 125

            if wants_product_summary and "analyser" in haystack:
                value -= 55

            if wants_full_analyser and "/summary" in path:
                value -= 45

            if wants_structure and "/structure" in path:
                value += 120

            if wants_guide and "/guide" in path:
                value += 120

            if wants_suppliers and "/suppliers" in path:
                value += 120

            if wants_pricing and "/pricing" in path:
                value += 120

            if wants_customers and "/customers" in path:
                value += 120

            if wants_parents and "/parents" in path:
                value += 120

            if wants_movements and "/internal-movements" in path:
                value += 120

            if wants_invoices:
                if wants_outbound and "/outbound-invoice" in path:
                    value += 130
                elif wants_inbound and "/inbound-invoice" in path:
                    value += 130
                elif "/inbound-invoice" in path or "/outbound-invoice" in path:
                    value += 120

            if wants_inspection and "/inspection" in path:
                value += 120

            if intent == ChatProductQueryIntent.STRUCTURE:
                if "/structure" in path:
                    value += 150

                if "structure" in haystack or "estrutura" in haystack or "bom" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

                if "search" in path:
                    value -= 80

            elif intent == ChatProductQueryIntent.STOCK:
                if "/products/{code}/stock" in haystack or path.endswith("/stock"):
                    value += 120

                if "stock" in haystack or "estoque" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

            elif intent == ChatProductQueryIntent.PARENTS:
                if "/parents" in path:
                    value += 200

                if "parent" in haystack or "pai" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

                if "search" in path:
                    value -= 80

            elif intent == ChatProductQueryIntent.SUMMARY:
                if "/products/{code}/summary" in path or path.endswith("/summary"):
                    value += 260

                if "summary" in haystack and "product" in haystack:
                    value += 40

                if "analyser" in haystack or "analyzer" in haystack:
                    value -= 120

                if path == "/products/{code}":
                    value += 30

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 90

                if "search" in path:
                    value -= 100

            elif intent == ChatProductQueryIntent.ANALYSER:
                if "/products/{code}/analyser" in haystack or path.endswith("/analyser"):
                    value += 280

                if "analyser" in haystack or "analyzer" in haystack:
                    value += 60

                if "/summary" in path:
                    value -= 100

                if path == "/products/{code}":
                    value += 40

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 90

                if "search" in path:
                    value -= 100

            elif intent == ChatProductQueryIntent.DESCRIPTION:
                if path == "/products/{code}":
                    value += 200

                if wants_product_summary and "/summary" in path:
                    value += 80

                if wants_full_analyser and "/products/{code}/analyser" in haystack:
                    value += 180
                elif not wants_product_summary and "/products/{code}/analyser" in haystack:
                    value += 120

                if "/description" in path:
                    value += 150

                if wants_product_summary and "analyser" in haystack:
                    value -= 80

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 80

                if "search" in path:
                    value -= 100

            else:
                if not has_specific_sub_intent:
                    if "/products/{code}/analyser" in haystack:
                        value += 100

                    if "analyser" in haystack or "analyzer" in haystack:
                        value += 60

                if "/products/{code}" in haystack:
                    value += 25

            if "product" in haystack or "products" in haystack or "produto" in haystack:
                value += 20

            if "search" in haystack or "buscar" in haystack or "busca" in haystack:
                value += 8

            if intent != ChatProductQueryIntent.STOCK and (
                "stock" in haystack or "estoque" in haystack
            ):
                value += 6

            if "structure" in haystack or "estrutura" in haystack:
                value += 5

            value += self._provider_preference_bonus(action)

            return value

        return sorted(candidates, key=score, reverse=True)

    @classmethod
    def _provider_preference_bonus(cls, action: dict) -> int:
        from app.infrastructure.config.settings import Settings

        if not Settings.CHAT_PREFER_API_EXTERNA_PROVIDER:
            return 0

        action_id = str(action.get("actionId") or "").lower()

        if action_id.startswith("api_externa."):
            return 95

        if action_id.startswith("api_delpi."):
            return -120

        return 0

    @classmethod
    def _clamp_max_depth_for_path(cls, value: int, path: str) -> int:
        try:
            depth = int(value)
        except (TypeError, ValueError):
            depth = 10

        lowered = str(path or "").lower()
        cap = (
            cls.HIERARCHICAL_PRODUCT_MAX_DEPTH
            if "/structure" in lowered or "/parents" in lowered
            else 99
        )

        return min(max(depth, 1), cap)

    def _build_product_parameters(self, action: dict, code: str, *, message: str | None = None) -> dict:
        parameters = {}
        path = (action.get("path") or "").lower()
        is_full_listing = "/structure" in path or "/parents" in path
        normalized = (
            ChatMessageNormalizationService.normalize_for_matching(message)
            if message
            else ""
        )

        branch_code = (
            ChatOperationalRefinementService.extract_branch_code(normalized)
            if normalized
            else None
        )
        warehouse_code = (
            ChatOperationalRefinementService.extract_warehouse_code(normalized)
            if normalized
            else None
        )
        requested_page_size = (
            ChatOperationalRefinementService.extract_requested_page_size(normalized)
            if normalized
            else None
        )
        requested_page = (
            ChatOperationalRefinementService.extract_requested_page(normalized)
            if normalized
            else None
        )

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {
                "code",
                "product_code",
                "productcode",
                "codigo",
                "cod_produto",
                "produto",
                "item",
                "id",
            }:
                parameters[name] = code

            elif lowered in {
                "query",
                "q",
                "search",
                "description",
                "descricao",
                "term",
            }:
                parameters[name] = code

            elif lowered == "page":
                parameters[name] = requested_page or 1

            elif lowered in {"page_size", "pagesize", "limit"}:
                if requested_page_size is not None:
                    parameters[name] = requested_page_size
                else:
                    parameters[name] = 200 if is_full_listing else 50

            elif lowered in {"max_depth", "maxdepth", "depth", "nivel", "levels"}:
                parameters[name] = (
                    self.HIERARCHICAL_PRODUCT_MAX_DEPTH
                    if is_full_listing
                    else min(10, self.HIERARCHICAL_PRODUCT_MAX_DEPTH)
                )

            elif lowered in {"branch", "filial", "branch_code", "branchcode"} and branch_code:
                parameters[name] = branch_code

            elif lowered in {
                "warehouse",
                "armazem",
                "armazém",
                "warehouse_code",
                "deposito",
                "depósito",
                "location",
                "local",
            } and warehouse_code:
                parameters[name] = warehouse_code

        return parameters

    def _resolve_previous_external_action_id(
        self,
        previous_messages: list | None,
        *,
        path_fragment: str,
    ) -> str | None:
        fragment = str(path_fragment or "").strip().lower()

        if not fragment:
            return None

        for item in reversed((previous_messages or [])[-14:]):
            metadata = item.get("metadata") if isinstance(item, dict) else getattr(item, "metadata", None)

            if not isinstance(metadata, dict):
                continue

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()

                if fragment not in path:
                    continue

                action_id = tool_meta.get("actionId")

                if action_id:
                    return str(action_id)

        return None

    def _extract_numeric_code(self, message: str) -> str | None:
        return ChatProductQueryIntentService.extract_product_code(message)

    def _resolve_data_sql_action(self, allowed_action_ids: list[str]) -> dict | None:
        actions: list[dict] = []
        seen: set[str] = set()

        list_actions = getattr(self.repository, "list_actions", None)
        if callable(list_actions):
            for action in list_actions():
                action_id = str(action.get("actionId") or "")
                if action_id and action_id not in seen:
                    seen.add(action_id)
                    actions.append(action)

        for action in self.repository.find_candidate_actions(
            "sql execute readonly query data",
            limit=120,
            allowed_action_ids=list(allowed_action_ids),
        ):
            action_id = str(action.get("actionId") or "")
            if action_id and action_id not in seen:
                seen.add(action_id)
                actions.append(action)

        return ExternalActionSqlCapabilityService.pick_sql_execution_action(
            actions,
            allowed_action_ids=allowed_action_ids,
        )

    def _list_allowed_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        limit: int,
    ) -> list[dict]:
        allowed = {str(item) for item in allowed_action_ids}

        return [
            action
            for action in self.repository.find_candidate_actions(
                message,
                limit=limit,
                allowed_action_ids=allowed_action_ids,
            )
            if str(action.get("actionId")) in allowed
        ]

    def _find_allowed_actions_by_path_token(
        self,
        *,
        path_token: str,
        operation_token: str,
        allowed_action_ids: list[str],
        method: str = "GET",
    ) -> list[dict]:
        token = str(path_token or "").lower().strip()
        op_token = str(operation_token or "").lower().strip()
        allowed = {str(item) for item in allowed_action_ids}

        if not allowed or (not token and not op_token):
            return []

        matches: list[dict] = []
        list_actions = getattr(self.repository, "list_actions", None)

        if not callable(list_actions):
            return []

        for action in list_actions():
            if str(action.get("actionId")) not in allowed:
                continue

            if str(action.get("method") or "").upper() != method.upper():
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if token and token in path:
                matches.append(action)
                continue

            if op_token and op_token in operation_id:
                matches.append(action)
                continue

            if token and token.replace("-", "_") in operation_id:
                matches.append(action)

        return matches

    def _rank_candidates(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        if not candidates:
            return []

        if self.semantic_ranker:
            return self.semantic_ranker.rank(
                message,
                candidates,
                allowed_action_ids=allowed_action_ids,
            )

        return candidates
