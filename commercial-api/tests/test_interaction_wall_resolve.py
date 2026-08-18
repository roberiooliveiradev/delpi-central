"""Resolve kind=wall — mural por grupo ou mural global."""

from __future__ import annotations

from uuid import uuid4

from commercial_app.application.use_cases.manage_interaction_rooms import (
    ManageInteractionRoomsUseCase,
    ResolveInteractionRoomInput,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


def test_resolve_wall_by_group_is_unique() -> None:
    rooms = InMemoryInteractionRoomRepo()
    uc = ManageInteractionRoomsUseCase(repository=rooms)
    group_id = uuid4()
    first = uc.resolve(
        ResolveInteractionRoomInput(
            kind="wall",
            actor_user_id="u1",
            group_id=group_id,
            title="Mural equipe A",
        )
    )
    second = uc.resolve(
        ResolveInteractionRoomInput(
            kind="wall",
            actor_user_id="u2",
            group_id=group_id,
        )
    )
    assert first.id == second.id
    assert first.kind == "wall"
    assert first.group_id == group_id
    assert rooms.get_member(room_id=first.id, user_id="u2") is not None


def test_resolve_global_wall_without_group() -> None:
    rooms = InMemoryInteractionRoomRepo()
    uc = ManageInteractionRoomsUseCase(repository=rooms)
    first = uc.resolve(
        ResolveInteractionRoomInput(kind="wall", actor_user_id="u1")
    )
    second = uc.resolve(
        ResolveInteractionRoomInput(kind="wall", actor_user_id="u2")
    )
    assert first.id == second.id
    assert first.group_id is None
    assert first.title == InteractionRoomContentService.message("wallGlobalTitle")


def test_v021_enforces_global_wall_unique() -> None:
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V021__interaction_wall_global_unique.sql"
    ).read_text(encoding="utf-8")
    assert "uq_commercial_interaction_rooms_wall_global" in text
    assert "group_id IS NULL" in text
