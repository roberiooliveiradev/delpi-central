from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

from tm_app.core.serialize import json_safe
from tm_app.application.services.collaboration_presence_service import (
    CollaborationPresenceService,
)
from tm_app.application.services.transformometro_realtime_notify import (
    notify_presence_updated,
)

logger = logging.getLogger(__name__)


class TransformometroRealtimeCollaborationHandler:
    """Processa mensagens WebSocket de presença e travas colaborativas."""

    def __init__(self, service: CollaborationPresenceService | None = None) -> None:
        self._service = service or CollaborationPresenceService()

    async def handle_message(
        self,
        websocket: WebSocket,
        *,
        raw_message: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        user_name: str | None,
        user_email: str | None,
    ) -> None:
        stripped = raw_message.strip()
        if stripped.lower() == "ping":
            await websocket.send_json({"type": "pong"})
            return

        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return

        if not isinstance(data, dict):
            return

        msg_type = data.get("type")
        section_key = str(data.get("sectionKey") or data.get("section_key") or "")

        try:
            if msg_type == "presence.request":
                await self._send_presence(websocket, entity_type=entity_type, entity_id=entity_id)
                return

            if msg_type == "presence.heartbeat":
                mode = str(data.get("mode") or "viewing")
                self._service.heartbeat(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    section_key=section_key,
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                    mode=mode,
                )
                self._broadcast_presence(entity_type, entity_id)
                return

            if msg_type == "presence.leave":
                self._clear_user_presence(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id,
                )
                return

            if msg_type == "lock.acquire":
                result = self._service.acquire_lock(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    section_key=section_key,
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                )
                await websocket.send_json(
                    json_safe(
                        {
                            "type": "lock.result",
                            "entityType": entity_type,
                            "entityId": entity_id,
                            "sectionKey": section_key,
                            "data": result,
                        }
                    )
                )
                self._broadcast_presence(entity_type, entity_id)
                return

            if msg_type == "lock.release":
                self._service.release_lock(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    section_key=section_key,
                    user_id=user_id,
                )
                self._broadcast_presence(entity_type, entity_id)
                return
        except ValueError as exc:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": str(exc),
                    "sectionKey": section_key or None,
                }
            )
        except Exception:  # noqa: BLE001
            logger.exception("transformometro_realtime_message_failed")
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Falha ao processar mensagem em tempo real.",
                    "sectionKey": section_key or None,
                }
            )

    async def handle_disconnect(
        self,
        *,
        entity_type: str,
        entity_id: str,
        user_id: str,
    ) -> None:
        self._clear_user_presence(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
        )

    def _clear_user_presence(
        self,
        *,
        entity_type: str,
        entity_id: str,
        user_id: str,
    ) -> None:
        try:
            self._service.clear_user_presence(
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
            )
        except ValueError:
            return
        self._broadcast_presence(entity_type, entity_id)

    async def _send_presence(
        self,
        websocket: WebSocket,
        *,
        entity_type: str,
        entity_id: str,
    ) -> None:
        payload = self._service.list_presence(entity_type=entity_type, entity_id=entity_id)
        await websocket.send_json(
            json_safe(
                {
                    "type": "presence.updated",
                    "entityType": entity_type,
                    "entityId": entity_id,
                    "data": payload,
                }
            )
        )

    @staticmethod
    def _broadcast_presence(entity_type: str, entity_id: str) -> None:
        try:
            payload = CollaborationPresenceService().list_presence(
                entity_type=entity_type,
                entity_id=entity_id,
            )
        except ValueError:
            return
        notify_presence_updated(
            entity_type=entity_type,
            entity_id=entity_id,
            presence=payload,
        )


transformometro_realtime_collaboration = TransformometroRealtimeCollaborationHandler()
