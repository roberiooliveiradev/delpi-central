"""Conteúdo declarativo da análise estruturada de turno — bundle ``turn_analysis``."""

from __future__ import annotations

import json

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)

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
        grounding_status: str = "ungrounded",
        last_result_excerpt: dict | None = None,
        turn_grounding_stage: str | None = None,
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
            groundingStatus=str(grounding_status or "ungrounded").strip() or "ungrounded",
            turnGroundingStage=str(turn_grounding_stage or "unavailable").strip()
            or "unavailable",
            lastResultExcerpt=cls.format_last_result_excerpt(last_result_excerpt),
        )

    @classmethod
    def format_last_result_excerpt(cls, excerpt: dict | None) -> str:
        if not isinstance(excerpt, dict) or not excerpt:
            return "(nenhum)"

        payload = {
            key: excerpt.get(key)
            for key in (
                "operationId",
                "profileKey",
                "entity",
                "presentationType",
                "title",
                "rowCount",
                "topKeys",
                "keysByComponentType",
                "preview",
            )
            if excerpt.get(key) is not None
        }

        if not payload:
            return "(nenhum)"

        preview = payload.get("preview")

        if isinstance(preview, str):
            max_chars = ChatTurnGroundingContentService.max_preview_chars()

            if max_chars > 0 and len(preview) > max_chars:
                payload["preview"] = f"{preview[:max_chars]}\n…"

        return json.dumps(payload, ensure_ascii=False, indent=2)

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

    @classmethod
    def dispatch_intents(cls) -> frozenset[str]:
        raw = ChatAssistantContentService.list(_BUNDLE, "dispatchIntents")
        return frozenset(
            str(item).strip().lower().replace("-", "_")
            for item in raw
            if str(item).strip()
        )

    @classmethod
    def dispatch_intent_aliases(cls) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "dispatchIntentAliases")
        if not isinstance(node, dict):
            return {}
        out: dict[str, str] = {}
        for key, value in node.items():
            k = str(key or "").strip().lower().replace("-", "_")
            v = str(value or "").strip().lower().replace("-", "_")
            if k and v:
                out[k] = v
        return out
