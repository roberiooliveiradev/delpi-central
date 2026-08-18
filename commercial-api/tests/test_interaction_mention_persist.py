from __future__ import annotations

import pytest

from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
    PostInteractionMessageInput,
)
from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_message_use_case import (
    InMemoryInteractionMessageRepo,
    _open_room,
)
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


def test_post_persists_catalog_mentions() -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    room = _open_room(rooms)
    posted = uc.post(
        PostInteractionMessageInput(
            room_id=room.id,
            actor_user_id="u1",
            body_text="Ver @Ana e o pedido",
            mentions=[
                ("user", {"user_id": "u2"}, "@Ana"),
                ("order", {"branch": "01", "order": "102942"}, "102942"),
            ],
        )
    )
    stored = messages.list_mentions_for_message(posted.id)
    kinds = {item.mention_kind for item in stored}
    assert kinds == {"user", "order"}
    assert InteractionMentionKindsContentService.is_known("user")
    assert InteractionMentionKindsContentService.is_known("order")


def test_post_rejects_unknown_mention_kind() -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    room = _open_room(rooms)
    with pytest.raises(ValueError) as exc:
        uc.post(
            PostInteractionMessageInput(
                room_id=room.id,
                actor_user_id="u1",
                body_text="x",
                mentions=[("spaceship", {"id": "1"}, "@nave")],
            )
        )
    assert str(exc.value) == InteractionRoomContentService.error("kindUnknown")
    assert messages.messages == {}
