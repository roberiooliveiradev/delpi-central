"""Contexto de grounding de parâmetros de tools no turno atual."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Iterator


_grounding_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "chat_tool_grounding_context",
    default=None,
)


class ChatToolGroundingContextService:
    @classmethod
    @contextmanager
    def scope(
        cls,
        *,
        message: str | None = None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> Iterator[None]:
        payload = {
            "message": message,
            "conversation_context": conversation_context,
            "previous_messages": previous_messages,
            "memory_snapshot": memory_snapshot if isinstance(memory_snapshot, dict) else None,
        }
        token: Token = _grounding_context.set(payload)

        try:
            yield
        finally:
            _grounding_context.reset(token)

    @classmethod
    def current(cls) -> dict[str, Any]:
        value = _grounding_context.get()

        return dict(value) if isinstance(value, dict) else {}

    @classmethod
    def current_memory_snapshot(cls) -> dict | None:
        snapshot = cls.current().get("memory_snapshot")

        return snapshot if isinstance(snapshot, dict) else None

    @classmethod
    def current_message(cls) -> str | None:
        message = cls.current().get("message")

        return str(message) if message not in (None, "") else None

    @classmethod
    def current_previous_messages(cls) -> list | None:
        previous = cls.current().get("previous_messages")

        return previous if isinstance(previous, list) else None

    @classmethod
    def current_conversation_context(cls) -> str | None:
        value = cls.current().get("conversation_context")

        return str(value) if value not in (None, "") else None
