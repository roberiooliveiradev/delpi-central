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

        plan = cls._ensure_stack_plan(metadata)

        cls._ensure_tail_visual_policy(metadata, plan)
        cls._prune_null_presentations(metadata)
        cls._prune_structure_duplicate_tables(metadata)

        if cls._layout_mode(metadata) == "stack":
            cls._prune_table_primary_dashboard(metadata, plan)
            cls._prune_allowlisted_visuals(metadata, plan)
        else:
            cls._trim_stack_plan_for_single_layout(plan)

        cls._attach_render_hints(metadata, plan)

    @classmethod
    def _layout_mode(cls, metadata: dict[str, Any]) -> str:
        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            return str(decision.get("layoutMode") or "single").strip().lower() or "single"

        return "single"

    @classmethod
    def _trim_stack_plan_for_single_layout(cls, plan: dict[str, Any]) -> None:
        for key in (
            "narrativeOrder",
            "tailVisualOrder",
            "tableRoleOrder",
            "profileFirst",
            "highlightsAfterProfile",
            "attentionLast",
        ):
            plan.pop(key, None)

        plan["layoutMode"] = "single"

    @classmethod
    def _ensure_stack_plan(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        plan = cls._resolve_stack_plan(metadata)

        if isinstance(plan, dict):
            if metadata.get("stackPresentationPlan") is not plan:
                metadata["stackPresentationPlan"] = plan
            return plan

        plan = {}
        metadata["stackPresentationPlan"] = plan
        return plan

    @classmethod
    def _ensure_tail_visual_policy(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> None:
        policy = str(plan.get("tailVisualPolicy") or "").strip().lower()

        if policy:
            return

        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            plan["tailVisualPolicy"] = "allowlist"
            return

        plan["tailVisualPolicy"] = "allowlist"

    @classmethod
    def _prune_table_primary_dashboard(
        cls,
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> None:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )
        from app.domain.services.chat_presentation_rich_stack_policy_service import (
            ChatPresentationRichStackPolicyService,
        )

        path = str(metadata.get("path") or "")
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        profile = ChatPresentationProfileService.resolve_profile(path, entity)

        if not ChatPresentationRichStackPolicyService._should_omit_dashboard_for_table_primary(
            metadata,
            profile,
        ):
            return

        if metadata.pop("dashboardPresentation", None) is None:
            return

        tail_order = plan.get("tailVisualOrder")

        if isinstance(tail_order, list):
            plan["tailVisualOrder"] = [
                token
                for token in tail_order
                if str(token).strip().lower() != "dashboard"
            ]

        hints = plan.get("renderHints")

        if not isinstance(hints, dict):
            hints = {}
            plan["renderHints"] = hints

        existing = hints.get("suppressedKinds")

        if isinstance(existing, list):
            merged = list(dict.fromkeys([*existing, "dashboard"]))
        else:
            merged = ["dashboard"]

        hints["suppressedKinds"] = merged

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        for key in ("availableViews", "visualOrder"):
            values = decision.get(key)

            if not isinstance(values, list):
                continue

            decision[key] = [
                item for item in values if str(item).strip().lower() != "dashboard"
            ]

        available_formats = metadata.get("availableFormats")

        if isinstance(available_formats, list):
            metadata["availableFormats"] = [
                item for item in available_formats if str(item).strip().lower() != "dashboard"
            ]

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
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if explicit in _VISUAL_TOKEN_TO_KEY:
            allowed.add(explicit)

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            selected = str(decision.get("selected") or "").strip().lower()

            if selected in _VISUAL_TOKEN_TO_KEY:
                allowed.add(selected)
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

        prefers_table = ChatPresentationStructureDedupService._explicit_table_session(metadata)

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
            if key == "presentation" and prefers_table:
                continue

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

        if presentation_type in _VISUAL_TOKEN_TO_KEY and presentation_type not in allowed:
            metadata.pop("presentation", None)
            suppressed.append(presentation_type)

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

        hints["tailVisualPolicy"] = str(plan.get("tailVisualPolicy") or "allowlist")
        hints["textRenderMode"] = cls._resolve_text_render_mode(metadata)
