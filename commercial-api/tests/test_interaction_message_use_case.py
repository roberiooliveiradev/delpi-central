from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence
from uuid import UUID, uuid4

import pytest

from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
    PostInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_interaction_rooms import (
    ManageInteractionRoomsUseCase,
    ResolveInteractionRoomInput,
)
from commercial_app.domain.entities.interaction_room import (
    InteractionMention,
    InteractionMessage,
    InteractionPin,
    InteractionReaction,
)
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


class InMemoryInteractionMessageRepo(InteractionMessageRepositoryPort):
    def __init__(self) -> None:
        self.messages: dict[UUID, InteractionMessage] = {}
        self.mentions: dict[UUID, list[InteractionMention]] = {}

    def get_by_id(self, message_id: UUID) -> InteractionMessage | None:
        message = self.messages.get(message_id)
        if message is None:
            return None
        return InteractionMessage(
            id=message.id,
            room_id=message.room_id,
            message_kind=message.message_kind,
            body_text=message.body_text,
            created_at=message.created_at,
            author_user_id=message.author_user_id,
            parent_id=message.parent_id,
            edited_at=message.edited_at,
            deleted_at=message.deleted_at,
            mentions=tuple(self.mentions.get(message.id, ())),
            reactions=message.reactions,
        )

    def list_for_room(
        self,
        *,
        room_id: UUID,
        limit: int = 50,
        before_created_at: datetime | None = None,
        before_id: UUID | None = None,
        query: str | None = None,
    ) -> Sequence[InteractionMessage]:
        items = [
            self.get_by_id(mid)
            for mid, msg in self.messages.items()
            if msg.room_id == room_id and msg.deleted_at is None
        ]
        result = [item for item in items if item is not None]
        q = (query or "").strip().lower()
        if q:
            result = [item for item in result if q in item.body_text.lower()]
        result.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return result[:limit]

    def create_message(
        self,
        *,
        room_id: UUID,
        author_user_id: str | None,
        message_kind: str,
        body_text: str,
        parent_id: UUID | None = None,
        mentions: Sequence[tuple[str, Mapping[str, object], str]] | None = None,
    ) -> InteractionMessage:
        message_id = uuid4()
        mention_rows = [
            InteractionMention(
                id=uuid4(),
                message_id=message_id,
                mention_kind=kind,
                ref=dict(ref),
                label=label,
            )
            for kind, ref, label in mentions or ()
        ]
        self.mentions[message_id] = mention_rows
        message = InteractionMessage(
            id=message_id,
            room_id=room_id,
            message_kind=message_kind,
            body_text=body_text,
            created_at=datetime.now(timezone.utc),
            author_user_id=author_user_id,
            parent_id=parent_id,
            mentions=tuple(mention_rows),
        )
        self.messages[message_id] = message
        return message

    def update_body(
        self,
        *,
        message_id: UUID,
        body_text: str,
    ) -> InteractionMessage | None:
        message = self.messages.get(message_id)
        if message is None or message.deleted_at is not None:
            return None
        updated = InteractionMessage(
            id=message.id,
            room_id=message.room_id,
            message_kind=message.message_kind,
            body_text=body_text,
            created_at=message.created_at,
            author_user_id=message.author_user_id,
            parent_id=message.parent_id,
            edited_at=datetime.now(timezone.utc),
            deleted_at=message.deleted_at,
            mentions=tuple(self.mentions.get(message.id, ())),
            reactions=message.reactions,
        )
        self.messages[message_id] = updated
        return updated

    def soft_delete(self, *, message_id: UUID) -> InteractionMessage | None:
        message = self.messages.get(message_id)
        if message is None or message.deleted_at is not None:
            return None
        updated = InteractionMessage(
            id=message.id,
            room_id=message.room_id,
            message_kind=message.message_kind,
            body_text=message.body_text,
            created_at=message.created_at,
            author_user_id=message.author_user_id,
            parent_id=message.parent_id,
            edited_at=message.edited_at,
            deleted_at=datetime.now(timezone.utc),
            mentions=tuple(self.mentions.get(message.id, ())),
            reactions=message.reactions,
        )
        self.messages[message_id] = updated
        return updated

    def set_reaction(
        self,
        *,
        message_id: UUID,
        user_id: str,
        code: str,
    ) -> InteractionReaction:
        raise NotImplementedError

    def clear_reaction(
        self,
        *,
        message_id: UUID,
        user_id: str,
        code: str,
    ) -> bool:
        raise NotImplementedError

    def list_pins(self, room_id: UUID) -> Sequence[InteractionPin]:
        return ()

    def pin_message(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        pinned_by_user_id: str,
    ) -> InteractionPin:
        raise NotImplementedError

    def unpin_message(self, *, room_id: UUID, message_id: UUID) -> bool:
        return False

    def list_mentions_for_message(
        self,
        message_id: UUID,
    ) -> Sequence[InteractionMention]:
        return tuple(self.mentions.get(message_id, ()))

    def latest_in_room(self, room_id: UUID) -> InteractionMessage | None:
        items = [
            self.get_by_id(mid)
            for mid, msg in self.messages.items()
            if msg.room_id == room_id and msg.deleted_at is None
        ]
        alive = [item for item in items if item is not None]
        if not alive:
            return None
        alive.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return alive[0]

    def count_unread(
        self,
        *,
        room_id: UUID,
        since: datetime | None,
        exclude_user_id: str | None = None,
    ) -> int:
        actor = (exclude_user_id or "").strip()
        total = 0
        for message in self.messages.values():
            if message.room_id != room_id or message.deleted_at is not None:
                continue
            if since is not None and message.created_at <= since:
                continue
            if actor and (message.author_user_id or "").strip() == actor:
                continue
            total += 1
        return total

    def user_mentioned_in_room(self, *, room_id: UUID, user_id: str) -> bool:
        actor = (user_id or "").strip()
        if not actor:
            return False
        for message in self.messages.values():
            if message.room_id != room_id or message.deleted_at is not None:
                continue
            for mention in self.mentions.get(message.id, ()):
                if mention.mention_kind != "user":
                    continue
                if str(mention.ref.get("user_id") or "").strip() == actor:
                    return True
        return False


