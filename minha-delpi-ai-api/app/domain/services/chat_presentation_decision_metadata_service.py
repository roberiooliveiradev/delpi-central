"""Helpers de metadata para decisão de apresentação — extraído do god class jun/2026."""

from __future__ import annotations

from typing import Any

_CHART_SELECTED_TOKENS = frozenset(
    {
        "line_chart",
        "area_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
        "grouped_bar",
        "stacked_bar",
        "combo_chart",
        "histogram",
        "heatmap",
        "gauge",
        "scatter",
        "chart",
    }
)


class ChatPresentationDecisionMetadataService:
    @classmethod
    def entity_from_metadata(cls, metadata: dict[str, Any] | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                return raw_entity.strip()

        raw_entity = metadata.get("entity")

        if isinstance(raw_entity, str) and raw_entity.strip():
            return raw_entity.strip()

        return None

    @classmethod
    def resolve_entity(
        cls,
        metadata: dict[str, Any] | None,
        *,
        path: str | None = None,
    ) -> str | None:
        entity = cls.entity_from_metadata(metadata)

        if entity or not path:
            return entity

        from app.domain.services.chat_operational_response_profile_service import (
            ChatOperationalResponseProfileService,
        )

        resolved_entity = str(
            ChatOperationalResponseProfileService.resolve(
                metadata if isinstance(metadata, dict) else {},
                path=path,
            ).entity
            or ""
        ).strip()

        return resolved_entity or None

    @classmethod
    def view_has_presentation(cls, metadata: dict[str, Any], view: str) -> bool:
        token = str(view or "").strip().lower()

        if token in {"", "canvas", "checklist"}:
            return True

        if token == "text":
            text_presentation = metadata.get("textPresentation")

            return isinstance(text_presentation, dict) and bool(
                str(text_presentation.get("markdown") or "").strip()
            )

        slot_by_view = {
            "table": "tablePresentation",
            "tree": "treePresentation",
            "chart": "chartPresentation",
            "kpi": "kpiPresentation",
            "dashboard": "dashboardPresentation",
        }
        slot_key = slot_by_view.get(token)
        presentation = metadata.get(slot_key) if slot_key else None

        if presentation is None and token in _CHART_SELECTED_TOKENS:
            presentation = metadata.get("chartPresentation")

        if isinstance(presentation, dict):
            presentation_type = str(presentation.get("type") or "").strip().lower()

            if token in _CHART_SELECTED_TOKENS:
                return presentation_type in {
                    "chart",
                    "line_chart",
                    "bar_chart",
                    "horizontal_bar",
                    "donut",
                    "area_chart",
                }

            return presentation_type == token or (
                token == "table" and presentation_type == "table"
            )

        primary = metadata.get("presentation")

        if isinstance(primary, dict):
            presentation_type = str(primary.get("type") or "").strip().lower()

            if token == "table":
                return presentation_type == "table"

            if token in _CHART_SELECTED_TOKENS:
                return presentation_type == "chart"

            return presentation_type == token

        if token == "table":
            bundled = metadata.get("tablePresentations")

            return isinstance(bundled, list) and any(
                isinstance(item, dict) and item.get("type") == "table" for item in bundled
            )

        return False

    @classmethod
    def metadata_has_visual(cls, metadata: dict[str, Any]) -> bool:
        for key in (
            "tablePresentation",
            "chartPresentation",
            "treePresentation",
            "kpiPresentation",
            "dashboardPresentation",
        ):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type"):
                return True

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            presentation_type = str(presentation.get("type") or "").strip().lower()

            if presentation_type in {"table", "chart", "tree", "kpi", "dashboard"}:
                return True

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            return any(
                isinstance(item, dict) and item.get("type") == "table" and (item.get("rows") or [])
                for item in bulk
            )

        return False

    @classmethod
    def rows_from_presentation(
        cls,
        presentation: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(presentation, dict):
            return []

        if presentation.get("type") != "table":
            return []

        rows = presentation.get("rows") or []

        return [row for row in rows if isinstance(row, dict)]

    @classmethod
    def rows_from_metadata_tables(cls, metadata: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not isinstance(metadata, dict):
            return []

        for key in ("tablePresentation", "presentation", "profileTablePresentation"):
            rows = cls.rows_from_presentation(metadata.get(key))

            if rows:
                return rows

        bulk = metadata.get("tablePresentations")

        if not isinstance(bulk, list):
            return []

        combined: list[dict[str, Any]] = []

        for table in bulk:
            if not isinstance(table, dict) or table.get("type") != "table":
                continue

            combined.extend(cls.rows_from_presentation(table))

        return combined

    @classmethod
    def message_from_metadata(cls, metadata: dict[str, Any]) -> str:
        from app.domain.services.chat_humanized_data_response_service import (
            ChatHumanizedDataResponseService,
        )

        commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(metadata)

        if not isinstance(commentary, dict):
            return ""

        return str(commentary.get("summary") or "").strip()[:320]

    @classmethod
    def stack_commentary_insight(cls, metadata: dict[str, Any]) -> str:
        from app.domain.services.chat_humanized_data_response_service import (
            ChatHumanizedDataResponseService,
        )

        commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(metadata)

        if not isinstance(commentary, dict):
            return ""

        narrative = str(commentary.get("narrativeInsight") or "").strip()

        if narrative:
            return narrative

        summary = str(commentary.get("summary") or "").strip()

        if summary:
            return summary

        highlights = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]

        if not highlights:
            return ""

        return highlights[0]

    @classmethod
    def effective_tree_presentation(
        cls,
        *,
        tree_presentation: dict[str, Any] | None = None,
        primary_presentation: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if isinstance(tree_presentation, dict) and tree_presentation.get("type") == "tree":
            return tree_presentation

        if isinstance(primary_presentation, dict) and primary_presentation.get("type") == "tree":
            return primary_presentation

        return None

    @classmethod
    def resolve_dashboard_presentation(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        dashboard = metadata.get("dashboardPresentation")

        if isinstance(dashboard, dict) and dashboard.get("type") == "dashboard":
            return dashboard

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict) and presentation.get("type") == "dashboard":
            return presentation

        return None

    @classmethod
    def tree_node_count(cls, tree_presentation: dict[str, Any] | None) -> int | bool:
        if not isinstance(tree_presentation, dict):
            return False

        nodes = tree_presentation.get("nodes")

        if isinstance(nodes, list):
            return len(nodes)

        root = tree_presentation.get("root")

        if isinstance(root, dict) and root:
            children = root.get("children")

            if isinstance(children, list) and children:
                return len(children) + 1

            return 1

        return False

    @classmethod
    def is_product_field_value_table(cls, rows: list[dict[str, Any]] | None) -> bool:
        if not rows:
            return False

        sample = rows[0]

        if not isinstance(sample, dict):
            return False

        keys = {str(key).strip().lower() for key in sample.keys()}

        return keys == {"campo", "valor"} or keys == {"field", "value"}
