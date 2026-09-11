"""E2.S4 — map Turn Understanding goals → department KPI match."""

from __future__ import annotations

from app.domain.entities.turn_understanding import TurnUnderstanding
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
    DepartmentKpiMatch,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class TurnUnderstandingKpiIntentMapperService:
    """Derives DepartmentKpiMatch from TU prose (high-confidence tokens only)."""

    # J-R9 — emptied: catalogToken/domainPrefix must not be a parallel selection authority.
    _TOKEN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @classmethod
    def from_understanding(cls, contract: TurnUnderstanding | None) -> DepartmentKpiMatch | None:
        from app.domain.services.chat_semantic_authority_ownership_service import (
            ChatSemanticAuthorityOwnershipService,
        )

        if not ChatSemanticAuthorityOwnershipService.family_intent_resolve_enabled():
            return None

        if contract is None or not contract.goals:
            return None

        user_goal = ChatMessageNormalizationService.normalize_for_matching(
            str(contract.user_goal or "")
        )
        if not user_goal:
            return None

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        if ChatProductQueryIntentService.extract_product_code(user_goal):
            return None

        path_token = cls._path_token_from_prose(user_goal)
        if not path_token:
            for goal in contract.goals:
                path_token = cls._path_token_from_prose(str(goal.intent or ""))
                if path_token:
                    break
        if not path_token:
            return None

        return cls._hydrate_match(path_token)

    @classmethod
    def from_message(cls, message: str) -> DepartmentKpiMatch | None:
        from app.domain.services.chat_turn_understanding_service import (
            ChatTurnUnderstandingService,
        )

        return cls.from_understanding(ChatTurnUnderstandingService.analyze(message))

    @classmethod
    def _path_token_from_prose(cls, prose: str) -> str | None:
        from app.domain.services.chat_semantic_authority_ownership_service import (
            ChatSemanticAuthorityOwnershipService,
        )

        if not ChatSemanticAuthorityOwnershipService.family_intent_resolve_enabled():
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(prose)
        if not normalized:
            return None
        for path_token, needles in cls._TOKEN_RULES:
            if any(needle in normalized for needle in needles):
                return path_token
        return None

    @classmethod
    def _hydrate_match(cls, path_token: str) -> DepartmentKpiMatch | None:
        token = str(path_token or "").strip()
        if not token:
            return None

        for domain_prefix, path, _keywords, _excludes, label, _mode, branch_default in (
            ChatDepartmentKpiIntentService._rules()
        ):
            if path != token:
                continue
            return DepartmentKpiMatch(
                path_token=path,
                domain_prefix=domain_prefix,
                reason=ExternalActionResponseContentService.format(
                    "selectionReasons",
                    "departmentKpiLabeled",
                    label=label,
                ),
                operation_hint=label,
                branch_default=branch_default,
            )
        return None
