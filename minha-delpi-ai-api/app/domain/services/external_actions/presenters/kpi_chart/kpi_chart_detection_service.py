"""Delegate — KPI/chart presenter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_constants import (
    SERIES_LIST_KEYS,
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
        """F2 — entity/shape authority; path tokens are not authority."""
        del presenter  # host reserved for parity with other kpi delegates

        if not isinstance(root, dict):
            return False

        if entity == "product_billing":
            return False

        if entity and ChatOperationalResponseProfileService.is_kpi_entity(entity):
            return True

        kpi_keys = ("value", "percentage", "current", "previous", "target", "meta")
        has_series = any(k in root for k in SERIES_LIST_KEYS)
        kpi_count = sum(1 for k in kpi_keys if k in root)

        if has_series:
            flags = ChatPresentationProfileService.flags(path, entity)
            policy = str(
                (ChatPresentationProfileService.resolve_profile(path, entity) or {}).get(
                    "defaultViewPolicy"
                )
                or ""
            ).strip().lower()
            if "kpi" in flags or "chart" in flags or policy == "kpi_when_available":
                return True

        if kpi_count >= 2 or (kpi_count >= 1 and has_series):
            return True

        has_nested = any(isinstance(value, (dict, list)) for value in root.values())

        if not root.get("items") and not has_nested and len(root) <= 8:
            numeric_count = sum(1 for value in root.values() if isinstance(value, (int, float)))

            if numeric_count >= 2:
                return True

        return False
