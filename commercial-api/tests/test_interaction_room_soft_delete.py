from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.application.use_cases.manage_interaction_rooms import (
    ManageInteractionRoomsUseCase,
    ResolveInteractionRoomInput,
)
from commercial_app.domain.entities.interaction_room import InteractionRoom
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.interface.http.routes import interaction_room_routes
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


class _User:
    def __init__(self, permissions: list[str], sub: str = "manager-1"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str, method: str = "DELETE") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def _open_entity_room(
    repo: InMemoryInteractionRoomRepo,
    *,
    actor: str = "u1",
    entity_type: str = "order",
    entity_key: str = "01|102991",
    title: str = "Pedido 102991",
) -> InteractionRoom:
    uc = ManageInteractionRoomsUseCase(repository=repo)
    return uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            actor_user_id=actor,
            entity_type=entity_type,
            entity_key=entity_key,
            title=title,
        )
    )


def test_audit_messages_content_has_interaction_room_deleted() -> None:
    AuditMessagesContentService.clear_cache()
    bundle = AuditMessagesContentService.bundle()
    assert "interaction_room.deleted" in bundle["titles"]
    assert "interaction_room.deleted" in bundle["messages"]
    assert bundle["tones"]["interaction_room.deleted"] == "warning"
    assert InteractionRoomContentService.message("deleteRoomOk")


def test_soft_delete_marks_deleted_and_hides_from_get() -> None:
    repo = InMemoryInteractionRoomRepo()
    room = _open_entity_room(repo)
    audit = MagicMock()
    uc = ManageInteractionRoomsUseCase(repository=repo, audit_repository=audit)

    deleted = uc.soft_delete(room_id=room.id, actor_user_id="manager-1")
    assert deleted.deleted_at is not None
    assert repo.get_by_id(room.id) is None
    assert room.id in repo.rooms
    assert repo.rooms[room.id].deleted_at is not None

    with pytest.raises(LookupError):
        uc.get(room_id=room.id, actor_user_id="manager-1")

    audit.append.assert_called_once()
    kwargs = audit.append.call_args.kwargs
    assert kwargs["action"] == "interaction_room.deleted"
    assert kwargs["entity_type"] == "interaction_room"
    assert kwargs["entity_id"] == str(room.id)
    assert kwargs["payload"]["title"] == "Pedido 102991"
    assert kwargs["payload"]["kind"] == "entity"
    assert kwargs["payload"]["entity_type"] == "order"
    assert kwargs["payload"]["entity_key"] == "01|102991"


def test_soft_delete_without_audit_repo_still_works() -> None:
    repo = InMemoryInteractionRoomRepo()
    room = _open_entity_room(repo)
    uc = ManageInteractionRoomsUseCase(repository=repo, audit_repository=None)
    deleted = uc.soft_delete(room_id=room.id, actor_user_id="manager-1")
    assert deleted.deleted_at is not None


def test_soft_delete_requires_actor() -> None:
    repo = InMemoryInteractionRoomRepo()
    room = _open_entity_room(repo)
    uc = ManageInteractionRoomsUseCase(repository=repo)
    with pytest.raises(ValueError):
        uc.soft_delete(room_id=room.id, actor_user_id="  ")


def test_resolve_same_entity_creates_new_room_after_soft_delete() -> None:
    repo = InMemoryInteractionRoomRepo()
    first = _open_entity_room(repo)
    uc = ManageInteractionRoomsUseCase(repository=repo)
    uc.soft_delete(room_id=first.id, actor_user_id="manager-1")

    second = _open_entity_room(repo, actor="u2")
    assert second.id != first.id
    assert second.deleted_at is None
    assert repo.get_by_id(first.id) is None
    assert repo.get_by_id(second.id) is not None

    uc.soft_delete(room_id=second.id, actor_user_id="manager-1")
    third = _open_entity_room(repo, actor="u3")
    assert third.id not in {first.id, second.id}
    soft_deleted = [
        room
        for room in repo.rooms.values()
        if room.entity_key == "01|102991" and room.deleted_at is not None
    ]
    assert len(soft_deleted) == 2
    assert len([r for r in repo.rooms.values() if r.deleted_at is None]) == 1


