from __future__ import annotations

from uuid import uuid4

import pytest

from commercial_app.domain.services.interaction_room_access_service import (
    InteractionRoomAccessService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


def test_require_room_exists_raises_when_missing() -> None:
    repo = InMemoryInteractionRoomRepo()
    svc = InteractionRoomAccessService(repo)
    with pytest.raises(LookupError) as exc:
        svc.require_room_exists(uuid4())
    assert str(exc.value) == InteractionRoomContentService.error("roomNotFound")


def test_room_exists_false_for_missing() -> None:
    repo = InMemoryInteractionRoomRepo()
    svc = InteractionRoomAccessService(repo)
    assert svc.room_exists(uuid4()) is False