def _open_room(rooms: InMemoryInteractionRoomRepo, user_id: str = "u1"):
    return ManageInteractionRoomsUseCase(rooms).resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="order",
            entity_key="01|99",
            actor_user_id=user_id,
        )
    )


def test_post_list_and_search_messages() -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    room = _open_room(rooms)
    posted = uc.post(
        PostInteractionMessageInput(
            room_id=room.id,
            actor_user_id="u1",
            body_text="Falar com @Ana sobre atraso",
            mentions=[("user", {"user_id": "u2"}, "@Ana")],
        )
    )
    uc.post(
        PostInteractionMessageInput(
            room_id=room.id,
            actor_user_id="u1",
            body_text="Outro tópico",
        )
    )
    listed = uc.list_messages(room_id=room.id, actor_user_id="u1")
    assert len(listed) == 2
    found = uc.list_messages(room_id=room.id, actor_user_id="u1", query="atraso")
    assert len(found) == 1
    assert found[0].id == posted.id
    assert found[0].mentions[0].mention_kind == "user"


def test_update_and_delete_only_author() -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    rooms_uc = ManageInteractionRoomsUseCase(rooms)
    room = _open_room(rooms)
    rooms_uc.add_member(room_id=room.id, actor_user_id="u1", user_id="u2")
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    msg = uc.post(
        PostInteractionMessageInput(
            room_id=room.id,
            actor_user_id="u1",
            body_text="rascunho",
        )
    )
    with pytest.raises(PermissionError):
        uc.update(
            room_id=room.id,
            message_id=msg.id,
            actor_user_id="u2",
            body_text="hack",
        )
    updated = uc.update(
        room_id=room.id,
        message_id=msg.id,
        actor_user_id="u1",
        body_text="publicado",
    )
    assert updated.body_text == "publicado"
    assert updated.edited_at is not None
    deleted = uc.delete(room_id=room.id, message_id=msg.id, actor_user_id="u1")
    assert deleted.deleted_at is not None
    assert uc.list_messages(room_id=room.id, actor_user_id="u1") == []


def test_post_requires_body_and_membership() -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    room = _open_room(rooms)
    with pytest.raises(ValueError) as empty:
        uc.post(
            PostInteractionMessageInput(
                room_id=room.id,
                actor_user_id="u1",
                body_text="   ",
            )
        )
    assert str(empty.value) == InteractionRoomContentService.error("bodyRequired")
    with pytest.raises(PermissionError):
        uc.post(
            PostInteractionMessageInput(
                room_id=room.id,
                actor_user_id="stranger",
                body_text="oi",
            )
        )
