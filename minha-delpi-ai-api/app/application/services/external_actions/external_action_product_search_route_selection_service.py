"""Seleção de busca de produtos por grupo ou descrição — Fase 3B lote 19."""

from __future__ import annotations

import re

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductSearchRouteSelectionService:
    @staticmethod
    def looks_like_product_search(value: str) -> bool:
        from app.domain.services.chat_product_search_intent_service import (
            ChatProductSearchIntentService,
        )

        return ChatProductSearchIntentService.looks_like_product_search(value)

    @classmethod
    def build_search_parameters(
        cls,
        message: str,
        normalized: str,
        action: dict,
        *,
        description_override: str | None = None,
    ) -> dict | None:
        group_code = cls.extract_search_group_code(message, normalized)
        description_query = description_override or cls.extract_search_description(message)
        product_code_query = ChatProductQueryIntentService.extract_product_code(message)
        page_size = cls.extract_search_limit(normalized)

        parameters: dict = {}

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

        if parameters:
            return parameters

        if group_code:
            return {
                "group_code": group_code,
                "page": 1,
                "page_size": page_size,
            }

        if not description_query:
            return None

        return {
            "description": description_query,
            "page_size": page_size,
        }

    @staticmethod
    def extract_search_description(message: str) -> str:
        normalized = str(message or "").lower().strip()

        patterns = ExternalActionResponseContentService.list(
            "actionSelection",
            "productSearch",
            "descriptionExtractPatterns",
        )

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
        from app.domain.services.chat_product_search_intent_service import (
            ChatProductSearchIntentService,
        )

        return ChatProductSearchIntentService.extract_search_group_code(
            message,
            normalized,
        )

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
