"""Monta presentation tipo dashboard (multi-card) — Playbook gráficos Fase 4."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatDashboardPresentationService:
    @classmethod
    def _dashboard_text(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "dashboardPresentation",
            *path,
            default=default,
        )

    @classmethod
    def _chart_block_titles(cls) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(
            "presenter_content",
            "dashboardPresentation",
            "chartBlockTitles",
        )

        if not isinstance(node, dict):
            return {}

        return {str(key): str(value) for key, value in node.items() if value}

    @classmethod
    def _resolve_dashboard_title(cls, path: str) -> str:
        lowered = str(path or "").lower()
        titles = ChatAssistantContentService.get_node(
            "presenter_content",
            "dashboardPresentation",
            "titlesByPathFragment",
        )

        if isinstance(titles, dict):
            for fragment, title in titles.items():
                if str(fragment).lower() in lowered:
                    return str(title)

        return cls._dashboard_text("defaultTitle", default="Dashboard")

    @classmethod
    def build(
        cls,
        root: dict[str, Any],
        *,
        path: str,
        build_kpi,
        build_lmp_table,
        build_items_table,
        build_items_chart=None,
    ) -> dict[str, Any] | None:
        if not isinstance(root, dict):
            return None

        lowered = str(path or "").lower()
        has_dashboard_path = "dashboard" in lowered
        has_shape = isinstance(root.get("summary"), dict) and (
            isinstance(root.get("charts"), dict)
            or isinstance(root.get("items"), list)
        )

        if not has_dashboard_path and not has_shape:
            return None

        panels: list[dict[str, Any]] = []

        summary = root.get("summary")

        if isinstance(summary, dict):
            kpi = build_kpi(summary, path)

            if kpi:
                panels.append(
                    {
                        "id": "summary",
                        "title": str(
                            kpi.get("title")
                            or cls._dashboard_text("summaryFallbackTitle", default="Resumo")
                        ),
                        "presentation": kpi,
                    }
                )

        charts = root.get("charts")

        if isinstance(charts, dict):
            for key, panel_title in cls._chart_block_titles().items():
                block = charts.get(key)

                if not isinstance(block, list) or not block:
                    continue

                chart = cls._chart_from_labeled_values(block, title=panel_title, block_key=key)

                if chart:
                    panels.append(
                        {
                            "id": key,
                            "title": panel_title,
                            "presentation": chart,
                        }
                    )

        items = root.get("items")

        if isinstance(items, list) and items and isinstance(items[0], dict):
            table = None

            if "sale_number" in items[0] or "saleNumber" in items[0]:
                table = build_lmp_table(items, root)
            else:
                table = build_items_table(
                    items,
                    title=cls._dashboard_text("panelItemsTitle", default="Itens do painel"),
                )

            if table and table.get("type") == "table":
                items_panel: dict[str, Any] = {
                    "id": "items",
                    "title": str(
                        table.get("title")
                        or cls._dashboard_text("itemsFallbackTitle", default="Itens")
                    ),
                    "presentation": table,
                }

                if build_items_chart:
                    chart = build_items_chart(items, root, path)

                    if isinstance(chart, dict) and chart.get("type") == "chart":
                        items_panel["chartPresentation"] = chart

                panels.append(items_panel)

        if len(panels) < 2:
            return None

        return {
            "type": "dashboard",
            "title": cls._resolve_dashboard_title(lowered),
            "panels": panels[:6],
        }

    @classmethod
    def _chart_from_labeled_values(
        cls,
        rows: list[Any],
        *,
        title: str,
        block_key: str,
    ) -> dict[str, Any] | None:
        data: list[dict[str, Any]] = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            name = row.get("name") or row.get("nivel") or row.get("label")
            value = row.get("value")

            if value is None:
                value = row.get("valor") or row.get("count") or row.get("total")

            if name is None or value is None:
                continue

            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue

            label_key = "nivel" if "nivel" in row else "name"
            data.append({label_key: str(name), "value": numeric})

        if len(data) < 2:
            return None

        label_key = "nivel" if data and "nivel" in data[0] else "name"
        chart_type = "horizontal_bar" if label_key == "nivel" else "donut"

        if block_key == "evolutionData":
            chart_type = "line"

        return {
            "type": "chart",
            "title": title,
            "chartType": chart_type,
            "data": data[:24],
            "config": {
                "xAxis": label_key,
                "yAxis": ["value"],
                "legend": False,
            },
        }
