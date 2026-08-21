"""Análise estruturada de turno — JSON (clarify | execute | narrate)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_turn_analysis_content_service import (
    ChatTurnAnalysisContentService,
)

logger = logging.getLogger("minha-delpi-ai-api.chat.turn-analysis")

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


@dataclass(frozen=True)
class ChatTurnAnalysisResult:
    decision: str
    intent: str | None = None
    sub_intent: str | None = None
    skills_to_load: tuple[str, ...] = ()
    action_ids: tuple[str, ...] = ()
    clarify_key: str | None = None
    reason: str = "turn_analysis"
    raw: dict[str, Any] = field(default_factory=dict)
    source: str = "llm"

    def to_metadata(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "intent": self.intent,
            "subIntent": self.sub_intent,
            "skillsToLoad": list(self.skills_to_load),
            "actionIds": list(self.action_ids),
            "clarifyKey": self.clarify_key,
            "reason": self.reason,
            "source": self.source,
        }

    def direct_answer(self) -> str | None:
        if self.decision != "clarify":
            return None
        return ChatTurnAnalysisContentService.clarify_answer(self.clarify_key) or None


class ChatTurnAnalysisService:
    @classmethod
    def safe_clarify(
        cls,
        *,
        clarify_key: str | None = "default",
        reason: str = "turn_analysis_fallback",
        source: str = "fallback",
    ) -> ChatTurnAnalysisResult:
        return ChatTurnAnalysisResult(
            decision="clarify",
            clarify_key=clarify_key or "default",
            reason=reason,
            source=source,
        )

    @classmethod
    def parse(
        cls,
        raw_text: str,
        *,
        allowed_action_ids: set[str] | None = None,
        allowed_skill_keys: set[str] | None = None,
    ) -> ChatTurnAnalysisResult | None:
        payload = cls._extract_json_object(raw_text)
        if not isinstance(payload, dict):
            return None

        decisions = ChatTurnAnalysisContentService.allowed_decisions()
        decision = str(payload.get("decision") or "").strip().lower()
        if decision not in decisions:
            return None

        max_actions = ChatTurnAnalysisContentService.max_action_ids()
        max_skills = ChatTurnAnalysisContentService.max_skills_to_load()
        allowed_actions = {
            str(item).strip() for item in (allowed_action_ids or set()) if str(item).strip()
        }
        allowed_skills = {
            str(item).strip().lower()
            for item in (allowed_skill_keys or set())
            if str(item).strip()
        }

        action_ids: list[str] = []
        for item in payload.get("actionIds") or []:
            action_id = str(item or "").strip()
            if not action_id:
                continue
            if allowed_actions and action_id not in allowed_actions:
                continue
            if action_id not in action_ids:
                action_ids.append(action_id)
            if len(action_ids) >= max_actions:
                break

        skills: list[str] = []
        for item in payload.get("skillsToLoad") or []:
            key = str(item or "").strip().lower()
            if not key:
                continue
            if allowed_skills and key not in allowed_skills:
                continue
            if key not in skills:
                skills.append(key)
            if len(skills) >= max_skills:
                break

        if decision == "execute" and not action_ids and not skills:
            # Execute sem plano útil → clarificar em vez de narrar CoT.
            return cls.safe_clarify(
                clarify_key=str(payload.get("clarifyKey") or "default") or "default",
                reason="execute_without_plan",
                source="parse",
            )

        if decision != "execute":
            action_ids = []

        clarify_key = str(payload.get("clarifyKey") or "").strip() or None
        if decision == "clarify" and not clarify_key:
            clarify_key = "default"

        return ChatTurnAnalysisResult(
            decision=decision,
            intent=str(payload.get("intent") or "").strip() or None,
            sub_intent=str(payload.get("subIntent") or "").strip() or None,
            skills_to_load=tuple(skills),
            action_ids=tuple(action_ids),
            clarify_key=clarify_key,
            reason=str(payload.get("reason") or "turn_analysis").strip() or "turn_analysis",
            raw=payload,
            source="llm",
        )

    @classmethod
    def analyze(
        cls,
        *,
        llm_gateway: LlmGatewayPort,
        message: str,
        response_mode: str,
        heuristic_intent: str,
        heuristic_confidence: float,
        heuristic_reason: str,
        skills_catalog_lines: list[str],
        actions_catalog_lines: list[str],
        allowed_action_ids: set[str] | None = None,
        allowed_skill_keys: set[str] | None = None,
    ) -> ChatTurnAnalysisResult:
        system = ChatTurnAnalysisContentService.system_prompt()
        user = ChatTurnAnalysisContentService.user_prompt(
            message=message,
            response_mode=response_mode,
            heuristic_intent=heuristic_intent,
            heuristic_confidence=heuristic_confidence,
            heuristic_reason=heuristic_reason,
            skills_catalog="\n".join(skills_catalog_lines) or "(nenhuma)",
            actions_catalog="\n".join(actions_catalog_lines) or "(nenhuma)",
        )

        try:
            raw = llm_gateway.generate(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
            )
        except Exception:
            logger.exception("turn_analysis_llm_failed")
            return cls.safe_clarify(reason="turn_analysis_llm_error")

        parsed = cls.parse(
            str(raw or ""),
            allowed_action_ids=allowed_action_ids,
            allowed_skill_keys=allowed_skill_keys,
        )
        if parsed is None:
            logger.warning("turn_analysis_parse_failed")
            return cls.safe_clarify(reason="turn_analysis_parse_failed")

        return parsed

    @classmethod
    def _extract_json_object(cls, raw_text: str) -> dict[str, Any] | None:
        text = str(raw_text or "").strip()
        if not text:
            return None

        candidates = [text]
        match = _JSON_OBJECT_RE.search(text)
        if match:
            candidates.append(match.group(0))

        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data

        return None
