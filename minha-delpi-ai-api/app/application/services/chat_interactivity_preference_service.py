"""Preferências de chips por sessão — Playbook 07 Fase 2."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort

logger = logging.getLogger("minha-delpi-ai-api.interactivity")

_USAGE_KEY = "interactivityUsage"
_MAX_BOOST = 24


class ChatInteractivityPreferenceService:
    @classmethod
    def usage_from_workspace(cls, workspace_context: dict | None) -> dict[str, int]:
        working = (workspace_context or {}).get("workingMemory") or {}
        behavior = working.get("behaviorInstructions") or {}

        if not isinstance(behavior, dict):
            return {}

        return cls._parse_usage(behavior.get(_USAGE_KEY))

    @classmethod
    def rank_boost(cls, label: str, usage: dict[str, int] | None) -> int:
        if not label or not usage:
            return 0

        clicks = int(usage.get(label) or 0)

        if clicks <= 0:
            return 0

        return -min(clicks * 8, _MAX_BOOST)

    @classmethod
    def record_click(
        cls,
        *,
        repository: ChatSessionMemoryRepositoryPort | None,
        session_id: str | UUID | None,
        label: str,
    ) -> None:
        if not repository or not session_id:
            return

        token = str(label or "").strip()

        if not token:
            return

        try:
            session_uuid = session_id if isinstance(session_id, UUID) else UUID(str(session_id))
        except (TypeError, ValueError):
            return

        overlay = repository.load_active_overlay(session_uuid)
        behavior = dict(overlay.get("behaviorInstructions") or {})
        usage = cls._parse_usage(behavior.get(_USAGE_KEY))
        usage[token] = int(usage.get(token) or 0) + 1
        behavior[_USAGE_KEY] = json.dumps(usage, ensure_ascii=False)

        repository.sync_from_snapshot(
            session_uuid,
            {
                "operationalFocus": overlay.get("operationalFocus") or {},
                "behaviorInstructions": behavior,
            },
        )

        logger.info(
            "interactivity_preference label=%s count=%s session_id=%s",
            token,
            usage[token],
            session_uuid,
        )

    @classmethod
    def _parse_usage(cls, raw: Any) -> dict[str, int]:
        if raw in (None, "", {}):
            return {}

        payload = raw

        if isinstance(raw, str):
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return {}

        if not isinstance(payload, dict):
            return {}

        output: dict[str, int] = {}

        for key, value in payload.items():
            label = str(key or "").strip()

            if not label:
                continue

            try:
                output[label] = max(0, int(value))
            except (TypeError, ValueError):
                continue

        return output
