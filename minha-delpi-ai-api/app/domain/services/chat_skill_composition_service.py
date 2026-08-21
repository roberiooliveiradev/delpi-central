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


_SPECIALIZED_FLAGS = frozenset(
    {
        "sqlAuthoring",
        "drawingAnalysis",
        "technicalDescription",
    }
)


class ChatSkillCompositionService:
    @classmethod
    def flag_for_skill_key(cls, skill_key: str) -> str | None:
        key = str(skill_key or "").strip().lower()
        return _SKILL_KEY_TO_FLAG.get(key)

    @classmethod
    def infer_heuristic_skill_keys(
        cls,
        message: str | None = None,
        *,
        attachment_ids: list | None = None,
    ) -> tuple[str, ...]:
        text = str(message or "").strip()
        if not text:
            return ()

        keys: list[str] = []

        from app.domain.services.chat_drawing_intent_service import (
            ChatDrawingIntentService,
        )

        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )

        if ChatDrawingIntentService.is_drawing_analysis_request(
            text,
            attachment_ids=attachment_ids,
        ):
            keys.append("drawing-analysis")
            normalized = ChatMessageNormalizationService.normalize_for_matching(text)
            if "norma" in normalized:
                keys.append("company-knowledge")

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(text):
            keys.append("company-knowledge")

        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        if ChatSqlIntentService.is_sql_conversation_turn(text):
            keys.append("sql")

        return tuple(keys)

    @classmethod
    def resolve_loaded_skills(
        cls,
        *,
        enabled_skills: dict[str, Any] | None,
        skills_to_load: list[str] | tuple[str, ...] | None = None,
        analysis_ran: bool = False,
        message: str | None = None,
        attachment_ids: list | None = None,
    ) -> dict[str, bool]:
        """Retorna o dict de flags efetivas para o prompt do turno.

        Loaded = interseção (enabled ∩ (heurística ∪ analysis.skillsToLoad)).
        Sem mensagem e sem análise: mantém o mapa enabled (compatibilidade).
        """
        enabled = {
            str(key): bool(value)
            for key, value in dict(enabled_skills or {}).items()
            if bool(value)
        }

        requested = [
            str(item).strip().lower()
            for item in (skills_to_load or ())
            if str(item).strip()
        ]
        for key in cls.infer_heuristic_skill_keys(
            message,
            attachment_ids=attachment_ids,
        ):
            if key not in requested:
                requested.append(key)

        if not requested:
            if analysis_ran:
                return {}
            if not str(message or "").strip():
                return enabled
            return {
                flag: True
                for flag in enabled
                if flag not in _SPECIALIZED_FLAGS
            }

        max_skills = ChatTurnAnalysisContentService.max_skills_to_load()
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

    @classmethod
    def loaded_skill_keys(
        cls,
        loaded_flags: dict[str, bool] | None,
    ) -> list[str]:
        inverse = {flag: key for key, flag in _SKILL_KEY_TO_FLAG.items() if "-" in key or key == "sql"}
        # Prefer canonical registry keys.
        canonical = {
            "sqlAuthoring": "sql",
            "companyKnowledge": "company-knowledge",
            "technicalDescription": "technical-description",
            "drawingAnalysis": "drawing-analysis",
        }
        keys: list[str] = []
        for flag, on in dict(loaded_flags or {}).items():
            if not on:
                continue
            key = canonical.get(flag) or inverse.get(flag)
            if key and key not in keys:
                keys.append(key)
        return keys
