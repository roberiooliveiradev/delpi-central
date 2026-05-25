import re

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class ExternalActionSelectionService:
    def __init__(self, repository, semantic_ranker=None):
        self.repository = repository
        self.semantic_ranker = semantic_ranker

    def select_action(
        self,
        message: str,
        allowed_action_ids: list[str] | None = None,
        conversation_context: str | None = None,
    ) -> dict | None:
        allowed_action_ids = allowed_action_ids or []
        normalized = str(message or "").lower()
        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
        )

        if self._looks_like_sale_orders_list_question(normalized):
            selected = self._select_sale_orders_action(
                message,
                allowed_action_ids=allowed_action_ids,
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

        if self._looks_like_cpv_question(normalized) and not product_code:
            selected = self._select_supplies_metric_action(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="cpv",
                operation_token="cpv",
                reason="A pergunta solicita o indicador CPV de suprimentos.",
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

        if product_code and ChatProductQueryIntentService.detect(message) == ChatProductQueryIntent.STOCK:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STOCK,
            )

            if selected:
                return selected

        if product_code and ChatProductQueryIntentService.detect(message) == ChatProductQueryIntent.DESCRIPTION:
            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.DESCRIPTION,
            )

            if selected:
                return selected

        if product_code and self._looks_like_product_question(normalized):
            return self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.FULL,
            )

        if self._looks_like_sql_or_data_query(message):
            return self._select_sql_or_data_action(
                message,
                allowed_action_ids=allowed_action_ids,
            )

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

    def _select_supplies_metric_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        path_token: str,
        operation_token: str,
        reason: str,
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

            if path_token not in path and operation_token not in operation_id:
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": self._build_supplies_stock_parameters(action),
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

    def _looks_like_sale_orders_list_question(self, value: str) -> bool:
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

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if not (
                path.rstrip("/").endswith("/sales")
                or path.rstrip("/").endswith("/sales/")
                or "list_sale_orders" in operation_id
            ):
                continue

            if "/lmps" in path or "lmp" in path:
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": self._build_sale_orders_parameters(action),
                },
                "reason": "A pergunta solicita listagem de ordens de venda.",
            }

        return None

    def _build_sale_orders_parameters(self, action: dict) -> dict:
        parameters = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"page"}:
                parameters[name] = 1
            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 20

        return parameters

    def _looks_like_lmp_question(self, value: str) -> bool:
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

    def _looks_like_sql_or_data_query(self, message: str) -> bool:
        normalized = str(message or "").lower()

        return any(
            term in normalized
            for term in [
                "sql",
                "consulta sql",
                "rodar sql",
                "executar sql",
                "execute o sql",
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
    ) -> dict | None:
        if not allowed_action_ids:
            return None

        allowed = {str(item) for item in allowed_action_ids}

        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=120,
        )

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

        sql_query = self._extract_sql_query(message)
        body = {
            "query": sql_query,
            "sql": sql_query,
            "statement": sql_query,
        } if sql_query else {"message": message}

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "body": body,
            },
            "reason": "A pergunta solicita execução de consulta SQL via action OpenAPI autorizada do agente.",
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
    ) -> dict | None:
        if not allowed_action_ids:
            return None

        allowed = {str(item) for item in allowed_action_ids}

        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        if not candidates:
            return None

        candidates = [
            action
            for action in candidates
            if action.get("method") == "GET"
        ] or candidates

        for action in self._rank_product_actions(
            candidates,
            intent=intent,
            message=message,
        ):
            parameters = self._build_product_parameters(action, product_code)

            if parameters:
                return {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": action["actionId"],
                        "parameters": parameters,
                    },
                    "reason": "A pergunta solicita informações operacionais de produto via OpenAPI.",
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

            if wants_dashboard and "dashboard" in path:
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
                parameters[name] = 5
            elif lowered == "status" and "/dashboard" in path:
                parameters[name] = "Todos"

        if not parameters:
            parameters = {"page": 1, "page_size": 5}

        return parameters

    def _rank_product_actions(
        self,
        candidates: list[dict],
        *,
        intent: str = ChatProductQueryIntent.FULL,
        message: str | None = None,
    ) -> list[dict]:
        normalized = str(message or "").lower()
        wants_purchases = any(
            term in normalized
            for term in ("compra", "compras", "fornecedor comprou", "histórico de compra", "historico de compra")
        )
        wants_sales = any(
            term in normalized
            for term in (
                "venda",
                "vendas",
                "faturamento",
                "carteira",
                "pedidos em aberto",
                "pedido em aberto",
            )
        )
        wants_open_orders = any(
            term in normalized
            for term in ("carteira", "pedidos em aberto", "pedido em aberto", "open-orders")
        )

        has_specific_sub_intent = wants_purchases or wants_sales or wants_open_orders

        def score(action: dict) -> int:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ["actionId", "operationId", "path", "summary", "description"]
            ).lower()
            path = str(action.get("path") or "").lower()

            value = 0

            if wants_purchases and "/purchases" in path:
                value += 110

            if wants_open_orders and "open-orders" in path:
                value += 115

            elif wants_sales and "/sales" in path and "open-orders" not in path:
                value += 100

            if intent == ChatProductQueryIntent.STOCK:
                if "/products/{code}/stock" in haystack or path.endswith("/stock"):
                    value += 120

                if "stock" in haystack or "estoque" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

            elif intent == ChatProductQueryIntent.DESCRIPTION:
                if "analyser" in haystack or "analyzer" in haystack:
                    value += 70

                if "/products/{code}" in haystack and "stock" not in haystack:
                    value += 20

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

            return value

        return sorted(candidates, key=score, reverse=True)

    def _build_product_parameters(self, action: dict, code: str) -> dict:
        parameters = {}

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
                parameters[name] = 1

            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 5

        return parameters

    def _extract_numeric_code(self, message: str) -> str | None:
        return ChatProductQueryIntentService.extract_product_code(message)

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
