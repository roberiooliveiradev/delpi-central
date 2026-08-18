from datetime import datetime, timezone
from uuid import uuid4

from commercial_app.domain.entities.interaction_room import (
    MESSAGE_KINDS,
    ROOM_KINDS,
    InteractionMention,
    InteractionMessage,
    InteractionPin,
    InteractionReaction,
    InteractionRoom,
    InteractionRoomMember,
)
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)


def test_room_and_message_kind_vocabularies() -> None:
    assert ROOM_KINDS == frozenset({"entity", "process", "wall"})
    assert MESSAGE_KINDS == frozenset({"text", "system", "task_ref", "pin"})


def test_interaction_room_entities_to_dict() -> None:
    now = datetime.now(timezone.utc)
    room_id = uuid4()
    message_id = uuid4()
    room = InteractionRoom(
        id=room_id,
        kind="entity",
        title="Pedido 102942",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        entity_type="order",
        entity_key="01|102942",
    )
    member = InteractionRoomMember(
        id=uuid4(),
        room_id=room_id,
        user_id="u1",
        role="member",
        created_at=now,
    )
    mention = InteractionMention(
        id=uuid4(),
        message_id=message_id,
        mention_kind="user",
        ref={"user_id": "u2"},
        label="@Ana",
    )
    reaction = InteractionReaction(
        message_id=message_id,
        user_id="u1",
        code="ok",
        created_at=now,
    )
    pin = InteractionPin(
        id=uuid4(),
        room_id=room_id,
        message_id=message_id,
        pinned_by_user_id="u1",
        created_at=now,
    )
    message = InteractionMessage(
        id=message_id,
        room_id=room_id,
        message_kind="text",
        body_text="Olá @Ana",
        created_at=now,
        author_user_id="u1",
        mentions=(mention,),
        reactions=(reaction,),
    )

    assert room.to_dict()["entity_key"] == "01|102942"
    assert member.to_dict()["role"] == "member"
    assert mention.to_dict()["mention_kind"] == "user"
    assert reaction.to_dict()["code"] == "ok"
    assert pin.to_dict()["message_id"] == str(message_id)
    assert message.to_dict()["mentions"][0]["label"] == "@Ana"


def test_repository_ports_are_abstract() -> None:
    assert InteractionRoomRepositoryPort.__abstractmethods__
    assert InteractionMessageRepositoryPort.__abstractmethods__
    assert "find_entity_room" in InteractionRoomRepositoryPort.__abstractmethods__
    assert "create_message" in InteractionMessageRepositoryPort.__abstractmethods__
    assert "set_reaction" in InteractionMessageRepositoryPort.__abstractmethods__
