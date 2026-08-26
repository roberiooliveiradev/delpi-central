"""Use case create_task_from_interaction_message."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence
from uuid import UUID, uuid4

import pytest

from commercial_app.application.services.attachment_storage import AttachmentStorage
from commercial_app.application.use_cases.create_task_from_interaction_message import (
    CreateTaskFromInteractionMessageInput,
    CreateTaskFromInteractionMessageUseCase,
)
from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
)
from commercial_app.application.use_cases.manage_worklist import ManageWorklistUseCase
from commercial_app.domain.entities.attachment import CommercialAttachment
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


class FakeAttachments:
    def __init__(self) -> None:
        self.items: list[CommercialAttachment] = []

    def list_for_owner(
        self,
        *,
        owner_type: str,
        owner_id: str,
        limit: int = 50,
    ) -> Sequence[CommercialAttachment]:
        return [
            item
            for item in self.items
            if item.owner_type == owner_type and item.owner_id == owner_id
        ][:limit]

    def count_for_owners(self, *, owner_type: str, owner_ids: Sequence[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            if item.owner_type != owner_type or item.owner_id not in owner_ids:
                continue
            counts[item.owner_id] = counts.get(item.owner_id, 0) + 1
        return counts

    def get_by_id(self, attachment_id: UUID) -> CommercialAttachment | None:
        for item in self.items:
            if item.id == attachment_id:
                return item
        return None

    def create(
        self,
        *,
        owner_type: str,
        owner_id: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        byte_size: int,
        uploaded_by_user_id: str,
    ) -> CommercialAttachment:
        record = CommercialAttachment(
            id=uuid4(),
            owner_type=owner_type,
            owner_id=owner_id,
            file_name=file_name,
            storage_key=storage_key,
            content_type=content_type,
            byte_size=byte_size,
            uploaded_by_user_id=uploaded_by_user_id,
            created_at=datetime.now(timezone.utc),
        )
        self.items.append(record)
        return record

    def delete(self, attachment_id: UUID) -> CommercialAttachment | None:
        for index, item in enumerate(self.items):
            if item.id == attachment_id:
                return self.items.pop(index)
        return None


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
    attachments: FakeAttachments | None = None,
    storage: AttachmentStorage | None = None,
) -> tuple[CreateTaskFromInteractionMessageUseCase, InMemoryTaskRepo]:
    task_repo = tasks or InMemoryTaskRepo()
    attachment_repo = attachments or FakeAttachments()
    attachment_storage = storage or AttachmentStorage(
        base_dir=str(Path("/tmp/commercial-task-from-message-test")),
    )
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
            attachments=attachment_repo,
            attachment_storage=attachment_storage,
            tasks=task_repo,
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


def test_persists_source_message_mentions() -> None:
    rooms = FakeRooms()
    messages = FakeMessages()
    room_id, message_id = _seed_room_message(rooms=rooms, messages=messages)
    mention_id = uuid4()
    messages.items[message_id] = InteractionMessage(
        id=message_id,
        room_id=room_id,
        message_kind="text",
        body_text="Falar com @Ana Silva",
        created_at=_now(),
        author_user_id="u1",
        mentions=(
            InteractionMention(
                id=mention_id,
                message_id=message_id,
                mention_kind="user",
                ref={"user_id": "u2"},
                label="@Ana Silva",
            ),
        ),
    )
    uc, tasks = _use_case(rooms, messages)
    result = uc.execute(
        CreateTaskFromInteractionMessageInput(
            room_id=room_id,
            message_id=message_id,
            actor_user_id="u1",
        )
    )
    payload = result.task.to_dict()
    assert len(payload["source_message_mentions"]) == 1
    assert payload["source_message_mentions"][0]["mention_kind"] == "user"
    assert payload["source_message_mentions"][0]["label"] == "@Ana Silva"
    stored = tasks.items[result.task.id].source_message_mentions
    assert len(stored) == 1
    assert stored[0]["mention_kind"] == "user"


def test_clones_message_attachments_and_rewrites_description(
    tmp_path: Path,
) -> None:
    rooms = FakeRooms()
    messages = FakeMessages()
    attachments = FakeAttachments()
    storage = AttachmentStorage(base_dir=str(tmp_path))
    room_id, message_id = _seed_room_message(
        rooms=rooms,
        messages=messages,
        body="Veja ![img](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)",
    )
    source_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    stored = storage.save(
        owner_type="room_message",
        owner_id=str(message_id),
        original_name="foto.png",
        content=b"png-bytes",
        mime_type="image/png",
    )
    attachments.items.append(
        CommercialAttachment(
            id=source_id,
            owner_type="room_message",
            owner_id=str(message_id),
            file_name=stored.file_name,
            storage_key=stored.storage_key,
            content_type="image/png",
            byte_size=stored.byte_size,
            uploaded_by_user_id="u1",
            created_at=_now(),
        )
    )
    uc, tasks = _use_case(rooms, messages, attachments=attachments, storage=storage)
    result = uc.execute(
        CreateTaskFromInteractionMessageInput(
            room_id=room_id,
            message_id=message_id,
            actor_user_id="u1",
        )
    )
    task = result.task
    cloned = [
        item
        for item in attachments.items
        if item.owner_type == "task" and item.owner_id == str(task.id)
    ]
    assert len(cloned) == 1
    assert str(source_id) not in (task.description or "")
    assert f"attachment:{cloned[0].id}" in (task.description or "")
    assert tasks.items[task.id].description == task.description


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


def test_v022_adds_source_message_mentions_column() -> None:
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V022__task_source_message_mentions.sql"
    ).read_text(encoding="utf-8")
    assert "source_message_mentions" in text
    assert "ADD COLUMN IF NOT EXISTS source_message_mentions" in text


def test_v020_adds_source_interaction_message_column() -> None:
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V020__task_source_interaction_message.sql"
    ).read_text(encoding="utf-8")
    assert "source_interaction_message_id" in text
    assert "ADD COLUMN IF NOT EXISTS source_interaction_message_id" in text
