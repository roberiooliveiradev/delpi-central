import re


class ExternalActionSelectionService:
    def __init__(self, repository, semantic_ranker=None):
        self.repository = repository
        self.semantic_ranker = semantic_ranker

    def select_action(
        self,
        message: str,
        allowed_action_ids: list[str] | None = None,
    ) -> dict | None:
        allowed_action_ids = allowed_action_ids or []
        normalized = str(message or "").lower()
        product_code = self._extract_numeric_code(message)

        if product_code and self._looks_like_product_question(normalized):
            return self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
            )

        if self._looks_like_lmp_question(normalized):
            return self._select_lmp_action(
                message,
                allowed_action_ids=allowed_action_ids,
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
            "informações do produto",
            "informacoes do produto",
            "dados do produto",
            "busque as informações do produto",
            "busque informacoes do produto",
            "api delpi",
        ]

        return any(term in value for term in terms)

    def _looks_like_lmp_question(self, value: str) -> bool:
        return "lmp" in value or "lmps" in value

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

        for action in self._rank_product_actions(candidates):
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
    ) -> dict | None:
        if not allowed_action_ids:
            return None

        allowed = {str(item) for item in allowed_action_ids}

        candidates = self._list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        for action in candidates:
            if action.get("method") != "GET":
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": {
                        "page": 1,
                        "page_size": 5,
                    },
                },
                "reason": "A pergunta solicita consulta de LMP via OpenAPI.",
            }

        return None

    def _rank_product_actions(self, candidates: list[dict]) -> list[dict]:
        def score(action: dict) -> int:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ["actionId", "operationId", "path", "summary", "description"]
            ).lower()

            value = 0

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

            if "stock" in haystack or "estoque" in haystack:
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
        match = re.search(r"\b\d{4,}\b", message or "")

        if not match:
            return None

        return match.group(0)

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
