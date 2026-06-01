"""Telemetria de erros e vazios — Playbook 06 Fase 5."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("minha-delpi-ai-api.error-handling")


class ChatErrorHandlingTelemetryService:
    @classmethod
    def log_classification(cls, metadata: dict) -> None:
        payload = metadata.get("errorHandling")

        if not isinstance(payload, dict):
            return

        logger.info(
            "error_handling type=%s severity=%s recoverable=%s records=%s api_failed=%s",
            payload.get("type"),
            payload.get("severity"),
            payload.get("recoverable"),
            payload.get("records"),
            payload.get("apiFailed"),
        )
