"""Use case create_task_from_interaction_message."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence
from uuid import UUID, uuid4

import pytest

from commercial_app.application.use_cases.create_task_from_interaction_message import (
    CreateTaskFromInteractionMessageInput,
    CreateTaskFromInteractionMessageUseCase,
)
from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
)
from commercial_app.application.use_cases.manage_worklist import ManageWorklistUseCase
from commercial_app.domain.entities.interaction_room import (
    InteractionMention,
    InteractionMessage,
    InteractionRoom,
    InteractionRoomMember,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_worklist_use_case import InMemoryActivityRepo, InMemoryTaskRepo


class FakeRooms:
    def __init__(self) -> None:
        self.rooms: dict[UUID, InteractionRoom] = {}
        self.members: dict[tuple[UUID, str], InteractionRoomMember] = {}

    def get_by_id(self, room_id: UUID) -> InteractionRoom | None:
        return self.rooms.get(room_id)

    def get_member(self, *, room_id: UUID, user_id: str) -> InteractionRoomMember | None:
        return self.members.get((room_id, user_id))


class FakeMessages:
    def __init__(self) -> None:
        self.items: dict[UUID, InteractionMessage] = {}

    def get_by_id(self, message_id: UUID) -> InteractionMessage | None:
        return self.items.get(message_id)

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
        mention_rows = tuple(
            InteractionMention(
                id=uuid4(),
                message_id=message_id,
                mention_kind=kind,
                ref=dict(ref),
                label=label,
            )
            for kind, ref, label in mentions or ()
        )
        message = InteractionMessage(
            id=message_id,
            room_id=room_id,
            message_kind=message_kind,
            body_text=body_text,
            created_at=datetime.now(timezone.utc),
            author_user_id=author_user_id,
            parent_id=parent_id,
            mentions=mention_rows,
        )
        self.items[message_id] = message
        return message


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed_room_message(
    *,
    rooms: FakeRooms,
    messages: FakeMessages,
    actor: str = "u1",
    body: str = "Confirmar produto 90AAAA01 no pedido",
    deleted: bool = False,
) -> tuple[UUID, UUID]:
    room_id = uuid4()
    message_id = uuid4()
    now = _now()
    rooms.rooms[room_id] = InteractionRoom(
        id=room_id,
        kind="entity",
        title="Pedido 1",
        created_by_user_id=actor,
        created_at=now,
        updated_at=now,
        entity_type="order",
        entity_key="01|1",
    )
    rooms.members[(room_id, actor)] = InteractionRoomMember(
        id=uuid4(),
        room_id=room_id,
        user_id=actor,
        role="member",
        created_at=now,
    )
    messages.items[message_id] = InteractionMessage(
        id=message_id,
        room_id=room_id,
        message_kind="text",
        body_text=body,
        created_at=now,
        author_user_id=actor,
        deleted_at=now if deleted else None,
    )
    return room_id, message_id


def _use_case(
    rooms: FakeRooms,
    messages: FakeMessages,
    tasks: InMemoryTaskRepo | None = None,
) -> tuple[CreateTaskFromInteractionMessageUseCase, InMemoryTaskRepo]:
    task_repo = tasks or InMemoryTaskRepo()
    worklist = ManageWorklistUseCase(
        task_repository=task_repo,
        activity_repository=InMemoryActivityRepo(),
    )
    interaction_messages = ManageInteractionMessagesUseCase(
        rooms=rooms,
        messages=messages,
    )
    return (
        CreateTaskFromInteractionMessageUseCase(
            rooms=rooms,
            messages=messages,
            worklist=worklist,
            interaction_messages=interaction_messages,
        ),
        task_repo,
    )


def test_creates_task_linked_to_room_and_message() -> None:
    rooms = FakeRooms()
    messages = FakeMessages()
    room_id, message_id = _seed_room_message(rooms=rooms, messages=messages)
    uc, tasks = _use_case(rooms, messages)

    result = uc.execute(
        CreateTaskFromInteractionMessageInput(
            room_id=room_id,
            message_id=message_id,
            actor_user_id="u1",
        )
    )

    task = result.task
    assert task.title == "Confirmar produto 90AAAA01 no pedido"
    assert task.description == "Confirmar produto 90AAAA01 no pedido"
    assert task.related_entity_type == "interaction_room"
    assert task.related_entity_id == str(room_id)
    assert task.source_interaction_message_id == message_id
    assert tasks.items[task.id].source_interaction_message_id == message_id

    ref_msg = result.task_ref_message
    assert ref_msg.message_kind == "task_ref"
    assert ref_msg.body_text == "Tarefa criada: Confirmar produto 90AAAA01 no pedido"
    assert ref_msg.room_id == room_id
    assert any(m.mention_kind == "task" for m in ref_msg.mentions)
    assert any(
        str(m.ref.get("task_id")) == str(task.id) for m in ref_msg.mentions
    )


def test_allows_non_member() -> None:
    rooms = FakeRooms()
    messages = FakeMessages()
    room_id, message_id = _seed_room_message(rooms=rooms, messages=messages)
    uc, tasks = _use_case(rooms, messages)

    result = uc.execute(
        CreateTaskFromInteractionMessageInput(
            room_id=room_id,
            message_id=message_id,
            actor_user_id="stranger",
        )
    )
    assert result.task.title
    assert tasks.items[result.task.id].source_interaction_message_id == message_id


def test_rejects_deleted_message() -> None:
    rooms = FakeRooms()
    messages = FakeMessages()
    room_id, message_id = _seed_room_message(
        rooms=rooms,
        messages=messages,
        deleted=True,
    )
    uc, _ = _use_case(rooms, messages)

    with pytest.raises(ValueError) as exc:
        uc.execute(
            CreateTaskFromInteractionMessageInput(
                room_id=room_id,
                message_id=message_id,
                actor_user_id="u1",
            )
        )
    assert str(exc.value) == InteractionRoomContentService.error("messageDeletedForTask")


def test_rejects_message_from_other_room() -> None:
    rooms = FakeRooms()
    messages = FakeMessages()
    room_id, _ = _seed_room_message(rooms=rooms, messages=messages)
    other_message_id = uuid4()
    messages.items[other_message_id] = InteractionMessage(
        id=other_message_id,
        room_id=uuid4(),
        message_kind="text",
        body_text="outra",
        created_at=_now(),
        author_user_id="u1",
    )
    uc, _ = _use_case(rooms, messages)

    with pytest.raises(ValueError) as exc:
        uc.execute(
            CreateTaskFromInteractionMessageInput(
                room_id=room_id,
                message_id=other_message_id,
                actor_user_id="u1",
            )
        )
    assert str(exc.value) == InteractionRoomContentService.error("messageNotInRoom")


def test_title_summary_strips_images_and_truncates() -> None:
    InteractionRoomContentService.clear_cache()
    long_body = "A" * 120 + " ![img](attachment:11111111-2222-3333-4444-555555555555)"
    rooms = FakeRooms()
    messages = FakeMessages()
    room_id, message_id = _seed_room_message(rooms=rooms, messages=messages, body=long_body)
    uc, _ = _use_case(rooms, messages)
    result = uc.execute(
        CreateTaskFromInteractionMessageInput(
            room_id=room_id,
            message_id=message_id,
            actor_user_id="u1",
        )
    )
    assert len(result.task.title) <= 80
    assert result.task.title.endswith("…")
    assert "attachment:" not in result.task.title
    assert result.task.description == long_body.strip()


def test_v020_adds_source_interaction_message_column() -> None:
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V020__task_source_interaction_message.sql"
    ).read_text(encoding="utf-8")
    assert "source_interaction_message_id" in text
    assert "ADD COLUMN IF NOT EXISTS source_interaction_message_id" in text
