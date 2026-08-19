"""Publica mensagem system e emite WS (thread + inbox) sem acoplar o use case."""

from __future__ import annotations

import logging

from commercial_app.application.services.commercial_realtime_notify import (
    notify_interaction_room_activity,
)
from commercial_app.application.use_cases.post_system_message import (
    PostSystemMessageInput,
    PostSystemMessageUseCase,
)
from commercial_app.domain.entities.interaction_room import InteractionMessage

logger = logging.getLogger(__name__)


class NotifyingPostSystemMessageUseCase:
    def __init__(self, inner: PostSystemMessageUseCase) -> None:
        self._inner = inner

    def execute(self, request: PostSystemMessageInput) -> InteractionMessage:
        message = self._inner.execute(request)
        try:
            notify_interaction_room_activity(
                reason="created",
                room_id=str(message.room_id),
                message=message,
            )
        except Exception:  # noqa: BLE001 — notificação não pode falhar o publish
            logger.exception("system_message_notify_failed")
        return message
