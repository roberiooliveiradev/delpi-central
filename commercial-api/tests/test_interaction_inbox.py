from __future__ import annotations

from commercial_app.application.use_cases.list_interaction_inbox import (
    ListInteractionInboxUseCase,
)
from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
    PostInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_interaction_rooms import (
    ManageInteractionRoomsUseCase,
    ResolveInteractionRoomInput,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_message_use_case import InMemoryInteractionMessageRepo
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


def _uc():
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    return (
        rooms,
        messages,
        ManageInteractionRoomsUseCase(rooms),
        ManageInteractionMessagesUseCase(rooms=rooms, messages=messages),
        ListInteractionInboxUseCase(rooms=rooms, messages=messages),
    )


def test_inbox_lists_all_rooms_without_membership() -> None:
    rooms, messages, room_uc, msg_uc, inbox = _uc()
    order_room = room_uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="order",
            entity_key="01|999",
            actor_user_id="u1",
            title="Pedido 999",
        )
    )
    msg_uc.post(
        PostInteractionMessageInput(
            room_id=order_room.id,
            actor_user_id="u1",
            body_text="visível para todos com access",
        )
    )
    items = inbox.execute(actor_user_id="u2", filter_key="all")
    assert order_room.id in {item.id for item in items}


def test_inbox_lists_preview_unread_and_filters() -> None:
    rooms, messages, room_uc, msg_uc, inbox = _uc()
    order_room = room_uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="order",
            entity_key="01|102942",
            actor_user_id="u1",
            title="Pedido 102942",
        )
    )
    wall = room_uc.resolve(
        ResolveInteractionRoomInput(
            kind="wall",
            group_id=order_room.id,  # reuse uuid for group stub if FK not enforced in memory
            actor_user_id="u1",
            title="Mural equipe",
        )
    )
    # InMemory find_wall may need real group — resolve wall creates with group_id
    assert wall.kind == "wall"

    rooms.add_member(room_id=order_room.id, user_id="u2", role="member")
    room_uc.mark_read(room_id=order_room.id, actor_user_id="u1")
    msg_uc.post(
        PostInteractionMessageInput(
            room_id=order_room.id,
            actor_user_id="u2",
            body_text="Atualização do pedido 102942",
            mentions=[("user", {"user_id": "u1"}, "@u1")],
        )
    )

    all_items = inbox.execute(actor_user_id="u1", filter_key="all")
    assert {item.id for item in all_items} >= {order_room.id, wall.id}
    order_item = next(item for item in all_items if item.id == order_room.id)
    assert order_item.unread_count >= 1
    assert order_item.mentioned is True
    assert "102942" in (order_item.last_message_preview or "")

    unread = inbox.execute(actor_user_id="u1", filter_key="unread")
    assert order_room.id in {item.id for item in unread}

    mentioned = inbox.execute(actor_user_id="u1", filter_key="mentioned")
    assert order_room.id in {item.id for item in mentioned}

    walls = inbox.execute(actor_user_id="u1", filter_key="wall")
    assert all(item.kind == "wall" for item in walls)

    searched = inbox.execute(actor_user_id="u1", query="Pedido")
    assert order_room.id in {item.id for item in searched}


def test_inbox_rejects_unknown_filter() -> None:
    _, _, _, _, inbox = _uc()
    try:
        inbox.execute(actor_user_id="u1", filter_key="spaceship")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == InteractionRoomContentService.error("kindUnknown")
