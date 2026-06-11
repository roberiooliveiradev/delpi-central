"""Montagem de parâmetros HTTP por estratégia — desacoplada do domínio da rota."""

from __future__ import annotations

import re
from typing import Any, Callable

from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class OperationalApiParameterBuilderService:
    """Aplica estratégias declaradas em `api_route_domains.json`."""

    def build(
        self,
        spec: OperationalApiRouteSpec,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
        product_builder: Callable[..., dict] | None = None,
    ) -> dict:
        strategy = str(spec.parameter_strategy or "").strip().lower()

        if strategy == "product_code" and product_builder and spec.entity_code:
            return product_builder(
                action,
                spec.entity_code,
                message=message,
            )

        if strategy == "date_branch":
            parameters = self.build_date_branch(
                action,
                message,
                previous_messages=previous_messages,
            )

            if parameters:
                return parameters

            if spec.domain == "supplies_kpi":
                return self.build_supplies_stock(action)

            return parameters

        if strategy == "supplies_stock":
            return self.build_supplies_stock(action)

        return {}

    def build_date_branch(
        self,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        parameters: dict[str, Any] = {}
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
            elif date_range and lowered in {
                "reference_date",
                "referencedate",
            }:
                parameters[name] = date_range.start_date
            elif lowered in {"page"}:
                parameters[name] = 1
            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 50
            elif lowered in {"work_center", "workcenter"} and branch_match is None:
                work_center_match = re.search(r"\bct\s+(\S+)", normalized)

                if work_center_match:
                    parameters[name] = work_center_match.group(1)
            elif lowered == "product_group":
                group_match = re.search(r"\bgrupo\s+(\d{4})\b", normalized)

                if group_match:
                    parameters[name] = group_match.group(1)
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

    def merge_date_range(
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

            if lowered in {
                "start_date",
                "startdate",
                "data_inicio",
                "data_inicial",
                "date_start",
                "datestart",
            }:
                merged[name] = date_range.start_date
            elif lowered in {
                "end_date",
                "enddate",
                "data_fim",
                "data_final",
                "date_end",
                "dateend",
            }:
                merged[name] = date_range.end_date
            elif lowered in {
                "reference_date",
                "referencedate",
            }:
                merged[name] = date_range.start_date

        return merged

    @staticmethod
    def build_supplies_stock(action: dict) -> dict:
        parameters: dict[str, Any] = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"top_limit", "limit"}:
                parameters[name] = 10

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
