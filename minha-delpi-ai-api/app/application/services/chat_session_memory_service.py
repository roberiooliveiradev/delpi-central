"""Memória de sessão persistida (Fase 4 — contexto entre reloads)."""

from __future__ import annotations

import re
from uuid import UUID

from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


class ChatSessionMemoryService:
    _CLEAR_CONTEXT_RE = re.compile(
        r"(?:desconsidere|ignore|esqueça|esqueca|limpe|limpar|resete|reinicie)"
        r".{0,80}"
        r"(?:produto|filial|prefer[eê]ncias?|contexto|mem[oó]ria|conversa|lousa|assunto)",
        re.IGNORECASE | re.DOTALL,
    )
    _CLEAR_FULL_PHRASES = (
        "começar do zero",
        "comecar do zero",
        "trocar de assunto",
        "limpe o contexto",
        "limpar o contexto",
        "limpe a lousa",
        "limpar a lousa",
    )

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
                "lastEntities": {},
                "behaviorInstructions": {},
                "persistedMemoryApplied": False,
                "persistedMemoryCleared": True,
            }

        overlay = self.repository.load_active_overlay(session_id)

        if overlay.get("cleared"):
            cleared_snapshot = {
                **snapshot,
                "lastEntities": {},
                "behaviorInstructions": {},
                "persistedMemoryApplied": False,
                "persistedMemoryCleared": True,
            }
            return cleared_snapshot

        merged = self._merge_overlay(snapshot, overlay)

        if overlay.get("lastEntities") or overlay.get("behaviorInstructions"):
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

        self.repository.sync_from_snapshot(
            session_id,
            snapshot,
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

        if cls._CLEAR_CONTEXT_RE.search(text):
            return True

        if any(phrase in lowered for phrase in cls._CLEAR_FULL_PHRASES):
            return True

        return (
            "desconsidere" in lowered
            and any(token in lowered for token in ("produto", "filial", "prefer", "contexto"))
        )

    @classmethod
    def _merge_overlay(cls, snapshot: dict, overlay: dict) -> dict:
        result = dict(snapshot)
        entities = dict(result.get("lastEntities") or {})
        behavior = dict(result.get("behaviorInstructions") or {})

        for key, value in (overlay.get("lastEntities") or {}).items():
            if value and not entities.get(key):
                entities[key] = value

        for key, value in (overlay.get("behaviorInstructions") or {}).items():
            if value and not behavior.get(key):
                behavior[key] = value

        result["lastEntities"] = entities
        result["behaviorInstructions"] = behavior
        return ChatUserContextItemService.merge_items_into_snapshot(
            result,
            overlay.get("userContextItems"),
        )

    def compact_for_admin_debug(self, snapshot: dict | None) -> dict:
        base = snapshot or {}
        return {
            "persisted": bool(base.get("persistedMemoryApplied")),
            "clearedThisTurn": bool(base.get("persistedMemoryCleared")),
        }
