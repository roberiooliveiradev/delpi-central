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



class ExternalActionKpiChartPresentService:
    @staticmethod
    def present_kpi_response(
        presenter: ExternalActionKpiChartPresenter,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> dict | None:
        if not isinstance(root, dict):
            return None

        if not presenter.looks_like_kpi_response(root, path, entity=entity):
            return presenter._host._present_dict_fallback(root, path)

        kpi = presenter.build_kpi_chart(root, path)

        if kpi:
            linhas = presenter.kpi_cards_to_linhas(kpi)
            kpi_title = kpi.get("title") or presenter.kpi_title(path)

            return {
                "titulo": kpi_title,
                "linhas": linhas
                or [
                    presenter._host._presenter_text(
                        "generic",
                        "kpiSeeData",
                        title=kpi_title,
                    )
                ],
                "dados": root,
                "apresentacao": kpi,
            }

        fallback = presenter._host._present_dict_fallback(root, path)

        if fallback:
            return fallback

        kpi_title = presenter.kpi_title(path)

        return {
            "titulo": kpi_title,
            "linhas": [
                presenter._host._presenter_text(
                    "generic",
                    "kpiSeeData",
                    title=kpi_title,
                )
            ],
            "dados": root,
        }

