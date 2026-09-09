"""Policies declarativas do Presentation Composer (skip/invoke/budgets)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "presentation_composer_policies"


class PresentationComposerPolicyService:
    """Decide se o LLM composer deve rodar — thresholds só no content JSON."""

    @classmethod
    def budgets(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "budgets")
        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def max_user_excerpt_chars(cls) -> int:
        raw = cls.budgets().get("maxUserExcerptChars", 400)
        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 400

    @classmethod
    def max_repair_attempts(cls) -> int:
        raw = cls.budgets().get("maxRepairAttempts", 2)
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def should_invoke(
        cls,
        *,
        summary: dict[str, Any] | None,
        intent: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> bool:
        if not isinstance(summary, dict):
            return False

        skip = ChatAssistantContentService.get_node(_BUNDLE, "skip")
        invoke = ChatAssistantContentService.get_node(_BUNDLE, "invoke")
        if not isinstance(skip, dict):
            skip = {}
        if not isinstance(invoke, dict):
            invoke = {}

        bind_confidence = cls._as_float(summary.get("bindConfidence"), default=0.0)
        spec_applied = bool(summary.get("specApplied"))

        skip_applied = cls._as_float(
            skip.get("whenSpecAppliedAndBindConfidenceAtLeast"),
            default=0.72,
        )
        if spec_applied and bind_confidence >= skip_applied:
            return False

        skip_explicit = cls._as_float(
            skip.get("whenExplicitIntentAndBindConfidenceAtLeast"),
            default=0.85,
        )
        if cls._has_explicit_intent(intent) and bind_confidence >= skip_explicit:
            return False

        if invoke.get("whenNeedsComposerFlag", True) and bool(summary.get("needsComposer")):
            return True

        if invoke.get("whenComplexConstraintsPresent", True) and cls._has_complex_constraints(
            constraints
        ):
            return True

        if cls._is_ambiguous_multi_slot(profile, invoke):
            return True

        return False

    @classmethod
    def _has_explicit_intent(cls, intent: dict[str, Any] | None) -> bool:
        if not isinstance(intent, dict):
            return False
        if intent.get("mark"):
            return True
        dims = intent.get("dimensionConcepts") or intent.get("dimension_concepts") or []
        if isinstance(dims, list) and len(dims) > 0:
            return True
        if intent.get("measureConcept") or intent.get("measure_concept"):
            return True
        if intent.get("paletteFamily") or intent.get("palette_family"):
            return True
        return False

    @classmethod
    def _has_complex_constraints(cls, constraints: dict[str, Any] | None) -> bool:
        if not isinstance(constraints, dict) or not constraints:
            return False
        # Nested multi-view / density / canvas / multi-field requests.
        for key in ("fields", "density", "preferCanvas", "kpiMeasures", "dashboardPanels"):
            value = constraints.get(key)
            if value in (None, "", [], {}):
                continue
            if isinstance(value, list) and len(value) >= 2:
                return True
            if isinstance(value, (dict, bool, str, int, float)):
                return True
        return False

    @classmethod
    def _is_ambiguous_multi_slot(
        cls,
        profile: dict[str, Any] | None,
        invoke: dict[str, Any],
    ) -> bool:
        if not isinstance(profile, dict):
            return False
        min_dims = int(invoke.get("minDimensionCandidatesForAmbiguity") or 2)
        min_measures = int(invoke.get("minMeasureCandidatesForAmbiguity") or 2)
        dims = profile.get("dimensionCandidates") or []
        measures = profile.get("measureCandidates") or []
        return (
            isinstance(dims, list)
            and isinstance(measures, list)
            and len(dims) >= min_dims
            and len(measures) >= min_measures
        )

    @classmethod
    def _as_float(cls, value: Any, *, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
