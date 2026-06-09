"""Recomendações automáticas de formato — Playbook 09 Fase 5."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)

_CHART_SELECTED = frozenset(
    {
        "chart",
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


class ChatPresentationRecommendationService:
    @classmethod
    def _view_labels(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(
            "presenter_content",
            "presentationRecommendation",
            "viewLabels",
        )

    @classmethod
    def _view_queries(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(
            "presenter_content",
            "presentationRecommendation",
            "viewQueries",
        )

    @classmethod
    def _reasons(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(
            "presenter_content",
            "presentationRecommendation",
            "reasons",
        )

    @classmethod
    def _efficiency_hints(cls) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(
                "presenter_content",
                "presentationRecommendation",
                "efficiencyHints",
            )
        )

    @classmethod
    def build(
        cls,
        *,
        decision: dict[str, Any] | None,
        user_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        if not isinstance(decision, dict):
            return []

        selected = str(decision.get("selected") or "").strip().lower()
        available = {
            str(view or "").strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        }

        if not selected or not available:
            return []

        rows = cls._rows_from_metadata(metadata)
        shape = decision.get("dataShape")

        if isinstance(shape, dict) and shape.get("rows"):
            ideal = ChatPresentationDataShapeAnalyzer.analyze(rows=rows).get("recommended")
        else:
            ideal = ChatPresentationDataShapeAnalyzer.analyze(rows=rows).get("recommended")

        ideal = str(ideal or "").strip().lower()
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())

        output: list[dict[str, str]] = []
        seen: set[str] = set()
        reasons = cls._reasons()

        def add(view: str, reason: str) -> None:
            token = str(view or "").strip().lower()

            if not token or token == selected or token in seen:
                return

            if not cls._view_available(token, available):
                return

            label = cls._view_labels().get(token, f"Ver como {token}")

            output.append(
                {
                    "view": token,
                    "label": label,
                    "reason": reason,
                    "query": cls._view_queries().get(token, f"mostre em {token}"),
                }
            )
            seen.add(token)

        if ideal and ideal != selected:
            add(ideal, cls._reason_for_view(ideal, decision))

        if message and any(hint in message for hint in cls._efficiency_hints()):
            if selected in {"scatter", "chart", "bar_chart"}:
                add(
                    "horizontal_bar",
                    reasons.get("efficiencyHorizontalBar", ""),
                )

            if selected == "table" and ideal in {"", "table", "horizontal_bar"}:
                add(
                    "horizontal_bar",
                    reasons.get("efficiencyFactoryBars", ""),
                )

        if selected == "table" and "line_chart" in available:
            shape_dict = shape if isinstance(shape, dict) else {}

            if shape_dict.get("hasDate") and shape_dict.get("hasNumeric"):
                add("line_chart", reasons.get("timeSeriesLineChart", ""))

        if selected in _CHART_SELECTED and "table" in available:
            row_count = int((shape or {}).get("rows") or len(rows) or 0)

            if row_count >= 8:
                add("table", reasons.get("chartManyPointsTable", ""))

        if (
            isinstance(metadata, dict)
            and isinstance(metadata.get("presentation"), dict)
            and metadata["presentation"].get("type") == "dashboard"
            and selected != "dashboard"
        ):
            add("dashboard", reasons.get("dashboardConsolidated", ""))

        cls._apply_entity_family_rules(
            decision=decision,
            metadata=metadata,
            shape=shape if isinstance(shape, dict) else {},
            add=add,
        )

        return output[:3]

    @classmethod
    def _apply_entity_family_rules(
        cls,
        *,
        decision: dict[str, Any],
        metadata: dict[str, Any] | None,
        shape: dict[str, Any],
        add,
    ) -> None:
        profile_key = str(decision.get("presentationProfileKey") or "").strip()

        if not profile_key:
            from app.domain.services.chat_presentation_profile_service import (
                ChatPresentationProfileService,
            )

            path = str((metadata or {}).get("path") or "")
            entity = str((metadata or {}).get("entity") or "")
            profile = ChatPresentationProfileService.resolve_profile(path, entity)
            profile_key = str(profile.get("profileKey") or "").strip()

        if not profile_key:
            return

        families = ChatAssistantContentService.get_node(
            "presenter_content",
            "presentationRecommendation",
            "entityFamilies",
        )
        reasons = cls._reasons()

        if not isinstance(families, dict):
            return

        selected = str(decision.get("selected") or "").strip().lower()
        available = {
            str(view or "").strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        }

        for family_config in families.values():
            if not isinstance(family_config, dict):
                continue

            profile_keys = [
                str(key or "").strip()
                for key in (family_config.get("profileKeys") or [])
                if str(key or "").strip()
            ]

            if profile_key not in profile_keys:
                continue

            for rule in family_config.get("suggestions") or []:
                if not isinstance(rule, dict):
                    continue

                when_selected = str(rule.get("whenSelected") or "").strip().lower()

                if when_selected and when_selected != selected:
                    continue

                requires_shape = str(rule.get("requiresShape") or "").strip()

                if requires_shape and not shape.get(requires_shape):
                    continue

                view = str(rule.get("view") or "").strip().lower()
                reason_key = str(rule.get("reasonKey") or "").strip()
                reason = reasons.get(reason_key, "")

                if view and view in available:
                    add(view, reason)

            break

    @classmethod
    def _rows_from_metadata(cls, metadata: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not isinstance(metadata, dict):
            return []

        for key in ("tablePresentation", "presentation", "chartPresentation"):
            block = metadata.get(key)

            if not isinstance(block, dict):
                continue

            if block.get("type") == "table":
                rows = block.get("rows") or []

                return [row for row in rows if isinstance(row, dict)]

            if block.get("type") == "chart":
                data = block.get("data") or []

                return [row for row in data if isinstance(row, dict)]

        return []

    @classmethod
    def _view_available(cls, view: str, available: set[str]) -> bool:
        if view in available:
            return True

        if view in {"line_chart", "area_chart", "bar_chart", "horizontal_bar", "donut", "scatter"}:
            return "chart" in available or view in available

        return False

    @classmethod
    def _reason_for_view(cls, view: str, decision: dict[str, Any]) -> str:
        shape = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}
        fallback = str(decision.get("reason") or "").strip()
        reasons = cls._reasons()

        if view == "line_chart" and shape.get("hasDate"):
            return reasons.get("dataShapeLineChart", fallback)

        if view == "horizontal_bar" and int(shape.get("categoryCardinality") or 0) > 6:
            return reasons.get("dataShapeHorizontalBar", fallback)

        if view == "donut":
            return reasons.get("dataShapeDonut", fallback)

        if view == "table" and fallback:
            return reasons.get("dataShapeTableFallback", fallback)

        if view == "dashboard":
            return reasons.get("dashboardConsolidated", fallback)

        return fallback or reasons.get("genericAlternateView", "")
