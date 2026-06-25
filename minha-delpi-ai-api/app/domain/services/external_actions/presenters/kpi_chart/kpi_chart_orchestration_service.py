"""Delegate — KPI/chart presenter."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_constants import (
    CHART_WORTHY_NUMERIC_KEYS,
    NO_CHART_PATHS,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.presenters.kpi_chart_presenter import (
        ExternalActionKpiChartPresenter,
    )



class ExternalActionKpiChartOrchestrationService:
    @staticmethod
    def build_chart_presentation(
        presenter: ExternalActionKpiChartPresenter,
        data: Any,
        *,
        path: str = "",
        force: bool = False,
    ) -> dict | None:
        """Gera presentation tipo chart APENAS quando dados são naturalmente visuais."""
        entity = ChatOperationalResponseProfileService.resolve_entity(data, path=path)

        if not force:
            if ChatOperationalResponseProfileService.is_no_chart_route(entity, path):
                return None

        root = presenter._host._unwrap_data(data)

        if isinstance(root, dict) and ChatOperationalResponseProfileService.matches_entity(
            entity,
            "product_analyser",
        ):
            normalized = presenter._host._normalize_analyser_root(root)
            analyser_chart = presenter._build_analyser_structure_type_chart(normalized)

            if analyser_chart:
                return analyser_chart

        if not force and path:
            entity = ChatOperationalResponseProfileService.resolve(
                root if isinstance(root, dict) else {},
                path=path,
            ).entity
            profile = ChatPresentationProfileService.resolve_profile(path, entity)

            if (
                str(profile.get("chartPolicy") or "auto").strip().lower() == "skip"
            ):
                return None

        if not isinstance(root, dict):
            if isinstance(root, list) and root and isinstance(root[0], dict):
                return presenter.try_chart_from_rows(root, force=force, path=path)

            return None

        stock_items = presenter._collect_stock_items(root)

        if stock_items:
            return presenter._build_stock_chart(stock_items)

        items = root.get("items")

        if isinstance(items, list) and items and isinstance(items[0], dict):
            if presenter._is_stock_data(items[0]):
                return presenter._build_stock_chart(items)

            chart = presenter.try_chart_from_rows(items, force=force, path=path)

            if chart:
                return chart

            if force:
                return presenter._build_categorical_count_chart(items, path=path)

            return None

        if presenter.looks_like_kpi_response(root, path):
            stock_value_kpi = presenter._host._build_stock_value_kpi(root, path)

            if stock_value_kpi:
                return stock_value_kpi

            kpi_chart = presenter.build_kpi_chart(root, path)

            if isinstance(kpi_chart, dict) and kpi_chart.get("type") == "chart":
                return kpi_chart

            return kpi_chart

        from app.domain.services.chat_schema_driven_presentation_service import (
            ChatSchemaDrivenPresentationService,
        )

        profile = ChatOperationalResponseProfileService.resolve(data, path=path)
        rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(root)

        return ChatSchemaDrivenPresentationService.build_chart(
            presenter._host,
            root if isinstance(root, dict) else {},
            rows=rows,
            path=path,
            entity=profile.entity,
        )

