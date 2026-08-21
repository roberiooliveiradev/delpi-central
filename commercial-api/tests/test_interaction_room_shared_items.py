"""Shared items da sala — extractor + use case."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from commercial_app.application.use_cases.list_interaction_room_shared_items import (
    ListInteractionRoomSharedItemsUseCase,
)
from commercial_app.domain.entities.attachment import CommercialAttachment
from commercial_app.domain.entities.interaction_room import InteractionMessage
from commercial_app.domain.services.interaction_room_shared_items_service import (
    InteractionRoomSharedItemsService,
)
from tests.test_interaction_message_use_case import InMemoryInteractionMessageRepo
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


class _AttachRepo:
    def __init__(self, rows: dict[str, list[CommercialAttachment]] | None = None) -> None:
        self._rows = rows or {}

    def list_for_owner(self, *, owner_type: str, owner_id: str, limit: int = 50):
        return list(self._rows.get(owner_id, ()))[:limit]

    def count_for_owners(self, *, owner_type: str, owner_ids):
        return {}

    def get_by_id(self, attachment_id):
        return None

    def create(self, **kwargs):
        raise NotImplementedError

    def delete(self, attachment_id):
        return None


def test_extract_markdown_and_bare_links():
    body = "veja [Docs](https://example.com/a) e também https://example.com/b"
    links = InteractionRoomSharedItemsService.extract_http_links(body)
    assert links == [
        ("Docs", "https://example.com/a"),
        ("example.com", "https://example.com/b"),
    ]


def test_list_shared_items_files_and_links():
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    from commercial_app.application.use_cases.manage_interaction_rooms import (
        ManageInteractionRoomsUseCase,
        ResolveInteractionRoomInput,
    )
    from commercial_app.application.use_cases.manage_interaction_messages import (
        ManageInteractionMessagesUseCase,
        PostInteractionMessageInput,
    )

    room = ManageInteractionRoomsUseCase(repository=rooms).resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            actor_user_id="user-1",
            entity_type="order",
            entity_key="02|002573",
            title="Pedido 002573",
        )
    )
    msg_uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    message = msg_uc.post(
        PostInteractionMessageInput(
            room_id=room.id,
            actor_user_id="user-1",
            body_text="arquivo e [Portal](https://delpi.example/x)",
        )
    )
    now = datetime.now(timezone.utc)
    attachment = CommercialAttachment(
        id=uuid4(),
        owner_type="room_message",
        owner_id=str(message.id),
        file_name="nota.pdf",
        storage_key="k",
        content_type="application/pdf",
        byte_size=10,
        uploaded_by_user_id="user-1",
        created_at=now,
    )
    uc = ListInteractionRoomSharedItemsUseCase(
        rooms=rooms,
        messages=messages,
        attachments=_AttachRepo({str(message.id): [attachment]}),
    )
    items = uc.execute(room_id=room.id, actor_user_id="user-1", kind="all")
    kinds = {item["kind"] for item in items}
    assert kinds == {"file", "link"}
    files = [item for item in items if item["kind"] == "file"]
    links = [item for item in items if item["kind"] == "link"]
    assert files[0]["title"] == "nota.pdf"
    assert files[0]["attachment_id"] == str(attachment.id)
    assert links[0]["href"] == "https://delpi.example/x"
    assert "02|002573" not in str(items)

    only_files = uc.execute(room_id=room.id, actor_user_id="user-1", kind="file")
    assert all(item["kind"] == "file" for item in only_files)

    filtered = uc.execute(
        room_id=room.id, actor_user_id="user-1", kind="all", query="portal"
    )
    assert len(filtered) == 1
    assert filtered[0]["kind"] == "link"
