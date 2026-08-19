"""HTTP create_task_from_interaction_message."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.application.use_cases.create_task_from_interaction_message import (
    CreateTaskFromInteractionMessageResult,
)
from commercial_app.domain.entities.interaction_room import InteractionMessage
from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.interface.http.routes import interaction_room_routes
from commercial_app.interface.http.schemas.interaction_room_schemas import (
    CreateTaskFromInteractionMessageBody,
)


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-room-test"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str, method: str = "POST") -> Request:
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


def _task(*, room_id: UUID, message_id: UUID) -> CommercialTask:
    now = datetime.now(timezone.utc)
    return CommercialTask(
        id=uuid4(),
        title="Confirmar produto",
        description=None,
        task_type="follow_up",
        status="open",
        priority="normal",
        due_at=None,
        completed_at=None,
        assignee_user_id="user-room-test",
        created_by_user_id="user-room-test",
        customer_code=None,
        customer_store=None,
        created_at=now,
        updated_at=now,
        related_entity_type="interaction_room",
        related_entity_id=str(room_id),
        source_interaction_message_id=message_id,
    )


def _task_ref(*, room_id: UUID, task: CommercialTask) -> InteractionMessage:
    return InteractionMessage(
        id=uuid4(),
        room_id=room_id,
        message_kind="task_ref",
        body_text=f"Tarefa criada: {task.title}",
        created_at=datetime.now(timezone.utc),
        author_user_id="user-room-test",
    )


def test_create_task_from_message_403() -> None:
    request = _request("/interaction-rooms/x/messages/y/tasks")
    request.state.user = _User([])
    response = interaction_room_routes.create_task_from_interaction_message(
        request,
        room_id=uuid4(),
        message_id=uuid4(),
        body=CreateTaskFromInteractionMessageBody(),
    )
    assert response.status_code == 403


def test_create_task_from_message_201(monkeypatch: pytest.MonkeyPatch) -> None:
    room_id = UUID("00000000-0000-0000-0000-000000000111")
    message_id = UUID("00000000-0000-0000-0000-000000000222")
    task = _task(room_id=room_id, message_id=message_id)
    task_ref = _task_ref(room_id=room_id, task=task)
    fake_uc = MagicMock()
    fake_uc.execute.return_value = CreateTaskFromInteractionMessageResult(
        task=task,
        task_ref_message=task_ref,
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "build_create_task_from_interaction_message_use_case",
        lambda: fake_uc,
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "notify_worklist_changed",
        MagicMock(),
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "notify_interaction_room_activity",
        MagicMock(),
    )
    portal = MagicMock()
    monkeypatch.setattr(
        interaction_room_routes,
        "build_enqueue_task_portal_notifications_service",
        lambda: portal,
    )

    request = _request("/interaction-rooms/x/messages/y/tasks")
    request.state.user = _User(["commercial.access"])
    response = interaction_room_routes.create_task_from_interaction_message(
        request,
        room_id=room_id,
        message_id=message_id,
        body=CreateTaskFromInteractionMessageBody(description="detalhe"),
    )

    assert response.status_code == 201
    assert b"create_task_from_interaction_message" in response.body
    assert b"task_ref_message" in response.body
    fake_uc.execute.assert_called_once()
    portal.on_task_created.assert_called_once()


def test_create_task_from_message_404(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_uc = MagicMock()
    fake_uc.execute.side_effect = LookupError(
        InteractionRoomContentService.error("messageNotFound")
    )
    monkeypatch.setattr(
        interaction_room_routes,
        "build_create_task_from_interaction_message_use_case",
        lambda: fake_uc,
    )
    request = _request("/interaction-rooms/x/messages/y/tasks")
    request.state.user = _User(["commercial.access"])
    response = interaction_room_routes.create_task_from_interaction_message(
        request,
        room_id=uuid4(),
        message_id=uuid4(),
        body=None,
    )
    assert response.status_code == 404
    assert InteractionRoomContentService.error("messageNotFound").encode() in response.body
