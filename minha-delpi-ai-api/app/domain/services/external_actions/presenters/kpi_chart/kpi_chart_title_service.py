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



class ExternalActionKpiChartTitleService:
    @staticmethod
    def kpi_title(presenter: ExternalActionKpiChartPresenter, path: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        lowered = str(path or "").lower()
        playbook_title = ChatAssistantContentService.title_for_path(
            "presenter_content",
            path,
            default=None,
        )

        if playbook_title and any(
            token in lowered
            for token in (
                "/consumption/",
                "/losses/",
                "/schedule/today",
                "/orders/open",
                "/orders/finished",
                "/orders/finished-without-consumption",
                "/work-centers/",
                "/allocation-gaps",
                "/planned-vs-real-time",
                "/purchases/top-products",
            )
        ):
            return playbook_title

        matchers = ChatAssistantContentService.get_node(
            "presenter_content",
            "kpiPathMatchers",
        )

        if isinstance(matchers, list):
            generic_domain_fragments = frozenset(
                {
                    "/production/",
                    "/financial/",
                    "/finacial/",
                    "/commercial/",
                    "/quality/",
                    "/hr/",
                    "/supplies/",
                }
            )
            sorted_matchers = sorted(
                (entry for entry in matchers if isinstance(entry, dict)),
                key=lambda entry: (
                    str(entry.get("fragment") or "") in generic_domain_fragments,
                    -len(str(entry.get("fragment") or "")),
                ),
            )

            for entry in sorted_matchers:
                fragment = str(entry.get("fragment") or "").strip()
                title_key = str(entry.get("titleKey") or "").strip()

                if fragment and fragment in lowered and title_key:
                    title = ChatAssistantContentService.get(
                        "presenter_content",
                        "kpiTitles",
                        title_key,
                    )

                    if title:
                        return title

        return ChatAssistantContentService.get(
            "presenter_content",
            "kpiTitles",
            "default",
            default="Indicador",
        )

