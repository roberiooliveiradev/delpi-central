"""HTTP RBAC — worklist / follow-ups (Wave G+)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from starlette.requests import Request

from commercial_app.domain.entities.task import CommercialTask
from commercial_app.interface.http.routes import worklist_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-rbac-test"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str = "/me/worklist", method: str = "GET") -> Request:
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


def _sample_task() -> CommercialTask:
    now = datetime.now(timezone.utc)
    return CommercialTask(
        id=UUID("00000000-0000-0000-0000-000000000099"),
        title="Follow",
        description=None,
        task_type="follow_up",
        status="open",
        priority="normal",
        due_at=None,
        completed_at=None,
        assignee_user_id="user-rbac-test",
        created_by_user_id="user-rbac-test",
        customer_code=None,
        customer_store=None,
        created_at=now,
        updated_at=now,
    )


def test_get_my_worklist_403_without_worklist_view():
    request = _request("/me/worklist")
    request.state.user = _User(["commercial.accounts.view"])
    response = worklist_routes.get_my_worklist(request)
    assert response.status_code == 403
    assert b"permiss" in response.body.lower()


def test_list_tasks_403_without_worklist_view():
    request = _request("/tasks")
    request.state.user = _User(["commercial.accounts.view"])
    response = worklist_routes.list_tasks(request)
    assert response.status_code == 403


def test_create_task_403_without_followups_manage():
    request = _request("/tasks", method="POST")
    request.state.user = _User(["commercial.worklist.view"])
    body = SimpleNamespace(
        title="Teste",
        description=None,
        task_type="follow_up",
        priority="normal",
        due_at=None,
        customer_code=None,
        customer_store=None,
        customers=None,
        assignee_user_id=None,
        assignee_user_ids=None,
        assignee_group_ids=None,
    )
    response = worklist_routes.create_task(request, body)
    assert response.status_code == 403


def test_complete_task_403_without_followups_manage():
    request = _request("/tasks/x/complete", method="POST")
    request.state.user = _User(["commercial.worklist.view"])
    response = worklist_routes.complete_task(
        request, task_id=UUID("00000000-0000-0000-0000-000000000001")
    )
    assert response.status_code == 403


def test_defer_task_403_without_followups_manage():
    request = _request("/tasks/x/defer", method="POST")
    request.state.user = _User(["commercial.worklist.view"])
    body = SimpleNamespace(due_at=datetime.now(timezone.utc))
    response = worklist_routes.defer_task(
        request,
        task_id=UUID("00000000-0000-0000-0000-000000000001"),
        body=body,
    )
    assert response.status_code == 403


def test_get_my_worklist_200_with_worklist_view(monkeypatch: pytest.MonkeyPatch):
    request = _request("/me/worklist")
    request.state.user = _User(["commercial.worklist.view"])

    fake_uc = MagicMock()
    fake_uc.get_worklist.return_value = {
        "overdue": [],
        "today": [],
        "later": [],
        "counts": {"overdue": 0, "today": 0, "later": 0, "open": 0},
    }
    monkeypatch.setattr(worklist_routes, "_use_case", lambda: fake_uc)
    monkeypatch.setattr(
        worklist_routes,
        "_user_id",
        lambda _req: "user-rbac-test",
    )

    response = worklist_routes.get_my_worklist(request, scope="mine", assignee_user_id=None)
    assert response.status_code == 200
    fake_uc.get_worklist.assert_called_once()


def test_create_task_200_with_followups_manage(monkeypatch: pytest.MonkeyPatch):
    request = _request("/tasks", method="POST")
    request.state.user = _User(["commercial.followups.manage"])

    fake_uc = MagicMock()
    fake_uc.create_task.return_value = _sample_task()
    monkeypatch.setattr(worklist_routes, "_use_case", lambda: fake_uc)
    monkeypatch.setattr(worklist_routes, "_user_id", lambda _req: "user-rbac-test")

    body = SimpleNamespace(
        title="Follow",
        description=None,
        task_type="follow_up",
        priority="normal",
        due_at=None,
        customer_code=None,
        customer_store=None,
        customers=None,
        assignee_user_id=None,
        assignee_user_ids=None,
        assignee_group_ids=None,
    )
    response = worklist_routes.create_task(request, body)
    assert response.status_code == 200
    fake_uc.create_task.assert_called_once()


def test_reassign_task_403_without_followups_manage():
    request = _request("/tasks/x/reassign", method="POST")
    request.state.user = _User(["commercial.worklist.view"])
    body = SimpleNamespace(
        assignee_user_id="other",
        assignee_user_ids=None,
        assignee_group_ids=None,
    )
    response = worklist_routes.reassign_task(
        request,
        task_id=UUID("00000000-0000-0000-0000-000000000001"),
        body=body,
    )
    assert response.status_code == 403


def test_reassign_task_200_with_followups_manage(monkeypatch: pytest.MonkeyPatch):
    request = _request("/tasks/x/reassign", method="POST")
    request.state.user = _User(
        ["commercial.followups.manage", "commercial.seller-portfolios.manage"]
    )

    fake_uc = MagicMock()
    fake_uc.reassign_task.return_value = _sample_task()
    fake_tasks = MagicMock()
    fake_tasks.get_by_id.return_value = _sample_task()
    monkeypatch.setattr(worklist_routes, "_use_case", lambda: fake_uc)
    monkeypatch.setattr(worklist_routes, "build_task_repository", lambda: fake_tasks)
    monkeypatch.setattr(worklist_routes, "_user_id", lambda _req: "user-rbac-test")
    monkeypatch.setattr(worklist_routes, "_is_portfolio_manager", lambda _req: True)

    body = SimpleNamespace(
        assignee_user_id="seller-b",
        assignee_user_ids=None,
        assignee_group_ids=None,
    )
    response = worklist_routes.reassign_task(
        request,
        task_id=UUID("00000000-0000-0000-0000-000000000099"),
        body=body,
    )
    assert response.status_code == 200
    fake_uc.reassign_task.assert_called_once()
