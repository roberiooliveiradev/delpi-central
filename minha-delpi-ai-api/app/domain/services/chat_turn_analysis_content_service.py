"""Conteúdo declarativo da análise estruturada de turno — bundle ``turn_analysis``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "turn_analysis"


class ChatTurnAnalysisContentService:
    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "limits") or {}
        if not isinstance(raw, dict):
            return default
        try:
            return int(raw.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def max_action_ids(cls) -> int:
        return cls.limit_int("maxActionIds", 12)

    @classmethod
    def max_skills_to_load(cls) -> int:
        return cls.limit_int("maxSkillsToLoad", 3)

    @classmethod
    def system_prompt(cls) -> str:
        template = str(
            ChatAssistantContentService.get(_BUNDLE, "systemPrompt", default="") or ""
        ).strip()
        return template.format(
            maxSkills=cls.max_skills_to_load(),
            maxActions=cls.max_action_ids(),
        )

    @classmethod
    def user_prompt(
        cls,
        *,
        message: str,
        response_mode: str,
        heuristic_intent: str,
        heuristic_confidence: float,
        heuristic_reason: str,
        skills_catalog: str,
        actions_catalog: str,
    ) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "userPromptTemplate",
            default="",
            message=message,
            responseMode=response_mode,
            heuristicIntent=heuristic_intent,
            heuristicConfidence=f"{heuristic_confidence:.2f}",
            heuristicReason=heuristic_reason,
            skillsCatalog=skills_catalog or "(nenhuma)",
            actionsCatalog=actions_catalog or "(nenhuma)",
        )

    @classmethod
    def clarify_answer(cls, clarify_key: str | None = None) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "clarifyAnswers") or {}
        if not isinstance(node, dict):
            return ""
        key = str(clarify_key or "default").strip() or "default"
        text = str(node.get(key) or node.get("default") or "").strip()
        return text

    @classmethod
    def gate_setting(cls, key: str, default=None):
        node = ChatAssistantContentService.get_node(_BUNDLE, "gate") or {}
        if not isinstance(node, dict):
            return default
        return node.get(key, default)

    @classmethod
    def allowed_decisions(cls) -> frozenset[str]:
        raw = ChatAssistantContentService.list(_BUNDLE, "decisions")
        return frozenset(str(item).strip() for item in raw if str(item).strip())
