"""Delegate — KPI/chart presenter titles."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
        from app.domain.services.result_presentation_title_resolver import (
            ResultPresentationTitleResolver,
        )

        metadata = getattr(presenter, "metadata", None)
        if not isinstance(metadata, dict):
            host = getattr(presenter, "_host", None)
            host_meta = getattr(host, "metadata", None) if host is not None else None
            metadata = host_meta if isinstance(host_meta, dict) else {}

        default_title = ChatAssistantContentService.get(
            "presenter_content",
            "kpiTitles",
            "default",
            default="Indicador",
        )

        resolved = ResultPresentationTitleResolver.resolve(
            path=path,
            summary=str(metadata.get("summary") or metadata.get("actionSummary") or ""),
            action_id=str(metadata.get("actionId") or ""),
            metadata=metadata,
            fallback=str(default_title or "Indicador"),
        )
        return resolved.title
