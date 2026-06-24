"""Builder de decisão de apresentação — layout, views e stack narrativo."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)

_NATIVE_PRIMARY_VIEWS = frozenset(
    {
        "table",
        "tree",
        "chart",
        "kpi",
        "dashboard",
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
    }
)

_STACK_VISUAL_PRIORITY = (
    "text",
    "table",
    "tree",
    "chart",
    "line_chart",
    "bar_chart",
    "horizontal_bar",
    "donut",
    "kpi",
    "dashboard",
)


class ChatPresentationDecisionBuilderService:
    @classmethod
    def build(
        cls,
        *,
        selected: str,
        fallback: str,
        reason: str,
        available_views: list[str],
        rows: list[dict[str, Any]] | None,
        intent: str | None,
        data_shape: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        shape = data_shape or ChatPresentationDataShapeAnalyzer.analyze(rows=rows)
        unique_views = list(dict.fromkeys(str(view).strip() for view in available_views if str(view).strip()))
        selected_token = str(selected or "").strip().lower()

        if selected_token == "text":
            layout_mode = "single"
            visual_order = ["text"] if "text" in unique_views else unique_views[:1] or ["text"]
        elif selected_token in _NATIVE_PRIMARY_VIEWS:
            layout_mode = "single"
            visual_order = [selected_token]
        else:
            layout_mode = "stack" if len(unique_views) >= 2 else "single"
            visual_order = cls.visual_order_for_stack(unique_views)

        return {
            "selected": selected,
            "fallback": fallback,
            "reason": reason,
            "availableViews": available_views,
            "layoutMode": layout_mode,
            "visualOrder": visual_order,
            "dataShape": {
                "rows": shape.get("rows", 0),
                "columns": shape.get("columns", 0),
                "hasDate": shape.get("hasDate", False),
                "hasNumeric": shape.get("hasNumeric", False),
                "hasCategory": shape.get("hasCategory", False),
                "hasHierarchy": shape.get("hasHierarchy", False),
                "labelKey": shape.get("labelKey"),
                "numericKeys": shape.get("numericKeys") or [],
            },
            "intent": str(intent or "").strip() or None,
        }

    @classmethod
    def apply_rich_text_stack_layout(cls, decision: dict[str, Any]) -> dict[str, Any]:
        views = [
            str(view).strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view).strip()
        ]

        if len(views) >= 2:
            decision["layoutMode"] = "stack"
            decision["visualOrder"] = cls.visual_order_for_stack(views)

        return decision

    @classmethod
    def merge_views(
        cls,
        available_formats: list[str] | None,
        defaults: list[str],
    ) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()

        for token in list(available_formats or []) + list(defaults or []):
            normalized = cls.view_from_legacy_format(str(token))

            if normalized in seen:
                continue

            seen.add(normalized)
            merged.append(normalized)

        return merged

    @classmethod
    def view_from_legacy_format(cls, token: str) -> str:
        lowered = token.strip().lower()

        if lowered == "chart":
            return "chart"

        return lowered

    @classmethod
    def visual_order_for_stack(cls, available_views: list[str]) -> list[str]:
        normalized = {cls.view_from_legacy_format(str(view)) for view in available_views}
        ordered = [view for view in _STACK_VISUAL_PRIORITY if view in normalized]

        for view in sorted(normalized):
            if view not in ordered:
                ordered.append(view)

        return ordered

    @classmethod
    def legacy_preferred_format(cls, selected: str | None) -> str | None:
        if not selected:
            return None

        if selected in {
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
        }:
            return "chart"

        if selected == "canvas":
            return "canvas"

        return selected

    @classmethod
    def legacy_available_formats(cls, views: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()

        for view in views:
            legacy = cls.legacy_preferred_format(view) or view

            if legacy in seen:
                continue

            seen.add(legacy)
            output.append(legacy)

        return output
