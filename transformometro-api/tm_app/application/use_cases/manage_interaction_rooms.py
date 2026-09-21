from __future__ import annotations

from typing import Any

from tm_app.application.security.authorization_policy import TransformometroAuthorizationPolicy
from tm_app.domain.entities.interaction_room import InteractionMessage, InteractionRoom
from tm_app.domain.ports.interaction_room_repository_port import InteractionRoomRepositoryPort
from tm_app.domain.services.interaction_room_rules import (
    normalize_message_content,
    normalize_processo_id,
    normalize_uuid,
)
from tm_app.domain.services.transformometro_task_rules import normalize_user_id

DEFAULT_MESSAGE_LIMIT = 50
MAX_MESSAGE_LIMIT = 100


def _actor(user: Any) -> str:
    return normalize_user_id(str(getattr(user, "id", "") or ""), field="Usuário autenticado")


def _limit(value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_MESSAGE_LIMIT
    return max(1, min(parsed, MAX_MESSAGE_LIMIT))


class InteractionRoomUseCases:
    def __init__(
        self,
        repo: InteractionRoomRepositoryPort,
        policy: TransformometroAuthorizationPolicy | None = None,
    ) -> None:
        self._repo = repo
        self._policy = policy or TransformometroAuthorizationPolicy()

    def open_for_process(self, user: Any, processo_id: str) -> InteractionRoom:
        self._policy.require_access(user)
        actor = _actor(user)
        room = self._repo.get_or_create(
            processo_id=normalize_processo_id(processo_id),
            created_by_user_id=actor,
        )
        if room is None:
            raise LookupError("Processo não encontrado.")
        confirmed = self._repo.get(room.id)
        if confirmed is None or confirmed.processo_id != room.processo_id:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def get_room(self, user: Any, room_id: str) -> InteractionRoom:
        self._policy.require_access(user)
        room = self._repo.get(normalize_uuid(room_id, label="A sala"))
        if room is None:
            raise LookupError("Sala não encontrada.")
        return room

    def list_rooms(self, user: Any) -> list[InteractionRoom]:
        self._policy.require_access(user)
        return self._repo.list_rooms()

    def list_messages(self, user: Any, room_id: str, *, limit: int = DEFAULT_MESSAGE_LIMIT) -> dict[str, Any]:
        self._policy.require_access(user)
        room = self.get_room(user, room_id)
        messages, has_more = self._repo.list_messages(room.id, limit=_limit(limit))
        return {
            "items": [item.to_dict() for item in messages],
            "has_more": has_more,
        }

    def post_message(self, user: Any, room_id: str, content: str) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        text = normalize_message_content(content)
        room = self.get_room(user, room_id)
        created = self._repo.add_message(room_id=room.id, author_user_id=actor, content=text)
        confirmed = self._repo.get_message(created.id)
        if confirmed is None or confirmed.content != text or confirmed.author_user_id != actor:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed
