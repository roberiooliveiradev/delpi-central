"""Seleção de actions OpenAPI de LMP — Fase 3B lote 5."""

from __future__ import annotations

import re
from typing import Callable


class ExternalActionLmpRouteSelectionService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def _load_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable | None = None,
    ) -> list[dict]:
        if not allowed_action_ids or not candidates_loader:
            return []

        return candidates_loader(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        ) or []

    def select(
        self,
        message: str,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
        *,
        candidates_loader: Callable | None = None,
        merge_date_parameters: Callable | None = None,
    ) -> dict | None:
        if not allowed_action_ids:
            return None

        candidates = self._load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
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
            merge_date_parameters=merge_date_parameters,
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
        merge_date_parameters: Callable | None = None,
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

        if merge_date_parameters:
            return merge_date_parameters(action, message, parameters)

        return parameters
