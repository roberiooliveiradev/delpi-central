"""Playbook 13 P6-C — plano de renderização consumido pelo MFE (render-only)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_evidence_first_layout_service import (
    ChatPresentationEvidenceFirstLayoutService,
)

_VISUAL_TOKEN_TO_KEY: dict[str, str] = {
    "kpi": "kpiPresentation",
    "tree": "treePresentation",
    "chart": "chartPresentation",
    "dashboard": "dashboardPresentation",
    "table": "tablePresentation",
}

_TABLE_BUNDLE_SOURCES = (
    "tablePresentations",
    "tablePresentation",
    "profileTablePresentation",
    "inspectionTablePresentation",
)


class ChatPresentationRenderPlanService:
    @classmethod
    def build(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        decision = metadata.get("presentationDecision")
        layout_mode = "stack"

        if isinstance(decision, dict):
            layout_mode = str(decision.get("layoutMode") or "stack").strip() or "stack"

        stack_plan = cls._resolve_stack_plan(metadata)
        segments: list[dict[str, Any]] = []

        if layout_mode == "stack" and isinstance(stack_plan, dict):
            segments.extend(cls._stack_segments(metadata, stack_plan))
        else:
            segments.extend(cls._single_view_segments(metadata, decision))

        metadata["renderPlan"] = {
            "version": 1,
            "layoutMode": layout_mode,
            "segments": segments,
        }

        if not segments and cls._has_text_presentation(metadata):
            metadata["renderPlan"]["segments"] = [
                {"kind": "markdown", "slot": "lead", "source": "textPresentation"},
            ]

    @classmethod
    def _resolve_stack_plan(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        plan = metadata.get("stackPresentationPlan")

        if isinstance(plan, dict):
            return plan

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            nested = decision.get("stackPresentationPlan")

            if isinstance(nested, dict):
                return nested

        return None

    @classmethod
    def _stack_segments(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []

        if cls._should_include_decision(metadata):
            segments.append({"kind": "decision", "slot": "lead", "source": "dataAnswer"})

        narrative_order = plan.get("narrativeOrder") or []

        for slot in narrative_order:
            token = str(slot).strip()

            if token == "lead" and cls._has_text_presentation(metadata):
                segments.append(
                    {"kind": "markdown", "slot": "lead", "source": "textPresentation"},
                )
                continue

            if token == "highlights" and cls._markdown_has_highlights(metadata):
                segments.append(
                    {"kind": "markdown", "slot": "highlights", "source": "textPresentation"},
                )
                continue

            if token == "attention" and cls._markdown_has_attention(metadata):
                segments.append(
                    {"kind": "markdown", "slot": "attention", "source": "textPresentation"},
                )
                continue

            if token == "profileTables" and cls._has_table_bundle(metadata):
                segments.append(
                    {
                        "kind": "table",
                        "slot": "profileTables",
                        "source": "tablePresentations",
                    },
                )
                continue

            if token == "operationalTables" and cls._has_table_bundle(metadata):
                segments.append(
                    {
                        "kind": "table",
                        "slot": "operationalTables",
                        "source": "tablePresentations",
                    },
                )
                continue

            if token == "tailVisuals":
                segments.extend(cls._tail_visual_segments(metadata, plan))

        return segments

    @classmethod
    def _resolve_visual_source(cls, metadata: dict[str, Any], token: str) -> str | None:
        normalized = str(token or "").strip().lower()
        source = _VISUAL_TOKEN_TO_KEY.get(normalized)

        if source and metadata.get(source):
            return source

        if normalized == "table":
            bulk = metadata.get("tablePresentations")

            if isinstance(bulk, list) and bulk:
                return "tablePresentations"

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            presentation_type = str(presentation.get("type") or "").strip().lower()

            if presentation_type == normalized:
                return "presentation"

        return None

    @classmethod
    def _tail_visual_segments(
        cls,
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []

        for token in plan.get("tailVisualOrder") or []:
            normalized = str(token).strip().lower()
            source = cls._resolve_visual_source(metadata, normalized)

            if not source:
                continue

            segments.append(
                {
                    "kind": normalized,
                    "slot": "tailVisuals",
                    "source": source,
                },
            )

        return segments

    @classmethod
    def _single_view_segments(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []

        if cls._should_include_decision(metadata):
            segments.append({"kind": "decision", "slot": "lead", "source": "dataAnswer"})

        selected = str((decision or {}).get("selected") or "").strip().lower()

        if selected == "canvas" and cls._has_text_presentation(metadata):
            segments.append({"kind": "markdown", "slot": "lead", "source": "textPresentation"})
            return segments

        if cls._has_text_presentation(metadata) and selected in {"", "text"}:
            segments.append({"kind": "markdown", "slot": "lead", "source": "textPresentation"})

        if selected in _VISUAL_TOKEN_TO_KEY:
            source = cls._resolve_visual_source(metadata, selected)

            if not source and selected == "dashboard":
                source = cls._resolve_visual_source(metadata, "kpi")

                if source:
                    selected = "kpi"

            if source:
                if selected == "table" and cls._table_bundle_count(metadata) >= 2:
                    segments.append(
                        {
                            "kind": "table",
                            "slot": "operationalTables",
                            "source": "tablePresentations",
                        },
                    )
                else:
                    segments.append({"kind": selected, "slot": "primary", "source": source})

        return segments

    @classmethod
    def _should_include_decision(cls, metadata: dict[str, Any]) -> bool:
        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            return False

        data_answer = metadata.get("dataAnswer")

        return isinstance(data_answer, dict) and isinstance(data_answer.get("summary"), dict)

    @classmethod
    def _has_text_presentation(cls, metadata: dict[str, Any]) -> bool:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return False

        return bool(str(text_presentation.get("markdown") or "").strip())

    @classmethod
    def _table_bundle_count(cls, metadata: dict[str, Any]) -> int:
        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            return sum(
                1
                for item in bulk
                if isinstance(item, dict) and item.get("type") == "table"
            )

        return 0

    @classmethod
    def _has_table_bundle(cls, metadata: dict[str, Any]) -> bool:
        for key in _TABLE_BUNDLE_SOURCES:
            presentation = metadata.get(key)

            if isinstance(presentation, list) and presentation:
                return True

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                return True

        return False

    @classmethod
    def _markdown_has_highlights(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_presentation_stack_order_service import (
            ChatPresentationStackOrderService,
        )

        return ChatPresentationStackOrderService._markdown_has_highlights(metadata)

    @classmethod
    def _markdown_has_attention(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_presentation_stack_order_service import (
            ChatPresentationStackOrderService,
        )

        return ChatPresentationStackOrderService._markdown_has_attention(metadata)
