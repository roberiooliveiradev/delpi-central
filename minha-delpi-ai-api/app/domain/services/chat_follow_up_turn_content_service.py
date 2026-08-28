"""Loader canônico — bundle ``follow_up_turn.json``."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "follow_up_turn"


class ChatFollowUpTurnContentService:
    @classmethod
    def decisions(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "followUpDecisions")
            if str(item).strip()
        )

    @classmethod
    def stage_for_decision(cls, decision: str) -> str | None:
        node = ChatAssistantContentService.get_node(_BUNDLE, "stages") or {}
        if not isinstance(node, dict):
            return None
        value = node.get(str(decision or "").strip())
        return str(value).strip() or None if value is not None else None

    @classmethod
    def revise_slot_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "reviseSlotTriggers")
            if str(item).strip()
        )

    @classmethod
    def challenge_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "challengeTriggers")
            if str(item).strip()
        )

    @classmethod
    def narrate_reference_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "narrateReferenceTriggers")
            if str(item).strip()
        )

    @classmethod
    @lru_cache(maxsize=1)
    def branch_typos(cls) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "branchTypos") or {}
        if not isinstance(node, dict):
            return {}
        return {
            str(src).strip().lower(): str(dst).strip().lower()
            for src, dst in node.items()
            if str(src).strip() and str(dst).strip()
        }

    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")
        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")
        return re.compile(str(source), re.IGNORECASE)

    @classmethod
    def normalize_branch_typos(cls, text: str) -> str:
        """Substitui typos de filial sem alterar o restante da mensagem."""
        raw = str(text or "")
        if not raw:
            return raw
        normalized = raw
        for typo, canonical in cls.branch_typos().items():
            if typo == canonical:
                continue
            normalized = re.sub(
                rf"\b{re.escape(typo)}\b",
                canonical,
                normalized,
                flags=re.IGNORECASE,
            )
        return normalized

    @classmethod
    def extract_branch_code(cls, text: str) -> str | None:
        candidate = cls.normalize_branch_typos(text)
        match = cls.compile_pattern("branchWithCode").search(candidate)
        if not match:
            return None
        return str(match.group(1)).zfill(2)

    @classmethod
    def has_branch_trigger_without_code(cls, text: str) -> bool:
        candidate = cls.normalize_branch_typos(text)
        if cls.extract_branch_code(candidate):
            return False
        return bool(cls.compile_pattern("branchTriggerWithoutCode").search(candidate))

    @classmethod
    def topic_switch_markers(cls) -> dict[str, tuple[str, ...]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "topicSwitchMarkers") or {}
        if not isinstance(node, dict):
            return {}
        resolved: dict[str, tuple[str, ...]] = {}
        for domain, markers in node.items():
            if not isinstance(markers, list):
                continue
            cleaned = tuple(str(item).strip().lower() for item in markers if str(item).strip())
            if cleaned:
                resolved[str(domain).strip()] = cleaned
        return resolved

    @classmethod
    def topic_switch_exclude_markers(cls) -> dict[str, tuple[str, ...]]:
        node = (
            ChatAssistantContentService.get_node(
                _BUNDLE, "topicSwitchExcludeWhenLastActionMarkers"
            )
            or {}
        )
        if not isinstance(node, dict):
            return {}
        resolved: dict[str, tuple[str, ...]] = {}
        for domain, markers in node.items():
            if not isinstance(markers, list):
                continue
            cleaned = tuple(str(item).strip().lower() for item in markers if str(item).strip())
            if cleaned:
                resolved[str(domain).strip()] = cleaned
        return resolved

    @classmethod
    def clarify_slot_prompt(cls, slot: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE, "clarifySlotPrompts", slot, default=""
            )
            or ""
        ).strip()

    @classmethod
    def challenge_faithfulness_instruction(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE, "challengeFaithfulness", "instruction", default=""
            )
            or ""
        ).strip()

    @classmethod
    def challenge_suggestions(cls) -> list[dict[str, str]]:
        node = ChatAssistantContentService.get_node(
            _BUNDLE, "challengeFaithfulness", "suggestions"
        )
        suggestions: list[dict[str, str]] = []
        if not isinstance(node, list):
            return suggestions
        for item in node:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()
            if label and query:
                suggestions.append({"label": label, "query": query})
        return suggestions

    @classmethod
    def revise_ack_branch(cls, branch: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "reviseAck",
            "branchTemplate",
            default="Consulta filtrada pela filial {branch}.",
            branch=str(branch or "").strip(),
        )

    @classmethod
    def revise_ack_period(cls, *, start: str, end: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "reviseAck",
            "periodTemplate",
            default="Período mantido: {start} a {end}.",
            start=str(start or "").strip(),
            end=str(end or "").strip(),
        )

    @classmethod
    def message_has_any_trigger(cls, message: str, triggers: tuple[str, ...]) -> bool:
        haystack = str(message or "").strip().lower()
        if not haystack:
            return False
        return any(trigger in haystack for trigger in triggers if trigger)

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.branch_typos.cache_clear()
        cls.compile_pattern.cache_clear()
