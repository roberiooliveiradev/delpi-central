"""Pontos de commit incremental durante o streaming do chat."""

from __future__ import annotations

from typing import Any


class ChatStreamCheckpointService:
    CHECKPOINT_EVENT_TYPES = frozenset(
        {
            "user_persisted",
            "assistant_pending",
            "done",
        }
    )

    @classmethod
    def should_commit(cls, event: dict[str, Any]) -> bool:
        return str(event.get("type") or "") in cls.CHECKPOINT_EVENT_TYPES
