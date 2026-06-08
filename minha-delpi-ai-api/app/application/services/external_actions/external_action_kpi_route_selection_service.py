"""Seleção de KPIs departamentais e de suprimentos — Fase 3B lote 17."""

from __future__ import annotations

from typing import Callable

from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)


class ExternalActionKpiRouteSelectionService:
    def __init__(self, route_selection) -> None:
        self._route_selection = route_selection

    def try_select_without_product_code(
        self,
        message: str,
        normalized: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        if self.looks_like_cpv_question(normalized):
            selected = self.select_supplies_metric(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="cpv",
                operation_token="cpv",
                reason="A pergunta solicita o indicador CPV de suprimentos.",
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        if self.looks_like_otd_question(normalized):
            department_otd = ChatDepartmentKpiIntentService.resolve(message)
            path_token = str(getattr(department_otd, "path_token", "") or "").lower()

            if department_otd and ("otd" in path_token or "on_time" in path_token):
                selected = self.select_department_kpi(
                    message,
                    allowed_action_ids=allowed_action_ids,
                    match=department_otd,
                    previous_messages=previous_messages,
                    candidates_loader=candidates_loader,
                )

                if selected:
                    return selected

            selected = self.select_supplies_metric(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="otd",
                operation_token="otd",
                reason="A pergunta solicita o indicador OTD de suprimentos.",
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        if self.looks_like_inventory_turnover_question(normalized):
            selected = self.select_supplies_metric(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token="inventory-turnover",
                operation_token="inventory_turnover",
                reason="A pergunta solicita giro de estoque (IDD) em suprimentos.",
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        if self.looks_like_supplies_stock_kpi(normalized):
            selected = self.select_supplies_stock_value(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        department_kpi = ChatDepartmentKpiIntentService.resolve(message)

        if department_kpi:
            return self.select_department_kpi(
                message,
                allowed_action_ids=allowed_action_ids,
                match=department_kpi,
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
            )

        return None

    def select_metric_refinement(
        self,
        message: str,
        refinement,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        if refinement.metric_kind == "supplies" and refinement.metric_path_token:
            return self.select_supplies_metric(
                message,
                allowed_action_ids=allowed_action_ids,
                path_token=str(refinement.metric_path_token),
                operation_token=str(refinement.metric_path_token),
                reason=refinement.reason or "Refino de indicador de suprimentos.",
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
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

            return self.select_department_kpi(
                message,
                allowed_action_ids,
                match=match,
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
            )

        return None

    def select_department_kpi(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        match,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        spec = OperationalApiRouteSpec.from_department_kpi(match)

        return self._route_selection.select(
            spec,
            message=message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            fallback_candidates_loader=candidates_loader,
        )

    def select_supplies_metric(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        path_token: str,
        operation_token: str,
        reason: str,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        spec = OperationalApiRouteSpec.from_supplies_metric(
            path_token=path_token,
            operation_token=operation_token,
            reason=reason,
        )

        return self._route_selection.select(
            spec,
            message=message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            fallback_candidates_loader=candidates_loader,
        )

    def select_supplies_stock_value(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None:
        candidates = candidates_loader(
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

    @staticmethod
    def looks_like_cpv_question(value: str) -> bool:
        return any(
            term in value
            for term in (
                "cpv",
                "custo de produção vendido",
                "custo de producao vendido",
                "custo producao vendido",
            )
        )

    @staticmethod
    def looks_like_otd_question(value: str) -> bool:
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

    @staticmethod
    def looks_like_inventory_turnover_question(value: str) -> bool:
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

    @staticmethod
    def looks_like_supplies_stock_kpi(value: str) -> bool:
        terms = [
            "valor total",
            "valor de estoque",
            "valor do estoque",
            "valor em estoque",
        ]

        return any(term in value for term in terms)

    @staticmethod
    def _score_supplies_stock_action(action: dict) -> int:
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

    @staticmethod
    def _build_supplies_stock_parameters(action: dict) -> dict:
        parameters = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"top_limit", "limit"}:
                parameters[name] = 10

        return parameters
