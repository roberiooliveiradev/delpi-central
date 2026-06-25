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



class ExternalActionKpiChartBuildService:
    @staticmethod
    def build_kpi_chart(presenter: ExternalActionKpiChartPresenter, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        periods = root.get("periods") or root.get("series") or root.get("history")

        if isinstance(periods, list) and len(periods) >= 2:
            return {
                "type": "chart",
                "title": presenter.kpi_title(path),
                "chartType": "line",
                "data": periods[:24],
                "config": {
                    "xAxis": "period",
                    "legend": True,
                },
            }

        value = root.get("value") or root.get("percentage") or root.get("current")
        target = root.get("target") or root.get("meta")
        previous = root.get("previous") or root.get("anterior")
        unit = root.get("unit") or root.get("unidade") or ""

        if value is not None:
            cards = []
            trend = None
            delta = None

            if previous is not None:
                try:
                    diff = float(value) - float(previous)

                    if diff > 0:
                        trend = "up"
                        delta = f"+{presenter._host._format_num(diff)}{unit}"
                    elif diff < 0:
                        trend = "down"
                        delta = f"{presenter._host._format_num(diff)}{unit}"
                    else:
                        trend = "stable"
                except (ValueError, TypeError):
                    pass

            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=presenter._host._presenter_text("kpiCards", "current"),
                    value=value,
                    unit=str(unit or ""),
                    trend=trend,
                    delta=delta,
                    color="#0ea5e9",
                    key="current",
                )
            )

            if target is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=presenter._host._presenter_text("kpiCards", "target"),
                        value=target,
                        unit=str(unit or ""),
                        color="#10b981",
                        key="target",
                    )
                )

            if previous is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=presenter._host._presenter_text("kpiCards", "previous"),
                        value=previous,
                        unit=str(unit or ""),
                        color="#94a3b8",
                        key="previous",
                    )
                )

            if cards:
                return ChatPresentationKpiAssemblyService.build(
                    title=presenter.kpi_title(path),
                    cards=cards,
                    min_cards=1,
                )

        cards = presenter.build_generic_kpi_cards(root, path)

        if not cards:
            summary = root.get("summary")

            if isinstance(summary, dict):
                cards = presenter.build_generic_kpi_cards(summary, path)

        if cards:
            return ChatPresentationKpiAssemblyService.build(
                title=presenter.kpi_title(path),
                cards=cards,
                min_cards=1,
            )

        return None

    @staticmethod
    def build_generic_kpi_cards(presenter: ExternalActionKpiChartPresenter, root: dict, path: str) -> list | None:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        cfg = ChatAssistantContentService.get_node("presenter_content", "genericKpi") or {}
        palette = cfg.get("palette") or [
            "#0ea5e9",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
        ]
        max_cards = int(cfg.get("maxCards") or 6)
        min_cards = int(cfg.get("minCards") or 2)
        percent_keys = [
            str(token).lower()
            for token in (cfg.get("percentUnitKeys") or ["pct", "percent", "rate"])
            if str(token).strip()
        ]
        cards = []
        idx = 0

        for key, val in root.items():
            if not isinstance(val, (int, float)):
                continue

            field_format = presenter._host._column_labels.resolve_field_format(
                str(key),
                schema_formats=presenter._host._active_schema_formats,
            )
            from app.domain.services.chat_presentation_kpi_assembly_service import (
                ChatPresentationKpiAssemblyService,
            )

            lowered_key = str(key).lower()
            unit = (
                "%"
                if field_format == "percent"
                or any(token in lowered_key for token in percent_keys)
                else ""
            )
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    key=str(key),
                    label=presenter._host._humanize_key(key),
                    value=val,
                    data_type=str(field_format or "") or None,
                    unit=unit,
                    color=str(palette[idx % len(palette)]),
                )
            )
            idx += 1

            if idx >= max_cards:
                break

        return cards if len(cards) >= min_cards else None

