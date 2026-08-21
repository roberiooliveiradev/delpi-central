"""Composição de skills do turno — habilitadas no agente ≠ carregadas no prompt."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_turn_analysis_content_service import (
    ChatTurnAnalysisContentService,
)

# Mapa skillKey (registry) → flag booleana usada em PromptPolicyService / workspace.
_SKILL_KEY_TO_FLAG: dict[str, str] = {
    "sql": "sqlAuthoring",
    "sql-authoring": "sqlAuthoring",
    "company-knowledge": "companyKnowledge",
    "technical-description": "technicalDescription",
    "drawing-analysis": "drawingAnalysis",
}


class ChatSkillCompositionService:
    @classmethod
    def flag_for_skill_key(cls, skill_key: str) -> str | None:
        key = str(skill_key or "").strip().lower()
        return _SKILL_KEY_TO_FLAG.get(key)

    @classmethod
    def resolve_loaded_skills(
        cls,
        *,
        enabled_skills: dict[str, Any] | None,
        skills_to_load: list[str] | tuple[str, ...] | None = None,
        analysis_ran: bool = False,
    ) -> dict[str, bool]:
        """Retorna o dict de flags efetivas para o prompt do turno.

        - Sem análise: mantém todas as skills habilitadas (comportamento legado).
        - Com análise e ``skillsToLoad``: interseção com habilitadas, limitada.
        - Com análise e lista vazia: nenhuma skill de política no prompt.
        """
        enabled = {
            str(key): bool(value)
            for key, value in dict(enabled_skills or {}).items()
            if bool(value)
        }

        if not analysis_ran:
            return enabled

        max_skills = ChatTurnAnalysisContentService.max_skills_to_load()
        requested = [
            str(item).strip().lower()
            for item in (skills_to_load or ())
            if str(item).strip()
        ]

        if not requested:
            return {}

        loaded: dict[str, bool] = {}
        for skill_key in requested:
            flag = cls.flag_for_skill_key(skill_key)
            if not flag:
                continue
            if not enabled.get(flag):
                continue
            loaded[flag] = True
            if len(loaded) >= max_skills:
                break

        return loaded
