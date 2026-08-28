"""Classificador residual de follow-up via port (domain puro — sem HTTP)."""

from __future__ import annotations

from typing import Any, ClassVar

from app.domain.ports.follow_up_turn_classifier_port import FollowUpTurnClassifierPort
from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)


class ChatFollowUpTurnClassifierService:
    _port: ClassVar[FollowUpTurnClassifierPort | None] = None

    @classmethod
    def configure(cls, port: FollowUpTurnClassifierPort | None) -> None:
        cls._port = port

    @classmethod
    def classify(
        cls,
        message: str,
        last_action_summary: dict[str, Any] | None = None,
    ) -> str | None:
        if cls._port is None:
            return None
        try:
            label = cls._port.classify(message, last_action_summary)
        except Exception:
            return None
        normalized = str(label or "").strip()
        if not normalized:
            return None
        allowed = set(ChatFollowUpTurnContentService.classifier_labels())
        return normalized if normalized in allowed else None
