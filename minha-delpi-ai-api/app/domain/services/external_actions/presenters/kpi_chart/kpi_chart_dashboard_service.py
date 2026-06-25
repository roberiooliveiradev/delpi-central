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



class ExternalActionKpiChartDashboardService:
    @staticmethod
    def build_dashboard_presentation(presenter: ExternalActionKpiChartPresenter, data: Any, *, path: str = "") -> dict | None:
        from app.domain.services.chat_dashboard_presentation_service import (
            ChatDashboardPresentationService,
        )
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )
        from app.domain.services.chat_presentation_scalar_dashboard_service import (
            ChatPresentationScalarDashboardService,
        )

        root = presenter._host._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        def _build_scalar_kpi(payload: dict, route: str) -> dict | None:
            cards = presenter.build_generic_kpi_cards(payload, route)

            if not cards:
                return presenter.build_kpi_chart(payload, route)

            return ChatPresentationKpiAssemblyService.build(
                title=presenter.kpi_title(route)
                or presenter._host._presenter_text("charts", "dashboardKpiFallbackTitle"),
                cards=cards,
                min_cards=1,
            )

        scalar_dashboard = ChatPresentationScalarDashboardService.build(
            root,
            path=path,
            build_kpi=_build_scalar_kpi,
            build_kv_table=lambda payload, route: ChatPresentationScalarDashboardService.build_kv_table(
                payload,
                path=route,
                label_for=lambda key: presenter._host._column_labels.label_for(
                    key,
                    schema_labels=presenter._host._active_schema_labels,
                ),
                format_value=lambda key, value: presenter._host._format_field_value(key, value),
                field_labels=presenter._host._active_schema_labels,
            ),
        )

        if scalar_dashboard:
            return scalar_dashboard

        return ChatDashboardPresentationService.build(
            root,
            path=path,
            build_kpi=lambda summary, route: (
                (
                    ChatPresentationKpiAssemblyService.build(
                        title=presenter.kpi_title(route)
                        or presenter._host._presenter_text("charts", "dashboardKpiFallbackTitle"),
                        cards=cards,
                        min_cards=1,
                    )
                    if (cards := presenter.build_generic_kpi_cards(summary, route))
                    else None
                )
                or presenter.build_kpi_chart(summary, route)
            ),
            build_lmp_table=presenter._host._build_lmp_table,
            build_items_table=lambda items, title: presenter._host._build_items_table(
                items,
                title=presenter._host._infer_items_title(items, path) or title,
                path=path,
            ),
            build_items_chart=lambda items, root_payload, route: presenter.build_chart_presentation(
                {**root_payload, "items": items},
                path=route,
                force=True,
            ),
        )

