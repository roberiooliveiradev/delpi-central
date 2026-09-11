"""J-R9 — single semantic ownership matrix (Action Catalog is action authority)."""

from __future__ import annotations

from typing import Any


class ChatSemanticAuthorityOwnershipService:
    """Declares canonical owners so family mappers cannot select routes/actions.

    KEEP transversal layers (understanding / family triage / LLM decision / planner).
    REMOVE/DEMOTE ``_TOKEN_RULES`` and JSON keyword trees as route/catalogToken selectors.
    """

    ACTION_SELECTION_OWNER = "openapi_action_catalog"

    @classmethod
    def ownership_matrix(cls) -> dict[str, Any]:
        return {
            "turnUnderstanding": "ChatTurnUnderstandingService",
            "intentFamilyTriage": "ChatIntentRouterService",
            "turnDecision": "ChatTurnAnalysisService",
            "taskPlan": "ChatTaskPlannerService",
            "actionSelection": cls.ACTION_SELECTION_OWNER,
            "familyMappersRole": "removed_as_selection_authority",
            "cutover": "J-R9",
        }

    @classmethod
    def family_mapper_may_select_route(cls) -> bool:
        """TOKEN_RULES / catalogToken / productionOperationalKind must not pick routes."""
        return False

    @classmethod
    def family_intent_resolve_enabled(cls) -> bool:
        """Live resolve that materializes catalogToken/kind for selection is off."""
        return False
