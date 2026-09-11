"""Memória de sessão persistida (Fase 4 — contexto entre reloads)."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)

_LAST_ACTION_KEYS = (
    "name",
    "params",
    "path",
    "actionId",
    "operationId",
    "resultType",
    "apiRouteDomain",
)


class ChatSessionMemoryService:
    @classmethod
    def _clear_context_re(cls):
        return ChatMemoryIntentContentService.compile_pattern("sessionClear", "pattern")

    @classmethod
    def _clear_full_phrases(cls) -> tuple[str, ...]:
        return ChatMemoryIntentContentService.string_list("sessionClear", "fullPhrases")

    def __init__(self, repository: ChatSessionMemoryRepositoryPort | None = None):
        self.repository = repository

    def apply_to_pre_turn(
        self,
        *,
        session_id: UUID | None,
        snapshot: dict,
        message: str,
    ) -> dict:
        if not self.repository or not session_id:
            return snapshot

        if self.is_clear_context_request(message):
            self.repository.deactivate_all(session_id)
            return {
                **snapshot,
                "operationalFocus": {},
                "behaviorInstructions": {},
                "lastAction": None,
                "persistedMemoryApplied": False,
                "persistedMemoryCleared": True,
            }

        overlay = self.repository.load_active_overlay(session_id)

        if overlay.get("cleared"):
            cleared_snapshot = {
                **snapshot,
                "operationalFocus": {},
                "behaviorInstructions": {},
                "lastAction": None,
                "persistedMemoryApplied": False,
                "persistedMemoryCleared": True,
            }
            return cleared_snapshot

        merged = self._merge_overlay(snapshot, overlay)

        if (
            overlay.get("operationalFocus")
            or overlay.get("behaviorInstructions")
            or overlay.get("lastAction")
        ):
            merged["persistedMemoryApplied"] = True

        return merged

    def persist_post_turn(
        self,
        *,
        session_id: UUID | None,
        snapshot: dict,
        source_message_id: UUID | None = None,
    ) -> None:
        if not self.repository or not session_id or not snapshot:
            return

        if snapshot.get("persistedMemoryCleared"):
            return

        payload = dict(snapshot)
        payload["lastAction"] = self.sanitize_last_action(payload.get("lastAction"))

        self.repository.sync_from_snapshot(
            session_id,
            payload,
            source_message_id=source_message_id,
        )

    def persist_from_workspace(
        self,
        *,
        session_id: UUID | None,
        workspace_context: dict | None,
        source_message_id: UUID | None = None,
    ) -> None:
        snapshot = (workspace_context or {}).get("workingMemory")

        if not isinstance(snapshot, dict):
            return

        self.persist_post_turn(
            session_id=session_id,
            snapshot=snapshot,
            source_message_id=source_message_id,
        )

    @classmethod
    def is_clear_context_request(cls, message: str) -> bool:
        text = str(message or "").strip()

        if not text:
            return False

        lowered = text.lower()

        if re.search(r"esque.{0,40}produto", lowered) and "contexto" not in lowered and "memoria" not in lowered and "memória" not in lowered:
            return False

        if cls._clear_context_re().search(text):
            return True

        if any(phrase in lowered for phrase in cls._clear_full_phrases()):
            return True

        return (
            "desconsidere" in lowered
            and any(token in lowered for token in ("produto", "filial", "prefer", "contexto"))
        )

    @classmethod
    def _merge_overlay(cls, snapshot: dict, overlay: dict) -> dict:
        result = dict(snapshot)
        behavior = dict(result.get("behaviorInstructions") or {})
        overlay_behavior = overlay.get("behaviorInstructions") or {}
        response_format = str(overlay_behavior.get("responseFormat") or "").strip().lower()

        if response_format:
            behavior["responseFormat"] = response_format

        overlay_scope = str(overlay_behavior.get("scope") or "").strip().lower()

        if overlay_scope:
            behavior["scope"] = overlay_scope

        for key, value in overlay_behavior.items():
            if not value:
                continue

            if key in {"responseFormat", "scope"}:
                continue

            if not behavior.get(key):
                behavior[key] = value

        result["behaviorInstructions"] = behavior
        entities = dict(result.get("operationalFocus") or {})

        for key, value in (overlay.get("operationalFocus") or {}).items():
            token = str(value or "").strip()

            if token and not entities.get(key):
                entities[key] = token

        result["operationalFocus"] = entities

        overlay_last = cls.sanitize_last_action(overlay.get("lastAction"))
        existing_last = result.get("lastAction")
        if overlay_last and (
            not isinstance(existing_last, dict) or not existing_last
        ):
            result["lastAction"] = overlay_last

        return ChatUserContextItemService.merge_items_into_snapshot(
            result,
            overlay.get("userContextItems"),
        )

    @classmethod
    def sanitize_last_action(cls, raw: Any) -> dict[str, Any] | None:
        """Bounded lastAction for Postgres overlay (E3.S8) — no raw tool payload."""
        if not isinstance(raw, dict):
            return None
        out: dict[str, Any] = {}
        for key in _LAST_ACTION_KEYS:
            if key not in raw:
                continue
            value = raw.get(key)
            if value in (None, "", []):
                continue
            out[key] = value
        params = out.get("params")
        if isinstance(params, dict):
            capped: dict[str, Any] = {}
            for index, (pkey, pval) in enumerate(params.items()):
                if index >= 24:
                    break
                capped[str(pkey)] = pval
            out["params"] = capped
        elif "params" in out:
            del out["params"]
        if not (out.get("name") or out.get("actionId") or out.get("path")):
            return None
        return out

    def compact_for_admin_debug(self, snapshot: dict | None) -> dict:
        base = snapshot or {}
        return {
            "persisted": bool(base.get("persistedMemoryApplied")),
            "clearedThisTurn": bool(base.get("persistedMemoryCleared")),
        }
