"""Seleção de busca de produtos por grupo ou descrição — Fase 3B lote 19."""

from __future__ import annotations

import re
from typing import Callable

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductSearchRouteSelectionService:
    @staticmethod
    def looks_like_product_search(value: str) -> bool:
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatSqlIntentService.is_sql_conversation_turn(value):
            return False

        if ChatWebSearchIntentService.matches(value):
            return False

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
            "busque",
            "buscar",
            "pesquise",
            "pesquisar",
            "procure",
            "procurar",
            "encontre",
            "encontrar",
            "traga",
            "liste",
            "listar",
            "exemplos de",
            "existe algum",
            "existem",
            "tem algum",
            "quais produtos",
            "quais itens",
            "quais materiais",
            "mais informações sobre",
            "mais informacoes sobre",
            "informações sobre",
            "informacoes sobre",
            "detalhe de",
            "detalhes sobre",
            "search",
            "find",
        )
        product_context = (
            "produto",
            "item",
            "material",
            "cabo",
            "parafuso",
            "chapa",
            "tubo",
            "peça",
            "peca",
            "insumo",
            "mp",
            "componente",
            "motor",
            "válvula",
            "valvula",
            "rolamento",
            "filtro",
            "conector",
            "anel",
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

    def select(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
        description_override: str | None = None,
    ) -> dict | None:
        candidates = candidates_loader(
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

            group_code = self.extract_search_group_code(message, normalized)
            description_query = description_override or self.extract_search_description(
                message
            )
            product_code_query = ChatProductQueryIntentService.extract_product_code(message)
            page_size = self.extract_search_limit(normalized)

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
                elif lowered in {
                    "description",
                    "descricao",
                    "query",
                    "q",
                    "search",
                    "term",
                }:
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
                    parameters = {
                        "group_code": group_code,
                        "page": 1,
                        "page_size": page_size,
                    }
                else:
                    parameters = {
                        "description": description_query,
                        "page_size": page_size,
                    }

            if group_code:
                reason = ExternalActionResponseContentService.format(
                    "selectionReasons",
                    "productSearchByGroup",
                    group_code=group_code,
                )
            else:
                reason = ExternalActionResponseContentService.format(
                    "selectionReasons",
                    "productSearchByDescription",
                    description_query=description_query,
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

    @staticmethod
    def extract_search_description(message: str) -> str:
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
            "busque",
            "buscar",
            "pesquise",
            "pesquisar",
            "procure",
            "procurar",
            "encontre",
            "encontrar",
            "traga",
            "liste",
            "listar",
            "exemplos",
            "de",
            "produtos",
            "produto",
            "itens",
            "item",
            "materiais",
            "material",
            "me",
            "para",
            "mim",
            "os",
            "as",
            "o",
            "a",
            "um",
            "uma",
            "no",
            "na",
            "do",
            "da",
            "com",
            "que",
            "são",
            "sao",
            "tipo",
            "descrição",
            "descricao",
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

    @staticmethod
    def extract_search_group_code(message: str, normalized: str) -> str | None:
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

    @staticmethod
    def extract_search_limit(value: str) -> int:
        match = re.search(
            r"\b(\d{1,2})\s+(?:exemplos?|produtos?|itens?|resultados?)",
            value,
        )

        if match:
            return min(int(match.group(1)), 20)

        match = re.search(
            r"(?:exemplos?|produtos?|itens?|resultados?)\s+(\d{1,2})\b",
            value,
        )

        if match:
            return min(int(match.group(1)), 20)

        return 5
