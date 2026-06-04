"""Telemetria de aprendizagem contínua (playbook §38) — logs estruturados best-effort."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger("minha-delpi-ai-api.learning.events")


class ChatLearningEventService:
    @staticmethod
    def emit(event_type: str, **payload) -> None:
        if not event_type:
            return

        try:
            body = {"event": event_type, **payload}
            logger.info("learning_event %s", json.dumps(body, default=str, ensure_ascii=False))
        except Exception:
            return
