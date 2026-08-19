"""Acesso à sala de interação — gate de existência (RBAC na borda HTTP/WS)."""

from __future__ import annotations

from uuid import UUID

from commercial_app.domain.entities.interaction_room import InteractionRoom
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


class InteractionRoomAccessService:
    """
    Quem tem ``commercial.access`` (validado em HTTP/WS) acessa todas as salas.
    Domínio só garante que a sala existe e não foi removida.
    ``interaction_room_members`` guarda ``last_read_at`` e participantes, não ACL.
    """

    def __init__(self, rooms: InteractionRoomRepositoryPort) -> None:
        self._rooms = rooms

    def require_room_exists(self, room_id: UUID) -> InteractionRoom:
        room = self._rooms.get_by_id(room_id)
        if room is None:
            raise LookupError(InteractionRoomContentService.error("roomNotFound"))
        return room

    def room_exists(self, room_id: UUID) -> bool:
        return self._rooms.get_by_id(room_id) is not None
