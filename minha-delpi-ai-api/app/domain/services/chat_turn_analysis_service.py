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
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingStatus

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
    def should_analyze(
        cls,
        *,
        response_mode: str | None,
        heuristic_intent: str | None = None,
        heuristic_sub_intent: str | None = None,
        heuristic_decision: str | None = None,
        heuristic_reason: str | None = None,
        heuristic_confidence: float | None = None,
        pipeline_stages: list[str] | None = None,
        has_direct_answer: bool = False,
        turn_analysis_enabled: bool = True,
        tools_already_skipped: bool = False,
    ) -> bool:
        if not turn_analysis_enabled:
            return False

        if has_direct_answer:
            return False

        if tools_already_skipped:
            return False

        mode = str(response_mode or "normal").strip().lower() or "normal"
        disabled_modes = {
            str(item).strip().lower()
            for item in (ChatTurnAnalysisContentService.gate_setting("disabledResponseModes") or [])
            if str(item).strip()
        }
        if mode in disabled_modes:
            return False

        stages = {str(stage).strip() for stage in (pipeline_stages or []) if str(stage).strip()}
        skip_stages = {
            str(item).strip()
            for item in (ChatTurnAnalysisContentService.gate_setting("skipStages") or [])
            if str(item).strip()
        }
        if stages.intersection(skip_stages):
            return False

        intent = str(heuristic_intent or "").strip()
        skip_intents = {
            str(item).strip()
            for item in (ChatTurnAnalysisContentService.gate_setting("skipIntents") or [])
            if str(item).strip()
        }
        if intent in skip_intents:
            return False

        skip_sub_intents = {
            str(item).strip()
            for item in (ChatTurnAnalysisContentService.gate_setting("skipSubIntents") or [])
            if str(item).strip()
        }
        sub_intent = str(heuristic_sub_intent or "").strip()
        if sub_intent and sub_intent in skip_sub_intents:
            return False

        reason = str(heuristic_reason or "").strip()
        decision = str(heuristic_decision or "").strip()
        open_reasons = {
            str(item).strip()
            for item in (ChatTurnAnalysisContentService.gate_setting("openOnReasons") or [])
            if str(item).strip()
        }
        open_decisions = {
            str(item).strip()
            for item in (ChatTurnAnalysisContentService.gate_setting("openOnDecisions") or [])
            if str(item).strip()
        }

        if reason in open_reasons or decision in open_decisions:
            return True

        try:
            threshold = float(
                ChatTurnAnalysisContentService.gate_setting(
                    "openOnLowConfidenceBelow",
                    0.7,
                )
            )
        except (TypeError, ValueError):
            threshold = 0.7

        if heuristic_confidence is not None and float(heuristic_confidence) < threshold:
            if intent in {"mixed_task", "llm_general", "operational_query"}:
                return True

        return False

    @classmethod
    def safe_clarify(
        cls,
        *,
        clarify_key: str | None = "default",
        reason: str = "turn_analysis_fallback",
        source: str = "fallback",
        grounding_status: str | None = None,
    ) -> ChatTurnAnalysisResult:
        if cls._is_grounded_status(grounding_status):
            return ChatTurnAnalysisResult(
                decision="narrate",
                reason="grounded_forbid_generic_clarify",
                source=source,
            )

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
        grounding_status: str | None = None,
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
            if cls._is_grounded_status(grounding_status):
                return ChatTurnAnalysisResult(
                    decision="narrate",
                    reason="grounded_execute_without_plan",
                    source="parse",
                )

            # Execute sem plano útil → clarificar em vez de narrar CoT.
            return cls.safe_clarify(
                clarify_key=str(payload.get("clarifyKey") or "default") or "default",
                reason="execute_without_plan",
                source="parse",
                grounding_status=grounding_status,
            )

        if decision != "execute":
            action_ids = []

        clarify_key = str(payload.get("clarifyKey") or "").strip() or None
        if decision == "clarify" and not clarify_key:
            clarify_key = "default"

        if decision == "clarify" and cls._is_grounded_status(grounding_status):
            return ChatTurnAnalysisResult(
                decision="narrate",
                intent=str(payload.get("intent") or "").strip() or None,
                sub_intent=str(payload.get("subIntent") or "").strip() or None,
                reason="grounded_forbid_generic_clarify",
                raw=payload,
                source="parse",
            )

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
        grounding_status: str | None = None,
        last_result_excerpt: dict | None = None,
        turn_grounding_stage: str | None = None,
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
            grounding_status=str(grounding_status or "ungrounded"),
            last_result_excerpt=last_result_excerpt,
            turn_grounding_stage=turn_grounding_stage,
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
            return cls.safe_clarify(
                reason="turn_analysis_llm_error",
                grounding_status=grounding_status,
            )

        parsed = cls.parse(
            str(raw or ""),
            allowed_action_ids=allowed_action_ids,
            allowed_skill_keys=allowed_skill_keys,
            grounding_status=grounding_status,
        )
        if parsed is None:
            logger.warning("turn_analysis_parse_failed")
            return cls.safe_clarify(
                reason="turn_analysis_parse_failed",
                grounding_status=grounding_status,
            )

        return parsed

    @classmethod
    def _is_grounded_status(cls, grounding_status: str | None) -> bool:
        return (
            str(grounding_status or "").strip().lower()
            == ChatTurnGroundingStatus.GROUNDED.value
        )

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
