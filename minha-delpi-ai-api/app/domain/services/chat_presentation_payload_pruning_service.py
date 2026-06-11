"""Playbook 13 P6-A/B — omite visuais suprimidos do payload (MFE render-only)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_evidence_first_layout_service import (
    ChatPresentationEvidenceFirstLayoutService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_VISUAL_TOKEN_TO_KEY: dict[str, str] = {
    "kpi": "kpiPresentation",
    "tree": "treePresentation",
    "chart": "chartPresentation",
    "dashboard": "dashboardPresentation",
    "table": "tablePresentation",
}

_NULLABLE_PRESENTATION_KEYS = (
    *_VISUAL_TOKEN_TO_KEY.values(),
    "presentation",
    "profileTablePresentation",
    "inspectionTablePresentation",
    "storyPresentation",
)


class ChatPresentationPayloadPruningService:
    """Remove campos de apresentação que não devem chegar ao MFE neste turno."""

    @classmethod
    def prune(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        plan = cls._resolve_stack_plan(metadata)

        if not isinstance(plan, dict):
            return

        cls._ensure_tail_visual_policy(metadata, plan)
        cls._prune_null_presentations(metadata)
        cls._prune_structure_duplicate_tables(metadata)
        cls._prune_allowlisted_visuals(metadata, plan)
        cls._attach_render_hints(metadata, plan)

    @classmethod
    def _ensure_tail_visual_policy(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> None:
        policy = str(plan.get("tailVisualPolicy") or "").strip().lower()

        if policy:
            return

        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            plan["tailVisualPolicy"] = "allowlist"
            return

        plan["tailVisualPolicy"] = "legacy"

    @classmethod
    def _prune_allowlisted_visuals(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> None:
        policy = str(plan.get("tailVisualPolicy") or "").strip().lower()

        if policy != "allowlist":
            return

        allowed = {
            str(token).strip().lower()
            for token in (plan.get("tailVisualOrder") or [])
            if str(token).strip()
        }
        suppressed: list[str] = []

        for token, key in _VISUAL_TOKEN_TO_KEY.items():
            if token in allowed:
                continue

            if metadata.pop(key, None) is not None:
                suppressed.append(token)

        cls._prune_primary_presentation(metadata, allowed, suppressed)

        hints = plan.get("renderHints")

        if not isinstance(hints, dict):
            hints = {}
            plan["renderHints"] = hints

        if suppressed:
            existing = hints.get("suppressedKinds")

            if isinstance(existing, list):
                merged = list(dict.fromkeys([*existing, *suppressed]))
            else:
                merged = list(dict.fromkeys(suppressed))

            hints["suppressedKinds"] = merged

    @classmethod
    def _prune_null_presentations(cls, metadata: dict[str, Any]) -> None:
        for key in _NULLABLE_PRESENTATION_KEYS:
            if metadata.get(key) is None:
                metadata.pop(key, None)

        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            filtered = [item for item in bundled if item is not None]

            if filtered:
                metadata["tablePresentations"] = filtered
            else:
                metadata.pop("tablePresentations", None)

    @classmethod
    def _prune_structure_duplicate_tables(cls, metadata: dict[str, Any]) -> None:
        from app.domain.services.chat_presentation_structure_dedup_service import (
            ChatPresentationStructureDedupService,
        )

        if not metadata.get("structureDedupApplied"):
            return

        if not ChatPresentationStructureDedupService.metadata_has_tree(metadata):
            return

        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            filtered = ChatPresentationStructureDedupService._filter_table_list(bundled)

            if filtered:
                metadata["tablePresentations"] = filtered
            else:
                metadata.pop("tablePresentations", None)

        for key in (
            "tablePresentation",
            "profileTablePresentation",
            "inspectionTablePresentation",
            "presentation",
        ):
            presentation = metadata.get(key)

            if ChatPresentationStructureDedupService.is_hierarchy_duplicate_table(presentation):
                metadata.pop(key, None)

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
    def _prune_primary_presentation(
        cls,
        metadata: dict[str, Any],
        allowed: set[str],
        suppressed: list[str],
    ) -> None:
        presentation = metadata.get("presentation")

        if not isinstance(presentation, dict):
            return

        presentation_type = str(presentation.get("type") or "").strip().lower()

        if presentation_type == "dashboard" and "dashboard" not in allowed:
            metadata.pop("presentation", None)
            suppressed.append("dashboard")

    @classmethod
    def _resolve_text_render_mode(cls, metadata: dict[str, Any]) -> str:
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if explicit in {"text", "topics"}:
            return "full"

        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            return "compact"

        if ChatRichPresentationTextService.should_compact_metadata_text(metadata):
            return "compact"

        return "full"

    @classmethod
    def _attach_render_hints(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> None:
        hints = plan.get("renderHints")

        if not isinstance(hints, dict):
            hints = {}
            plan["renderHints"] = hints

        hints["tailVisualPolicy"] = str(plan.get("tailVisualPolicy") or "legacy")
        hints["textRenderMode"] = cls._resolve_text_render_mode(metadata)
