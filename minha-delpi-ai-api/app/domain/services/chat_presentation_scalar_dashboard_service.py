"""Dashboard declarativo para payloads campo-valor (ROL, KPIs departamentais)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_scalar_field_commentary_service import (
    ChatPresentationScalarFieldCommentaryService,
)


class ChatPresentationScalarDashboardService:
    @classmethod
    def matches(cls, root: dict[str, Any]) -> bool:
        if not isinstance(root, dict):
            return False

        if isinstance(root.get("items"), list):
            return False

        payload = ChatPresentationScalarFieldCommentaryService._unwrap_payload(root)

        return ChatPresentationScalarFieldCommentaryService._has_numeric_metrics(payload)

    @classmethod
    def build(
        cls,
        root: dict[str, Any],
        *,
        path: str,
        build_kpi: Callable[[dict[str, Any], str], dict[str, Any] | None],
        build_kv_table: Callable[[dict[str, Any], str], dict[str, Any] | None],
    ) -> dict[str, Any] | None:
        if not cls.matches(root):
            return None

        payload = ChatPresentationScalarFieldCommentaryService._unwrap_payload(root)

        if not isinstance(payload, dict):
            return None

        kpi = build_kpi(payload, path)
        detail_table = build_kv_table(payload, path)
        panels: list[dict[str, Any]] = []

        if isinstance(kpi, dict) and str(kpi.get("type") or "").strip().lower() == "kpi":
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

        if isinstance(detail_table, dict) and detail_table.get("type") == "table":
            panels.append(
                {
                    "id": "metrics",
                    "title": str(
                        detail_table.get("title")
                        or cls._dashboard_text("metricsFallbackTitle", default="Detalhamento")
                    ),
                    "presentation": detail_table,
                }
            )

        if not panels:
            return None

        if len(panels) < 2 and isinstance(kpi, dict):
            return {
                "type": "dashboard",
                "title": cls._resolve_dashboard_title(path, fallback=str(kpi.get("title") or "")),
                "panels": panels,
            }

        if len(panels) < 2:
            return None

        return {
            "type": "dashboard",
            "title": cls._resolve_dashboard_title(path),
            "panels": panels[:6],
        }

    @classmethod
    def build_kv_table(
        cls,
        payload: dict[str, Any],
        *,
        path: str,
        label_for: Callable[[str], str],
        format_value: Callable[[str, Any], str],
        field_labels: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.external_actions.external_action_column_label_service import (
            ExternalActionColumnLabelService,
        )

        labels = field_labels if isinstance(field_labels, dict) else {}
        ordered_keys = ChatPresentationScalarFieldCommentaryService._ordered_metric_keys(
            payload,
            field_labels=labels,
        )

        if not ordered_keys:
            return None

        rows = [
            {
                "campo": label_for(str(key)),
                "valor": format_value(str(key), payload.get(key)),
            }
            for key in ordered_keys
        ]

        return {
            "type": "table",
            "title": cls._resolve_detail_table_title(path),
            "columns": ExternalActionColumnLabelService().kv_table_column_defs(),
            "rows": rows,
        }

    @classmethod
    def _resolve_dashboard_title(cls, path: str, *, fallback: str = "") -> str:
        title = cls._title_for_fragment_map(
            ("dashboardPresentation", "titlesByPathFragment"),
            path,
        )

        if title:
            return title

        if fallback.strip():
            return fallback.strip()

        return cls._dashboard_text("defaultTitle", default="Dashboard")

    @classmethod
    def _resolve_detail_table_title(cls, path: str) -> str:
        title = cls._title_for_fragment_map(
            ("dashboardPresentation", "detailTableTitlesByPathFragment"),
            path,
        )

        if title:
            return title

        kpi_title = ChatAssistantContentService.title_for_path(
            "presenter_content",
            path,
        )

        if kpi_title:
            return f"{kpi_title} — detalhamento"

        return cls._dashboard_text("metricsFallbackTitle", default="Detalhamento")

    @classmethod
    def _title_for_fragment_map(cls, node_path: tuple[str, ...], path: str) -> str | None:
        fragments = ChatAssistantContentService.get_node("presenter_content", *node_path)

        if not isinstance(fragments, dict):
            return None

        lowered = str(path or "").lower()

        for fragment, label in sorted(
            fragments.items(),
            key=lambda item: len(str(item[0] or "")),
            reverse=True,
        ):
            if str(fragment).lower() in lowered:
                return str(label)

        return None

    @classmethod
    def _dashboard_text(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "dashboardPresentation",
            key,
            default=default,
        )
