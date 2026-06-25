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



class ExternalActionKpiChartDetectionService:
    @staticmethod
    def looks_like_kpi_response(
        presenter: ExternalActionKpiChartPresenter,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> bool:
        if entity == "product_billing":
            return False

        if entity and ChatOperationalResponseProfileService.is_kpi_entity(entity):
            return True

        kpi_paths = (
            "cpv",
            "otd",
            "inventory-turnover",
            "stock-value",
            "giro",
            "turnover",
            "kpi",
            "indicator",
            "snapshot",
            "ebitda",
            "pmr",
            "pdi",
            "completion",
            "closing-rate",
            "new-clients",
            "new-business",
            "depreciation",
            "labor_cost",
            "production_cost",
            "effectiveness",
            "delivery",
        )

        if any(token in path for token in kpi_paths):
            return True

        kpi_keys = ("value", "percentage", "current", "previous", "target", "meta")
        has_series = any(k in root for k in ("periods", "series", "history"))
        kpi_count = sum(1 for k in kpi_keys if k in root)

        if kpi_count >= 2 or (kpi_count >= 1 and has_series):
            return True

        has_nested = any(isinstance(value, (dict, list)) for value in root.values())

        if not root.get("items") and not has_nested and len(root) <= 8:
            numeric_count = sum(1 for value in root.values() if isinstance(value, (int, float)))

            if numeric_count >= 2:
                return True

        return False

