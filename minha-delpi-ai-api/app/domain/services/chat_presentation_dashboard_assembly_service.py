"""Dashboard multi-painel — chat base (KPI + gráfico + tabela em um stack)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatPresentationDashboardAssemblyService:
    @classmethod
    def _dashboard_text(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "dashboardPresentation",
            key,
            default=default,
        )

    @classmethod
    def resolve_title(cls, path: str, *, fallback: str | None = None) -> str:
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

        if fallback:
            return fallback

        return cls._dashboard_text("defaultTitle", default="Dashboard")

    @classmethod
    def panel(
        cls,
        *,
        panel_id: str,
        title: str,
        presentation: dict[str, Any],
        chart_presentation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": panel_id,
            "title": title,
            "presentation": presentation,
        }

        if isinstance(chart_presentation, dict):
            payload["chartPresentation"] = chart_presentation

        return payload

    @classmethod
    def build_rich_panels(
        cls,
        *,
        view_order: tuple[str, ...] = ("kpi", "tree", "chart", "table"),
        kpi: dict[str, Any] | None = None,
        tree: dict[str, Any] | None = None,
        chart: dict[str, Any] | None = None,
        table: dict[str, Any] | None = None,
        panel_titles: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        titles = panel_titles or {}
        slots: dict[str, dict[str, Any] | None] = {
            "kpi": kpi,
            "tree": tree,
            "chart": chart,
            "table": table,
        }
        panels: list[dict[str, Any]] = []

        for kind in view_order:
            presentation = slots.get(kind)

            if not isinstance(presentation, dict):
                continue

            presentation_type = str(presentation.get("type") or "").strip().lower()

            if not presentation_type:
                continue

            panel_id = {
                "kpi": "summary",
                "tree": "structure",
                "chart": "chart",
                "table": "detail",
            }.get(kind, kind)

            title = titles.get(kind) or str(presentation.get("title") or "").strip()
            chart_presentation = presentation if presentation_type == "chart" else None

            panels.append(
                cls.panel(
                    panel_id=panel_id,
                    title=title or cls._dashboard_text("panelItemsTitle", default="Itens do painel"),
                    presentation=presentation,
                    chart_presentation=chart_presentation,
                )
            )

        return panels

    @classmethod
    def build(
        cls,
        *,
        title: str,
        panels: list[dict[str, Any]],
        min_panels: int = 2,
    ) -> dict[str, Any] | None:
        normalized = [panel for panel in panels if isinstance(panel, dict) and panel.get("presentation")]

        if len(normalized) < min_panels:
            return None

        return {
            "type": "dashboard",
            "title": str(title or "").strip() or cls._dashboard_text("defaultTitle", default="Dashboard"),
            "panels": normalized[:6],
        }
