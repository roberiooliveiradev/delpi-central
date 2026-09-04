"""Intenções e parâmetros para rotas /system/* (metadados Protheus)."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_pagination_defaults_service import (
    ChatOperationalPaginationDefaultsService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatSystemMetadataIntentService:
    @classmethod
    def looks_like_question(cls, normalized: str) -> bool:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "systemMetadata",
            "terms",
        )

        if any(term in normalized for term in terms):
            return True

        # Schema/índices/colunas sem a palavra «tabela» ainda são metadado Protheus.
        return (
            cls.wants_schema(normalized)
            or cls.wants_indexes(normalized)
            or cls.wants_columns(normalized)
            or cls.wants_relations(normalized)
        )

    @classmethod
    def wants_columns(cls, normalized: str) -> bool:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "systemMetadataColumnTerms",
        )

        return any(term in normalized for term in terms)

    @classmethod
    def wants_schema(cls, normalized: str) -> bool:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "systemMetadataSchemaTerms",
        )

        return any(term in normalized for term in terms)

    @classmethod
    def wants_indexes(cls, normalized: str) -> bool:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "systemMetadataIndexTerms",
        )

        return any(term in normalized for term in terms)

    @classmethod
    def wants_relations(cls, normalized: str) -> bool:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "systemMetadataRelationTerms",
        )

        return any(term in normalized for term in terms)

    @classmethod
    def wants_table_search(cls, normalized: str) -> bool:
        if any(
            term in normalized
            for term in (
                "buscar tabela",
                "pesquisar tabela",
                "qual tabela",
                "qual a tabela",
                "qual e a tabela",
                "tabelas do",
            )
        ):
            return True

        return bool(re.search(r"\bqual\s+(?:a\s+)?tabela\b", normalized))

    @classmethod
    def extract_table_name(cls, text: str | None) -> str | None:
        raw = str(text or "")
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        table_match = re.search(
            r"\btabela\s+([a-z]{2,4}\d{0,4})\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if table_match and ChatSqlAuthoringGuidanceService._is_table_name_candidate(
            table_match.group(1)
        ):
            return table_match.group(1).upper()

        inline_match = re.search(
            r"\b(?:colunas?|schema|indices?|índices?|indexes?|relacionamentos?)\s+"
            r"(?:da|de|do)\s+([a-z]{2,4}\d{0,4})\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if inline_match and ChatSqlAuthoringGuidanceService._is_table_name_candidate(
            inline_match.group(1)
        ):
            return inline_match.group(1).upper()

        # «quais indexes da SB1010» / «schema SB1010» — token Protheus no texto.
        bare_match = re.search(
            r"\b([a-z]{2,4}\d{2,4})\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if bare_match and ChatSqlAuthoringGuidanceService._is_table_name_candidate(
            bare_match.group(1)
        ):
            if (
                cls.wants_schema(normalized)
                or cls.wants_indexes(normalized)
                or cls.wants_columns(normalized)
                or cls.wants_relations(normalized)
                or "tabela" in normalized
            ):
                return bare_match.group(1).upper()

        return None

    @classmethod
    def extract_table_search_description(cls, message: str) -> str | None:
        # Matching leve (sem fuzzy/stem) para preservar plural do termo buscado
        # (ex.: «produtos» não vira «produto»).
        normalized = re.sub(
            r"\s+",
            " ",
            ChatMessageNormalizationService.strip_accents(message or ""),
        ).strip()

        patterns = ExternalActionResponseContentService.list(
            "actionSelection",
            "systemTableSearch",
            "patterns",
        )

        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)

            if match:
                query = cls._clean_table_search_description(match.group(1))

                if len(query) >= 2:
                    return query[:120]

        return None

    @classmethod
    def _clean_table_search_description(cls, value: str) -> str:
        query = str(value or "").strip(" .?")
        strip_prefix = ExternalActionResponseContentService.get(
            "actionSelection",
            "systemTableSearch",
            "descriptionStripPrefix",
        )

        if strip_prefix:
            query = re.sub(strip_prefix, "", query, flags=re.IGNORECASE)

        return query.strip(" .?")

    @classmethod
    def build_parameters(cls, message: str, action: dict) -> dict:
        parameters: dict = {}
        path = str(action.get("path") or "")
        table_name = cls.extract_table_name(message)
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
                parameters[name] = ChatOperationalPaginationDefaultsService.standard()
            elif lowered == "description":
                description = cls.extract_table_search_description(message)

                if description:
                    parameters[name] = description
                else:
                    query_match = re.search(
                        r"(?:buscar|pesquisar|procurar)\s+(?:tabela|coluna)s?\s+(.+)$",
                        normalized,
                    )

                    if query_match:
                        parameters[name] = query_match.group(1).strip()[:120]

        if table_name and "{tableName}" in path and not parameters:
            parameters["tableName"] = table_name

        return parameters

    @classmethod
    def score_action(cls, message: str, action: dict) -> int:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        table_name = cls.extract_table_name(message)
        wants_columns = cls.wants_columns(normalized)
        wants_schema = cls.wants_schema(normalized)
        wants_indexes = cls.wants_indexes(normalized)
        wants_relations = cls.wants_relations(normalized)
        wants_table_search = cls.wants_table_search(normalized)
        path = str(action.get("path") or "").lower()
        value = 0

        if wants_schema and table_name and "/tables/" in path and "/schema" in path:
            value += 140

        if wants_indexes and table_name and "/tables/" in path and "/indexes" in path:
            value += 135

        if wants_relations and table_name and "/tables/" in path and "/relations" in path:
            value += 130

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

        if wants_schema and "/schema" not in path:
            value -= 20

        if wants_indexes and "/indexes" not in path:
            value -= 20

        return value
