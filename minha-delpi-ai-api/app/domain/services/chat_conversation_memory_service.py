"""Orquestração da memória de sessão (entidades, preferências, lousa, ações)."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from app.domain.services.chat_conversation_memory_extractor import (
    ChatConversationMemoryExtractor,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


class ChatConversationMemoryService:
    @classmethod
    def build_pre_turn(
        cls,
        *,
        message: str,
        previous_messages: list[Any] | None,
        session_memory_service=None,
        session_id: UUID | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
        attachments: list | None = None,
        previous_agent_id: str | None = None,
    ) -> dict:
        snapshot = ChatWorkingMemoryService.build_pre_turn_snapshot(
            message=message,
            previous_messages=previous_messages,
        )

        if session_memory_service and session_id:
            snapshot = session_memory_service.apply_to_pre_turn(
                session_id=session_id,
                snapshot=snapshot,
                message=message,
            )

        snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
            snapshot,
            previous_messages=previous_messages,
            attachments=attachments,
            agent_id=agent_id,
            project_id=project_id,
        )

        snapshot = cls._apply_selective_clear(message, snapshot)
        snapshot = cls._handle_agent_switch(
            snapshot,
            current_agent_id=agent_id,
            previous_agent_id=previous_agent_id,
        )

        resolved, used = ChatReferenceResolutionService.resolve_from_snapshot(
            message,
            snapshot,
        )
        existing_used = list(snapshot.get("usedMemoryKeys") or [])
        merged_used = list(dict.fromkeys(existing_used + used))

        snapshot["resolvedReferences"] = resolved
        snapshot["usedMemoryKeys"] = merged_used
        snapshot["memoryUsed"] = bool(
            merged_used
            or snapshot.get("lastEntities")
            or snapshot.get("behaviorInstructions")
        )
        snapshot["preferencesApplied"] = cls._preferences_applied(snapshot)

        ambiguity = ChatReferenceResolutionService.detect_ambiguity(message, snapshot)

        if ambiguity:
            snapshot["memoryAmbiguity"] = ambiguity

        return snapshot

    @classmethod
    def build_post_turn(
        cls,
        *,
        message: str,
        previous_messages: list[Any] | None,
        tool_calls: list | None,
        pre_snapshot: dict | None = None,
        attachments: list | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
            pre_snapshot=pre_snapshot,
        )

        snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
            snapshot,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
            attachments=attachments,
            agent_id=agent_id,
            project_id=project_id,
        )

        snapshot["preferencesApplied"] = cls._preferences_applied(snapshot)
        return snapshot

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str:
        return ChatWorkingMemoryService.format_prompt_block(snapshot)

    @classmethod
    def build_context_chips(cls, snapshot: dict | None) -> list[dict[str, str]]:
        chips = ChatWorkingMemoryService.build_context_chips(snapshot)

        if not snapshot:
            return chips

        entities = snapshot.get("lastEntities") or {}
        period = str(entities.get("period") or "").strip()

        if period and not any(chip.get("kind") == "period" for chip in chips):
            label = cls._period_label(period)
            chips.append({"label": label, "kind": "period", "value": period})

        canvas = snapshot.get("canvas") or {}

        if isinstance(canvas, dict) and canvas.get("active"):
            title = str(canvas.get("title") or "Lousa").strip()
            chips.append({"label": f"Lousa: {title[:40]}", "kind": "canvas", "value": "active"})

        return chips

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict:
        base = ChatWorkingMemoryService.compact_for_admin_debug(snapshot)

        if not snapshot:
            return base

        base["memoryUsed"] = bool(snapshot.get("memoryUsed"))
        base["preferencesApplied"] = snapshot.get("preferencesApplied") or []
        base["lastAction"] = snapshot.get("lastAction")
        base["lastPresentation"] = snapshot.get("lastPresentation")
        base["canvas"] = snapshot.get("canvas")
        base["lastAttachment"] = snapshot.get("lastAttachment")
        base["memoryAmbiguity"] = snapshot.get("memoryAmbiguity")
        base["agentContextReset"] = bool(snapshot.get("agentContextReset"))

        return base

    @classmethod
    def _preferences_applied(cls, snapshot: dict) -> list[str]:
        applied: list[str] = []
        behavior = snapshot.get("behaviorInstructions") or {}

        if behavior.get("responseFormat") == "table":
            applied.append("format=table")

        if behavior.get("tone") == "direct":
            applied.append("tone=direct")
        elif behavior.get("tone") == "simple":
            applied.append("tone=simple")
        elif behavior.get("tone") == "formal":
            applied.append("tone=formal")

        if behavior.get("answerLength") == "short":
            applied.append("answerLength=short")

        if behavior.get("finalVersionOnly") == "true":
            applied.append("correctionMode=final_only")

        email_prefs = snapshot.get("emailPreferences") or {}

        for key, active in email_prefs.items():
            if active:
                applied.append(f"email:{key}")

        correction_prefs = snapshot.get("textCorrectionPreferences") or {}

        for key, active in correction_prefs.items():
            if active:
                applied.append(f"textCorrection:{key}")

        return applied

    @classmethod
    def _apply_selective_clear(cls, message: str, snapshot: dict) -> dict:
        result = dict(snapshot)
        normalized = (message or "").strip().lower()
        cleared: list[str] = []
        entities = dict(result.get("lastEntities") or {})
        behavior = dict(result.get("behaviorInstructions") or {})

        if re.search(r"esque.{0,40}produto", normalized):
            entities.pop("productCode", None)
            cleared.append("productCode")

        if re.search(r"esque.{0,40}filial", normalized):
            entities.pop("branch", None)
            cleared.append("branch")

        if re.search(r"esque.{0,40}per[ií]odo", normalized):
            entities.pop("period", None)
            cleared.append("period")

        if re.search(
            r"\bn[aã]o\s+use\s+mais\b.*\bprefer",
            normalized,
        ) or re.search(r"\bremov(a|e)\b.*\bprefer", normalized):
            behavior = {}
            cleared.append("behaviorInstructions")

        if cleared:
            result["lastEntities"] = entities
            result["behaviorInstructions"] = behavior
            result["selectiveMemoryCleared"] = cleared

        return result

    @classmethod
    def _handle_agent_switch(
        cls,
        snapshot: dict,
        *,
        current_agent_id: str | None,
        previous_agent_id: str | None,
    ) -> dict:
        result = dict(snapshot)
        stored = str(previous_agent_id or result.get("activeAgentId") or "").strip()
        current = str(current_agent_id or "").strip()

        if stored and current and stored != current:
            result.pop("lastAction", None)
            result["agentContextReset"] = True
            result["agentSwitchNote"] = (
                "Agente alterado: a última consulta operacional não foi reaproveitada."
            )

        if current:
            result["activeAgentId"] = current

        return result

    @staticmethod
    def _period_label(period: str) -> str:
        labels = {
            "last_30_days": "Últimos 30 dias",
            "last_7_days": "Últimos 7 dias",
            "last_month": "Último mês",
            "current_month": "Este mês",
        }

        return labels.get(period, period)
