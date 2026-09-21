from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.list_my_task_items import ListMyTaskItemsUseCase
from tm_app.application.use_cases.manage_transformometro_tasks import TaskCommandUseCases
from tm_app.infrastructure.persistence.repositories.task_repository import InMemoryTaskRepository

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"

# operationIds do baseline: list_my_transformometro_tasks
# create_transformometro_task
# get_transformometro_task
# update_transformometro_task
# cancel_transformometro_task
# complete_transformometro_task


def _user(*, user_id=USER, permissions=None, is_superadmin=False):
    return SimpleNamespace(
        id=user_id,
        permissions=[ACCESS_PERMISSION] if permissions is None else permissions,
        is_superadmin=is_superadmin,
    )


def _commands() -> TaskCommandUseCases:
    return TaskCommandUseCases(InMemoryTaskRepository())


def test_create_and_list_isolation():
    commands = _commands()
    created = commands.create(_user(), title="Validar fluxo", description=None, assignee_user_id=USER, due_date="2026-09-25")
    commands.create(_user(user_id=OTHER), title="Outra", description=None, assignee_user_id=OTHER, due_date=None)
    mine = commands.list_mine(_user(), status="pending")
    assert [item.id for item in mine] == [created.id]
    assert created.title == "Validar fluxo"
    assert created.status == "pending"


def test_blank_title_and_invalid_assignee():
    commands = _commands()
    with pytest.raises(ValueError):
        commands.create(_user(), title="   ", description=None, assignee_user_id=USER, due_date=None)
    with pytest.raises(ValueError):
        commands.create(_user(), title="Ok", description=None, assignee_user_id="João Silva", due_date=None)


def test_complete_and_double_complete():
    commands = _commands()
    created = commands.create(_user(), title="Fechar", description="x", assignee_user_id=USER, due_date=None)
    done = commands.complete(_user(), created.id)
    assert done.status == "completed"
    assert done.completed_at is not None
    assert commands.list_mine(_user(), status="pending") == []
    with pytest.raises(ValueError):
        commands.complete(_user(), created.id)


def test_update_read_back():
    commands = _commands()
    created = commands.create(_user(), title="Antes", description=None, assignee_user_id=USER, due_date=None)
    updated = commands.update(
        _user(),
        created.id,
        title="Depois",
        description="nota",
        assignee_user_id=USER,
        due_date="2026-09-30",
    )
    assert updated.title == "Depois"
    assert updated.description == "nota"
    assert str(updated.due_date) == "2026-09-30"


def test_cancel_and_authz():
    commands = _commands()
    created = commands.create(_user(), title="Cancelar", description=None, assignee_user_id=USER, due_date=None)
    cancelled = commands.cancel(_user(), created.id)
    assert cancelled.status == "cancelled"
    with pytest.raises(AuthorizationDenied) as missing:
        commands.create(_user(permissions=[]), title="Sem acesso", description=None, assignee_user_id=USER, due_date=None)
    assert missing.value.status_code == 403
    with pytest.raises(AuthorizationDenied):
        commands.create(_user(permissions=[MANAGE_PERMISSION]), title="Só manage", description=None, assignee_user_id=USER, due_date=None)
    with pytest.raises(AuthorizationDenied) as anonymous:
        commands.list_mine(None)
    assert anonymous.value.status_code == 401


def test_unified_projection_does_not_copy_signature():
    commands = _commands()
    commands.create(_user(), title="Manual", description=None, assignee_user_id=USER, due_date=date(2020, 1, 1))
    signatures = {
        "items": [
            {
                "id": "ata-1",
                "title": "Reunião",
                "minute_number": "ATA-10",
                "unit_code": "01",
            }
        ]
    }
    result = ListMyTaskItemsUseCase(commands, lambda _user: signatures).execute(_user())
    types = [item["type"] for item in result["items"]]
    assert types[0] == "manual_task"
    assert types[1] == "meeting_minute_signature"
    assert result["items"][0]["overdue"] is True
    assert result["items"][1]["actions"]["can_complete"] is False
    assert result["items"][1]["id"] == "meeting_minute_signature:ata-1"
    assert result["summary"]["pending"] == 2


def test_http_authz_and_create():
    from types import SimpleNamespace
    from unittest.mock import patch

    from tm_app.interface.http.routes import task_routes

    commands = _commands()
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(task_routes, "_commands", commands):
        created = task_routes.create_task(
            request,
            task_routes.CreateTaskBody(title="Via HTTP", assignee_user_id=USER),
        )
        forbidden = task_routes.create_task(
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[]))),
            task_routes.CreateTaskBody(title="Bloqueada", assignee_user_id=USER),
        )
        anonymous = task_routes.list_my_tasks(
            SimpleNamespace(state=SimpleNamespace(user=None)),
        )
    assert created.status_code == 201
    assert forbidden.status_code == 403
    assert anonymous.status_code == 401


def test_partial_signature_failure_keeps_manual_tasks():
    commands = _commands()
    commands.create(_user(), title="Manual", description=None, assignee_user_id=USER, due_date=None)

    def boom(_user):
        raise RuntimeError("assinaturas indisponíveis")

    result = ListMyTaskItemsUseCase(commands, boom).execute(_user())
    assert result["items"][0]["type"] == "manual_task"
    assert result["partial_error"]
