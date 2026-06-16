"""Seleção de KPIs departamentais — refinamentos e fallback (DOCIE Fase 7).

Fast paths de suprimentos, dashboards produção e KPI departamental migraram para
``operational_route_registry`` + ``select_by_department_kpi`` no motor operacional.
"""

from __future__ import annotations

from typing import Callable

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
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
            spec = self._supplies_metric_spec(
                path_token=str(refinement.metric_path_token),
                reason=refinement.reason
                or ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "kpiMetricRefinementDefault",
                ),
            )

            return self._route_selection.select(
                spec,
                message=message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                fallback_candidates_loader=candidates_loader,
            )

        if refinement.metric_kind == "department_kpi" and refinement.metric_path_token:
            from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
            from app.domain.services.chat_department_kpi_intent_service import (
                DepartmentKpiMatch,
            )

            match = DepartmentKpiMatch(
                path_token=str(refinement.metric_path_token),
                domain_prefix=str(refinement.metric_domain_prefix or ""),
                reason=refinement.reason
                or ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "departmentKpiRefinement",
                ),
            )

            return self._route_selection.select(
                OperationalApiRouteSpec.from_department_kpi(match),
                message=message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                fallback_candidates_loader=candidates_loader,
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
        from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec

        return self._route_selection.select(
            OperationalApiRouteSpec.from_department_kpi(match),
            message=message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            fallback_candidates_loader=candidates_loader,
        )

    @staticmethod
    def _supplies_metric_spec(*, path_token: str, reason: str):
        from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec

        return OperationalApiRouteSpec.from_supplies_metric(
            path_token=path_token,
            operation_token=path_token,
            reason=reason,
        )
