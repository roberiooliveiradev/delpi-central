"""Seleção de rotas comerciais, Transforma e metadados Protheus — Fase 3B lote 18."""

from __future__ import annotations

import re
from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ExternalActionDomainRouteSelectionService:
    def __init__(self, repository) -> None:
        self.repository = repository

    @staticmethod
    def looks_like_sale_orders_list_question(value: str) -> bool:
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

    @staticmethod
    def looks_like_transforma_question(value: str) -> bool:
        return "transforma" in value

    @staticmethod
    def looks_like_system_metadata_question(value: str) -> bool:
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

    def select_sale_orders(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
        merge_date_parameters: Callable[..., dict],
    ) -> dict | None:
        candidates = candidates_loader(
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
                "parameters": self._build_sale_orders_parameters(
                    best,
                    message,
                    merge_date_parameters=merge_date_parameters,
                ),
            },
            "reason": "A pergunta solicita listagem de ordens de venda.",
        }

    def select_transforma(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
        build_date_branch_parameters: Callable[..., dict],
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = [
            action
            for action in candidates_loader(
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
                "parameters": build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                ),
            },
            "reason": "A pergunta solicita dados do programa Transforma Mais.",
        }

    def select_system_metadata(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None:
        allowed = {str(item) for item in allowed_action_ids}
        candidates = [
            action
            for action in candidates_loader(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )
            if action.get("method") == "GET"
            and str(action.get("path") or "").lower().startswith("/system/")
        ]

        if not candidates and allowed:
            list_actions = getattr(self.repository, "list_actions", None)

            if callable(list_actions):
                candidates = [
                    action
                    for action in list_actions()
                    if str(action.get("actionId")) in allowed
                    if action.get("method") == "GET"
                    and str(action.get("path") or "").lower().startswith("/system/")
                ]

        if not candidates:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        table_name = self._extract_protheus_table_name(message)
        wants_columns = "coluna" in normalized
        wants_relations = any(
            term in normalized
            for term in ("relacion", "relacionar", "join", "ligar", "associar")
        )
        wants_table_search = self._wants_system_table_search(normalized)

        def score(action: dict) -> int:
            path = str(action.get("path") or "").lower()
            value = 0

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

    @staticmethod
    def _build_sale_orders_parameters(
        action: dict,
        message: str,
        *,
        merge_date_parameters: Callable[..., dict],
    ) -> dict:
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

        return merge_date_parameters(action, message, parameters)

    @staticmethod
    def _wants_system_table_search(normalized: str) -> bool:
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

    def _extract_system_table_search_description(self, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        for pattern in (
            r"(?:buscar|pesquisar|procurar)\s+tabelas?\s+(.+?)(?:\?|$)",
            r"\bqual\s+(?:a\s+)?tabela(?:s)?\s+(?:de|do|da|dos|das)\s+(.+?)(?:\?|$)",
            r"\bqual\s+(?:a\s+)?tabela(?:s)?\s+(?:que\s+)?"
            r"(?:guarda|guardam|armazena|armazenam|contem|possui|tem|registra|grava)\s+"
            r"(.+?)(?:\?|$)",
            r"\bqual\s+(?:a\s+)?tabela(?:s)?\s+guarda(?:m)?\s+(.+?)(?:\?|$)",
        ):
            match = re.search(pattern, normalized, flags=re.IGNORECASE)

            if match:
                query = self._clean_table_search_description(match.group(1))

                if len(query) >= 2:
                    return query[:120]

        return None

    @staticmethod
    def _clean_table_search_description(value: str) -> str:
        query = str(value or "").strip(" .?")
        query = re.sub(
            r"^(?:as?\s+|os?\s+)?(?:informacoes?|dados|registros?)\s+(?:de|do|da|dos|das|sobre)\s+",
            "",
            query,
            flags=re.IGNORECASE,
        )

        return query.strip(" .?")

    def _extract_protheus_table_name(self, text: str | None) -> str | None:
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
            r"\bcolunas?\s+(?:da|de)\s+([a-z]{2,4}\d{0,4})\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if inline_match and ChatSqlAuthoringGuidanceService._is_table_name_candidate(
            inline_match.group(1)
        ):
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
                description = self._extract_system_table_search_description(message)

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
