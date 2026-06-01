"""Telemetria de interatividade — Playbook 07 Fase 5."""

from __future__ import annotations

import logging

logger = logging.getLogger("minha-delpi-ai-api.interactivity")


class ChatInteractivityTelemetryService:
    @classmethod
    def log_from_metadata(cls, metadata: dict) -> None:
        payload = metadata.get("interactivity")

        if not isinstance(payload, dict):
            return

        logger.info(
            "interactivity primary=%s more_groups=%s intent=%s",
            len(payload.get("suggestions") or []),
            len((payload.get("moreSuggestions") or {}).keys()),
            payload.get("sourceIntent"),
        )