def test_delete_route_403_without_manage(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/x")
    request.state.user = _User(["commercial.access"])
    fake_uc = MagicMock()
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    response = interaction_room_routes.delete_interaction_room(
        request,
        room_id=uuid4(),
    )
    assert response.status_code == 403
    fake_uc.soft_delete.assert_not_called()


def test_delete_route_403_without_permissions() -> None:
    request = _request("/interaction-rooms/x")
    request.state.user = _User([])
    response = interaction_room_routes.delete_interaction_room(
        request,
        room_id=uuid4(),
    )
    assert response.status_code == 403


def test_delete_route_200_with_manage(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/00000000-0000-0000-0000-000000000111")
    request.state.user = _User(["commercial.manage"])
    now = datetime.now(timezone.utc)
    room = InteractionRoom(
        id=UUID("00000000-0000-0000-0000-000000000111"),
        kind="entity",
        title="Pedido 1",
        created_by_user_id="manager-1",
        created_at=now,
        updated_at=now,
        entity_type="order",
        entity_key="01|1",
        deleted_at=now,
    )
    fake_uc = MagicMock()
    fake_uc.soft_delete.return_value = room
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "notify_interaction_room_deleted",
        MagicMock(),
    )
    response = interaction_room_routes.delete_interaction_room(
        request,
        room_id=room.id,
    )
    assert response.status_code == 200
    assert b"delete_interaction_room" in response.body
    fake_uc.soft_delete.assert_called_once()


def test_delete_route_404_when_already_deleted(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/x")
    request.state.user = _User(["commercial.manage"])
    fake_uc = MagicMock()
    fake_uc.soft_delete.side_effect = LookupError(
        InteractionRoomContentService.error("roomNotFound")
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    response = interaction_room_routes.delete_interaction_room(
        request,
        room_id=uuid4(),
    )
    assert response.status_code == 404


def test_rename_updates_title_and_audits() -> None:
    repo = InMemoryInteractionRoomRepo()
    room = _open_entity_room(repo, title="Pedido 1")
    audit = MagicMock()
    use_case = ManageInteractionRoomsUseCase(repository=repo, audit_repository=audit)
    updated = use_case.rename(
        room_id=room.id,
        actor_user_id="u-1",
        title="  Pedido Alfa  ",
    )
    assert updated.title == "Pedido Alfa"
    audit.append.assert_called_once()
    assert audit.append.call_args.kwargs["action"] == "interaction_room.renamed"
    assert audit.append.call_args.kwargs["payload"]["previous_title"] == "Pedido 1"


def test_rename_rejects_blank_title() -> None:
    repo = InMemoryInteractionRoomRepo()
    room = _open_entity_room(repo, title="Pedido 1")
    use_case = ManageInteractionRoomsUseCase(repository=repo)
    with pytest.raises(ValueError, match="Informe o nome"):
        use_case.rename(room_id=room.id, actor_user_id="u-1", title="   ")


def test_rename_route_200(monkeypatch: pytest.MonkeyPatch) -> None:
    from commercial_app.interface.http.schemas.interaction_room_schemas import (
        RenameInteractionRoomBody,
    )

    request = _request(
        "/interaction-rooms/00000000-0000-0000-0000-000000000222",
        method="PATCH",
    )
    request.state.user = _User(["commercial.access"], sub="u-1")
    now = datetime.now(timezone.utc)
    room = InteractionRoom(
        id=UUID("00000000-0000-0000-0000-000000000222"),
        kind="entity",
        title="Novo nome",
        created_by_user_id="u-1",
        created_at=now,
        updated_at=now,
        entity_type="order",
        entity_key="01|1",
    )
    fake_uc = MagicMock()
    fake_uc.rename.return_value = room
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "notify_room_inbox_changed",
        MagicMock(),
    )
    response = interaction_room_routes.rename_interaction_room(
        request,
        room_id=room.id,
        body=RenameInteractionRoomBody(title="Novo nome"),
    )
    assert response.status_code == 200
    assert b"rename_interaction_room" in response.body
    fake_uc.rename.assert_called_once()
