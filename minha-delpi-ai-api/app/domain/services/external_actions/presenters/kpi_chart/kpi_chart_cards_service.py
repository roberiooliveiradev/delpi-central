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



class ExternalActionKpiChartCardsService:
    @staticmethod
    def kpi_cards_to_linhas(presenter: ExternalActionKpiChartPresenter, kpi: dict) -> list[str]:
        cards = kpi.get("cards")

        if not isinstance(cards, list):
            return []

        linhas: list[str] = []

        for card in cards:
            if not isinstance(card, dict):
                continue

            label = str(card.get("label") or presenter.kpi_title("")).strip()
            unit = str(card.get("unit") or "").strip()
            value = card.get("value")
            field_key = str(card.get("key") or "").strip()

            if value is None:
                continue

            formatted_value = (
                presenter._host._format_field_value(field_key, value)
                if field_key
                else presenter._host._format_field_value(label, value)
            )
            suffix = (
                ""
                if formatted_value.endswith("%") or formatted_value.startswith("R$")
                else f" {unit}".rstrip()
            )
            linhas.append(f"**{label}:** {formatted_value}{suffix}")

        return linhas

    @staticmethod
    def kpi_cards_from_presenter_section(presenter: ExternalActionKpiChartPresenter, section: str, data: dict) -> list[dict]:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        cards_cfg = ChatAssistantContentService.get_node(
            "presenter_content",
            section,
            "kpiCards",
        )

        if not isinstance(cards_cfg, list):
            return []

        cards: list[dict] = []

        for item in cards_cfg:
            if not isinstance(item, dict):
                continue

            field = str(item.get("field") or "").strip()
            label = str(item.get("label") or "").strip()

            if not field or not label:
                continue

            from app.domain.services.chat_presentation_kpi_assembly_service import (
                ChatPresentationKpiAssemblyService,
            )

            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=label,
                    value=data.get(field),
                    unit=str(item.get("unit") or ""),
                    color=str(item.get("color") or "#0ea5e9"),
                    key=field,
                )
            )

        return cards

