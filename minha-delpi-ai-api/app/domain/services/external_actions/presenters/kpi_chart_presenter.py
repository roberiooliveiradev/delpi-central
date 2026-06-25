"""KPI e gráficos do ExternalActionResultPresenter — fachada fina (W3)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_build_service import (
    ExternalActionKpiChartBuildService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_cards_service import (
    ExternalActionKpiChartCardsService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_dashboard_service import (
    ExternalActionKpiChartDashboardService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_detection_service import (
    ExternalActionKpiChartDetectionService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_orchestration_service import (
    ExternalActionKpiChartOrchestrationService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_present_service import (
    ExternalActionKpiChartPresentService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_row_chart_service import (
    ExternalActionKpiChartRowChartService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_specialized_service import (
    ExternalActionKpiChartSpecializedService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_title_service import (
    ExternalActionKpiChartTitleService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionKpiChartPresenter:
    """Fachada — KPI cards, dashboard, chart orchestration e builders especializados."""

    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def present_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> dict | None:
        return ExternalActionKpiChartPresentService.present_kpi_response(
            self, root, path, entity=entity
        )

    def kpi_cards_to_linhas(self, kpi: dict) -> list[str]:
        return ExternalActionKpiChartCardsService.kpi_cards_to_linhas(self, kpi)

    def kpi_cards_from_presenter_section(self, section: str, data: dict) -> list[dict]:
        return ExternalActionKpiChartCardsService.kpi_cards_from_presenter_section(
            self, section, data
        )

    def build_dashboard_presentation(self, data: Any, *, path: str = "") -> dict | None:
        return ExternalActionKpiChartDashboardService.build_dashboard_presentation(
            self, data, path=path
        )

    def build_chart_presentation(
        self,
        data: Any,
        *,
        path: str = "",
        force: bool = False,
    ) -> dict | None:
        return ExternalActionKpiChartOrchestrationService.build_chart_presentation(
            self, data, path=path, force=force
        )

    def looks_like_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> bool:
        return ExternalActionKpiChartDetectionService.looks_like_kpi_response(
            self, root, path, entity=entity
        )

    def build_kpi_chart(self, root: dict, path: str) -> dict | None:
        return ExternalActionKpiChartBuildService.build_kpi_chart(self, root, path)

    def build_generic_kpi_cards(self, root: dict, path: str) -> list | None:
        return ExternalActionKpiChartBuildService.build_generic_kpi_cards(self, root, path)

    def kpi_title(self, path: str) -> str:
        return ExternalActionKpiChartTitleService.kpi_title(self, path)

    def try_chart_from_rows(
        self,
        rows: list,
        *,
        force: bool = False,
        path: str = "",
        user_message: str | None = None,
    ) -> dict | None:
        return ExternalActionKpiChartRowChartService.try_chart_from_rows(
            self,
            rows,
            force=force,
            path=path,
            user_message=user_message,
        )

    def try_heatmap_from_rows(
        self,
        rows: list,
        *,
        force: bool = False,
        user_message: str | None = None,
    ) -> dict | None:
        return ExternalActionKpiChartRowChartService.try_heatmap_from_rows(
            self,
            rows,
            force=force,
            user_message=user_message,
        )

    def _build_categorical_count_chart(
        self,
        rows: list,
        *,
        path: str = "",
    ) -> dict | None:
        return ExternalActionKpiChartRowChartService._build_categorical_count_chart(
            self, rows, path=path
        )

    def _build_analyser_structure_type_chart(self, root: dict) -> dict | None:
        return ExternalActionKpiChartSpecializedService._build_analyser_structure_type_chart(
            self, root
        )

    def _is_stock_data(self, row: dict) -> bool:
        return ExternalActionKpiChartSpecializedService._is_stock_data(self, row)

    def _collect_stock_items(self, root: dict) -> list | None:
        return ExternalActionKpiChartSpecializedService._collect_stock_items(self, root)

    def _build_stock_chart(self, items: list) -> dict | None:
        return ExternalActionKpiChartSpecializedService._build_stock_chart(self, items)
