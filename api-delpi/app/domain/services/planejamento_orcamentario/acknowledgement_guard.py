from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetGuidanceAcknowledgementRequiredError,
    BudgetGuidanceNotPublishedError,
)
from app.domain.services.planejamento_orcamentario.exercise_state_service import (
    modules_unlocked_for_exercise,
)


class GuidanceAckLookup(Protocol):
    def get_active_exercise(self) -> dict[str, Any] | None: ...

    def get_current_published_guidance(self, exercise_id: str) -> dict[str, Any] | None: ...

    def get_acknowledgement(
        self, *, user_sub: str, guidance_version_id: str
    ) -> dict[str, Any] | None: ...


class BudgetGuidanceAcknowledgementGuard:
    """Guard reutilizável: usuário confirmou a versão vigente das orientações?"""

    def __init__(self, repository: GuidanceAckLookup) -> None:
        self._repository = repository

    def evaluate(self, *, user_sub: str) -> dict[str, Any]:
        exercise = self._repository.get_active_exercise()
        if not exercise:
            return {
                "exercise": None,
                "guidance": None,
                "acknowledged": False,
                "modules_unlocked": False,
                "reason": "no_active_exercise",
            }
        guidance = self._repository.get_current_published_guidance(str(exercise["id"]))
        if not guidance:
            return {
                "exercise": exercise,
                "guidance": None,
                "acknowledged": False,
                "modules_unlocked": False,
                "reason": "guidance_not_published",
            }
        ack = self._repository.get_acknowledgement(
            user_sub=user_sub,
            guidance_version_id=str(guidance["id"]),
        )
        acknowledged = ack is not None
        unlocked = (
            acknowledged
            and modules_unlocked_for_exercise(str(exercise.get("status") or ""))
        )
        return {
            "exercise": exercise,
            "guidance": guidance,
            "acknowledgement": ack,
            "acknowledged": acknowledged,
            "modules_unlocked": unlocked,
            "reason": None if unlocked else ("ack_required" if not acknowledged else "exercise_not_open"),
        }

    def assert_modules_unlocked(self, *, user_sub: str) -> dict[str, Any]:
        state = self.evaluate(user_sub=user_sub)
        if state.get("reason") == "guidance_not_published":
            raise BudgetGuidanceNotPublishedError(
                "Orientações ainda não publicadas para o exercício ativo."
            )
        if not state.get("acknowledged"):
            raise BudgetGuidanceAcknowledgementRequiredError(
                "Confirmação de leitura das orientações vigente é obrigatória."
            )
        if not state.get("modules_unlocked"):
            raise BudgetGuidanceAcknowledgementRequiredError(
                "Módulos indisponíveis para o status atual do exercício."
            )
        return state
