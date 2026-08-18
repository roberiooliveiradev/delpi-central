"""Publisher interno post_system_message — allowlist JSON, sem HTTP."""

from __future__ import annotations

import pytest

from commercial_app.application.use_cases.manage_interaction_rooms import (
    ManageInteractionRoomsUseCase,
    ResolveInteractionRoomInput,
)
from commercial_app.application.use_cases.post_system_message import (
    PostSystemMessageInput,
    PostSystemMessageUseCase,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_message_use_case import InMemoryInteractionMessageRepo
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


def _room_and_uc() -> tuple[object, PostSystemMessageUseCase]:
    InteractionRoomContentService.clear_cache()
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    room = ManageInteractionRoomsUseCase(repository=rooms).resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            actor_user_id="u1",
            entity_type="order",
            entity_key="01|1",
            title="Pedido",
        )
    )
    return room, PostSystemMessageUseCase(rooms=rooms, messages=messages)


def test_posts_system_message_for_allowed_event_kinds() -> None:
    room, uc = _room_and_uc()
    for event_kind in ("otd_event", "process_stage"):
        msg = uc.execute(
            PostSystemMessageInput(
                room_id=room.id,
                event_kind=event_kind,
                body_text=f"Evento {event_kind}",
            )
        )
        assert msg.message_kind == "system"
        assert msg.author_user_id is None
        assert msg.body_text == f"Evento {event_kind}"


def test_rejects_unknown_system_event_kind() -> None:
    room, uc = _room_and_uc()
    with pytest.raises(ValueError) as exc:
        uc.execute(
            PostSystemMessageInput(
                room_id=room.id,
                event_kind="confirmation_event",
                body_text="ainda não",
            )
        )
    assert str(exc.value) == InteractionRoomContentService.error(
        "systemEventKindInvalid"
    )


def test_system_event_kinds_come_from_json() -> None:
    InteractionRoomContentService.clear_cache()
    assert InteractionRoomContentService.system_event_kinds() == frozenset(
        {"otd_event", "process_stage"}
    )
    assert InteractionRoomContentService.is_allowed_system_event_kind("otd_event")
    assert not InteractionRoomContentService.is_allowed_system_event_kind(
        "confirmation_event"
    )
    assert not InteractionRoomContentService.is_allowed_system_event_kind("")
