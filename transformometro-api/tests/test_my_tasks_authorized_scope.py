"""Authorized task visibility for the existing my_tasks capability.

Portal scopes stay `received` (assigned to me) and `delegated` (created by
me and assigned to someone else). `created` and `visible` are explicit
extensions of that same use case — not a new MCP tool and not an
organization-wide list.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.dispatch_service import GptActionsError
from tm_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.list_my_task_items import ListMyTaskItemsUseCase
from tm_app.application.use_cases.manage_transformometro_tasks import TaskCommandUseCases
from tm_app.infrastructure.persistence.repositories.task_repository import (
    InMemoryTaskRepository,
)
from tm_app.interface.http.routes import gpt_actions_routes, task_routes
from tm_app.interface.mcp import tool_bridge
from tm_app.interface.mcp.tool_bridge_v3 import tool_read

A = "11111111-1111-1111-1111-111111111111"
B = "22222222-2222-2222-2222-222222222222"
C = "33333333-3333-3333-3333-333333333333"
MANAGER = "44444444-4444-4444-4444-444444444444"


def _user(user_id=A, permissions=None):
    return SimpleNamespace(
        id=user_id,
        permissions=[ACCESS_PERMISSION] if permissions is None else permissions,
        is_superadmin=False,
    )


def _manager():
    return _user(MANAGER, permissions=[ACCESS_PERMISSION, MANAGE_PERMISSION])


def _use_case(commands: TaskCommandUseCases | None = None, signatures=None):
    repo_commands = commands or TaskCommandUseCases(InMemoryTaskRepository())
    payload = signatures if signatures is not None else {"items": []}
    return repo_commands, ListMyTaskItemsUseCase(repo_commands, lambda _user: payload)


def _ids(result) -> list[str]:
    return [
        item["source_id"]
        for item in result["items"]
        if item["type"] == "manual_task"
    ]


def _by_source(result, source_id):
    return next(item for item in result["items"] if item["source_id"] == source_id)


def test_self_assigned_task_is_in_received_and_created_once_in_visible():
    commands, use_case = _use_case()
    task = commands.create(
        _user(), title="Minha", description=None, assignee_user_id=A, due_date=None
    )
    received = use_case.execute(_user(), status="all", scope="received")
    created = use_case.execute(_user(), status="all", scope="created")
    visible = use_case.execute(_user(), status="all", scope="visible")
    assert _ids(received) == [task.id]
    assert _ids(created) == [task.id]
    assert _ids(visible) == [task.id]
    assert visible["total"] == 1
    assert _by_source(visible, task.id)["viewer_relation"] == "assignee_and_creator"
    assert use_case.execute(_user(), status="all")["scope"] == "received"


def test_task_created_by_a_and_assigned_to_b_follows_portal_visibility():
    commands, use_case = _use_case()
    task = commands.create(
        _user(),
        title="Para o Michael",
        description="acompanhar",
        assignee_user_id=B,
        due_date="2020-01-01",
    )
    assert _ids(use_case.execute(_user(B), status="all", scope="received")) == [task.id]
    assert _ids(use_case.execute(_user(B), status="all", scope="created")) == []
    assert _ids(use_case.execute(_user(), status="all", scope="received")) == []
    assert _ids(use_case.execute(_user(), status="all", scope="delegated")) == [task.id]
    assert _ids(use_case.execute(_user(), status="all", scope="created")) == [task.id]
    visible = use_case.execute(_user(), status="all", scope="visible")
    assert _ids(visible) == [task.id]
    item = _by_source(visible, task.id)
    assert item["viewer_relation"] == "creator"
    assert item["assignee_user_id"] == B
    assert item["created_by_user_id"] == A
    assignee = _by_source(
        use_case.execute(_user(B), status="all", scope="received"), task.id
    )
    assert assignee["viewer_relation"] == "assignee"


def test_unrelated_user_cannot_list_get_or_write():
    commands, use_case = _use_case()
    task = commands.create(
        _user(), title="Privada", description=None, assignee_user_id=B, due_date=None
    )
    for scope in ("received", "delegated", "created", "visible"):
        assert _ids(use_case.execute(_user(C), status="all", scope=scope)) == []
    with pytest.raises(AuthorizationDenied) as denied:
        commands.get(_user(C), task.id)
    assert denied.value.status_code == 403
    for action in (
        lambda: commands.update(
            _user(C), task.id, title="x", description=None,
            assignee_user_id=B, due_date=None,
        ),
        lambda: commands.complete(_user(C), task.id),
        lambda: commands.cancel(_user(C), task.id),
    ):
        with pytest.raises(PermissionError):
            action()
    assert commands.get(_user(), task.id).id == task.id
    assert commands.get(_user(B), task.id).id == task.id


def test_action_flags_match_portal_rules_and_do_not_authorize_writes():
    commands, use_case = _use_case()
    task = commands.create(
        _user(), title="Delegada", description=None, assignee_user_id=B, due_date=None
    )
    creator = _by_source(
        use_case.execute(_user(), status="all", scope="created"), task.id
    )
    assignee = _by_source(
        use_case.execute(_user(B), status="all", scope="received"), task.id
    )
    assert creator["actions"] == {
        "can_open": False,
        "can_edit": True,
        "can_complete": True,
        "can_cancel": True,
    }
    assert assignee["actions"]["can_edit"] is False
    assert assignee["actions"]["can_complete"] is True
    assert assignee["actions"]["can_cancel"] is False
    with pytest.raises(PermissionError):
        commands.update(
            _user(B), task.id, title="Não", description=None,
            assignee_user_id=B, due_date=None,
        )
    with pytest.raises(PermissionError):
        commands.cancel(_user(B), task.id)
    updated = commands.update(
        _user(), task.id, title="Ajustada", description="nota",
        assignee_user_id=B, due_date=None,
    )
    assert commands.get(_user(B), task.id).title == updated.title == "Ajustada"
    assert commands.complete(_user(B), task.id).status == "completed"
    assert commands.get(_user(), task.id).status == "completed"
    other = commands.create(
        _user(), title="Cancelar", description=None, assignee_user_id=B, due_date=None
    )
    assert commands.cancel(_user(), other.id).status == "cancelled"
    assert commands.get(_user(B), other.id).status == "cancelled"


def test_visible_pagination_does_not_duplicate_self_assigned_rows():
    commands, use_case = _use_case()
    self_task = commands.create(
        _user(), title="Eu", description=None, assignee_user_id=A, due_date=None
    )
    first = commands.create(
        _user(), title="Um", description=None, assignee_user_id=B, due_date="2020-01-02"
    )
    second = commands.create(
        _user(), title="Dois", description=None, assignee_user_id=B, due_date="2020-01-03"
    )
    page = use_case.execute(
        _user(), status="all", scope="visible", page=1, page_size=2
    )
    rest = use_case.execute(
        _user(), status="all", scope="visible", page=2, page_size=2
    )
    assert page["total"] == 3
    assert page["summary"]["pending"] == 3
    assert len(page["items"]) == 2
    assert len(rest["items"]) == 1
    combined = _ids(page) + _ids(rest)
    assert sorted(combined) == sorted([self_task.id, first.id, second.id])
    assert combined.count(self_task.id) == 1
    empty = use_case.execute(
        _user(), status="all", scope="visible", page=9, page_size=2
    )
    assert empty["items"] == []
    assert empty["total"] == 3


def test_filters_stay_inside_the_authorized_scope():
    commands, use_case = _use_case()
    late = commands.create(
        _user(),
        title="Alpha atrasada",
        description="prazo",
        assignee_user_id=B,
        due_date="2020-01-01",
    )
    commands.create(
        _user(),
        title="Alpha futura",
        description=None,
        assignee_user_id=B,
        due_date="2099-01-01",
    )
    done = commands.create(
        _user(), title="Alpha feita", description=None, assignee_user_id=B, due_date=None
    )
    commands.complete(_user(B), done.id)
    secret = commands.create(
        _user(C), title="Segredo do C", description=None, assignee_user_id=C, due_date=None
    )
    narrowed = use_case.execute(
        _user(),
        status="pending",
        scope="created",
        overdue=True,
        q="alpha",
    )
    assert _ids(narrowed) == [late.id]
    received_done = use_case.execute(_user(B), status="completed", scope="received")
    assert _ids(received_done) == [done.id]
    assert _ids(
        use_case.execute(_user(), status="all", scope="visible", q="segredo")
    ) == []
    assert _ids(
        use_case.execute(_user(C), status="all", scope="visible", q="segredo")
    ) == [secret.id]
    assert _ids(
        use_case.execute(_user(C), status="all", scope="visible", q="alpha")
    ) == []
    with pytest.raises(ValueError):
        use_case.execute(_user(), scope="team")
    with pytest.raises(ValueError):
        use_case.execute(_user(), page_size=0)
    with pytest.raises(ValueError):
        use_case.execute(_user(), overdue="talvez")


def test_manager_list_does_not_become_organization_wide():
    commands, use_case = _use_case()
    task = commands.create(
        _user(), title="Entre A e B", description=None, assignee_user_id=B, due_date=None
    )
    assert _ids(use_case.execute(_manager(), status="all", scope="visible")) == []
    assert commands.get(_manager(), task.id).id == task.id


def test_visible_includes_pending_signatures_once():
    commands, use_case = _use_case(
        signatures={"items": [{"id": "ata-1", "title": "Ata", "minute_number": "1"}]}
    )
    commands.create(
        _user(), title="Eu", description=None, assignee_user_id=A, due_date=None
    )
    visible = use_case.execute(_user(), status="pending", scope="visible")
    created = use_case.execute(_user(), status="pending", scope="created")
    signatures = [
        item for item in visible["items"] if item["type"] == "meeting_minute_signature"
    ]
    assert len(signatures) == 1
    assert signatures[0]["viewer_relation"] == "pending_signature"
    assert all(item["type"] == "manual_task" for item in created["items"])


def test_process_tasks_still_returns_a_delegated_task():
    repo = InMemoryTaskRepository()
    message_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    processo_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    repo.link_message_to_process(message_id, processo_id)
    commands = TaskCommandUseCases(repo)
    task = commands.create(
        _user(),
        title="No processo",
        description=None,
        assignee_user_id=B,
        due_date=None,
        source_interaction_message_id=message_id,
    )
    listed = commands.list_related_to_process(_user(C), processo_id)
    assert [item.id for item in listed] == [task.id]


def test_http_default_scope_stays_received_and_created_is_explicit():
    commands, use_case = _use_case()
    task = commands.create(
        _user(), title="Delegada", description=None, assignee_user_id=B, due_date=None
    )
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(task_routes, "_list_items", use_case):
        default = task_routes.list_my_tasks(request, status="all")
        created = task_routes.list_my_tasks(request, status="all", scope="created")
        invalid = task_routes.list_my_tasks(request, scope="team")
    assert default.status_code == 200
    assert created.status_code == 200
    assert invalid.status_code == 400
    default_body = json.loads(default.body)["data"]
    created_body = json.loads(created.body)["data"]
    assert default_body["scope"] == "received"
    assert default_body["items"] == []
    assert [item["source_id"] for item in created_body["items"]] == [task.id]


def test_gpt_route_forwards_scope_without_a_new_operation():
    request = SimpleNamespace(state=SimpleNamespace(user=_user()), headers={})
    with patch.object(
        gpt_actions_routes._dispatch, "list_my_tasks", return_value={"items": [], "total": 0}
    ) as listed:
        response = gpt_actions_routes.gpt_collaboration_read(
            request,
            action="my_tasks",
            status="all",
            scope="visible",
            page=2,
            page_size=5,
            overdue=True,
            q="alpha",
        )
    assert response.status_code == 200
    listed.assert_called_once()
    assert listed.call_args.kwargs["scope"] == "visible"
    assert listed.call_args.kwargs["page"] == 2
    assert listed.call_args.kwargs["q"] == "alpha"
    doc = build_gpt_actions_openapi()
    parameters = doc["paths"]["/transformometro/gpt-actions/v1/collaboration"]["get"]["parameters"]
    scope = next(item for item in parameters if item["name"] == "scope")
    assert scope["schema"]["enum"] == ["received", "delegated", "created", "visible"]
    assert scope["schema"]["default"] == "received"
    assert "organization" in scope["description"]
    catalog = build_capability_surface_catalog("mcp")
    task_read = next(item for item in catalog["analyses"] if item["id"] == "task_read")
    assert task_read["my_tasks_contract"]["default_scope"] == "received"
    assert "created" in task_read["my_tasks_contract"]["scope"]["enum"]


def _bind_memory(commands, use_case):
    original = (tool_bridge._dispatch._tasks, tool_bridge._dispatch._task_items)
    tool_bridge._dispatch._tasks = commands
    tool_bridge._dispatch._task_items = use_case
    return original


def _restore_memory(original) -> None:
    tool_bridge._dispatch._tasks, tool_bridge._dispatch._task_items = original


def _context(user_id: str):
    user_token = set_current_user(
        SimpleNamespace(
            id=user_id,
            email=f"{user_id[:8]}@example.com",
            name="Pessoa",
            roles=[],
            groups=[],
            permissions=[ACCESS_PERMISSION],
            is_superadmin=False,
        )
    )
    auth_token = set_request_authorization("Bearer test")
    return user_token, auth_token


def _reset(tokens) -> None:
    user_token, auth_token = tokens
    reset_request_authorization(auth_token)
    reset_current_user(user_token)


def _data(result):
    payload = result.structured_content
    return payload["data"] if payload.get("success") else payload


def test_mcp_read_returns_created_tasks_and_hides_them_from_strangers():
    commands, use_case = _use_case()
    task = commands.create(
        _user(), title="Para o Michael", description=None, assignee_user_id=B, due_date=None
    )
    original = _bind_memory(commands, use_case)
    try:
        tokens = _context(A)
        try:
            omitted = tool_read(entity="task", action="my_tasks", params={"status": "all"})
            created = tool_read(
                entity="task",
                action="my_tasks",
                params={"status": "all", "scope": "created"},
            )
            direct = tool_read(
                entity="task", action="task", params={"task_id": task.id}
            )
        finally:
            _reset(tokens)
        assert _data(omitted)["scope"] == "received"
        assert _data(omitted)["items"] == []
        assert [item["source_id"] for item in _data(created)["items"]] == [task.id]
        assert _data(direct)["id"] == task.id

        tokens = _context(B)
        try:
            assigned = tool_read(
                entity="task",
                action="my_tasks",
                params={"status": "all", "scope": "received"},
            )
            by_id = tool_read(entity="task", action="task", params={"task_id": task.id})
        finally:
            _reset(tokens)
        assert [item["source_id"] for item in _data(assigned)["items"]] == [task.id]
        assert _data(by_id)["assignee_user_id"] == B

        tokens = _context(C)
        try:
            hidden = tool_read(
                entity="task",
                action="my_tasks",
                params={"status": "all", "scope": "visible", "q": "Michael"},
            )
            denied = tool_read(entity="task", action="task", params={"task_id": task.id})
            invalid = tool_read(
                entity="task", action="my_tasks", params={"scope": "team"}
            )
            missing_process = tool_read(entity="task", action="process_tasks", params={})
        finally:
            _reset(tokens)
        assert _data(hidden)["items"] == []
        assert denied.structured_content["success"] is False
        assert denied.structured_content["status_code"] == 403
        assert invalid.structured_content["status_code"] == 400
        assert missing_process.structured_content["status_code"] == 400

        request_c = SimpleNamespace(state=SimpleNamespace(user=_user(C)), headers={})
        with pytest.raises(GptActionsError) as write_denied:
            tool_bridge._dispatch.task_write(
                request_c,
                "update_task",
                {
                    "task_id": task.id,
                    "title": "Invadiu",
                    "description": None,
                    "assignee_user_id": C,
                    "due_date": None,
                },
            )
        assert write_denied.value.status_code == 403
        request_a = SimpleNamespace(state=SimpleNamespace(user=_user()), headers={})
        updated = tool_bridge._dispatch.task_write(
            request_a,
            "update_task",
            {
                "task_id": task.id,
                "title": "Ajustada pelo criador",
                "description": None,
                "assignee_user_id": B,
                "due_date": None,
            },
        )
        assert updated["title"] == "Ajustada pelo criador"
        assert commands.get(_user(B), task.id).title == "Ajustada pelo criador"
    finally:
        _restore_memory(original)
