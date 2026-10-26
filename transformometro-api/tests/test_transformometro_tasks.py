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


def test_create_with_source_interaction_message():
    repo = InMemoryTaskRepository()
    msg_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    repo.message_ids.add(msg_id)
    commands = TaskCommandUseCases(repo)
    created = commands.create(
        _user(),
        title="Validar fluxo de compras",
        description="Validar fluxo de compras",
        assignee_user_id=USER,
        due_date=None,
        source_interaction_message_id=msg_id,
    )
    assert created.source_interaction_message_id == msg_id
    with pytest.raises(LookupError):
        commands.create(
            _user(),
            title="Sem origem",
            description=None,
            assignee_user_id=USER,
            due_date=None,
            source_interaction_message_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )


def test_create_allows_multiple_tasks_from_same_message():
    repo = InMemoryTaskRepository()
    msg_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    repo.message_ids.add(msg_id)
    commands = TaskCommandUseCases(repo)
    first = commands.create(
        _user(),
        title="Tarefa 1",
        description=None,
        assignee_user_id=USER,
        due_date=None,
        source_interaction_message_id=msg_id,
    )
    second = commands.create(
        _user(),
        title="Tarefa 2",
        description=None,
        assignee_user_id=USER,
        due_date=None,
        source_interaction_message_id=msg_id,
    )
    assert first.id != second.id
    assert first.source_interaction_message_id == second.source_interaction_message_id == msg_id


def test_partial_signature_failure_keeps_manual_tasks():
    commands = _commands()
    commands.create(_user(), title="Manual", description=None, assignee_user_id=USER, due_date=None)

    def boom(_user):
        raise RuntimeError("assinaturas indisponíveis")

    result = ListMyTaskItemsUseCase(commands, boom).execute(_user())
    assert result["items"][0]["type"] == "manual_task"
    assert result["partial_error"]


def test_list_related_to_process_via_interaction_chain():
    repo = InMemoryTaskRepository()
    processo_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    processo_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    msg_a = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    msg_b = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    repo.link_message_to_process(msg_a, processo_a)
    repo.link_message_to_process(msg_b, processo_b)
    commands = TaskCommandUseCases(repo)

    related_a = commands.create(
        _user(),
        title="Da sala A",
        description=None,
        assignee_user_id=USER,
        due_date=None,
        source_interaction_message_id=msg_a,
    )
    commands.create(
        _user(),
        title="Da sala B",
        description=None,
        assignee_user_id=USER,
        due_date=None,
        source_interaction_message_id=msg_b,
    )
    commands.create(
        _user(),
        title="Manual sem origem",
        description=None,
        assignee_user_id=USER,
        due_date=None,
    )

    listed_a = commands.list_related_to_process(_user(), processo_a)
    listed_b = commands.list_related_to_process(_user(), processo_b)
    assert [item.id for item in listed_a] == [related_a.id]
    assert [item.title for item in listed_b] == ["Da sala B"]
    assert all(item.source_interaction_message_id for item in listed_a)


def test_list_related_to_process_authz():
    repo = InMemoryTaskRepository()
    commands = TaskCommandUseCases(repo)
    with pytest.raises(AuthorizationDenied) as missing:
        commands.list_related_to_process(_user(permissions=[]), "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert missing.value.status_code == 403
    with pytest.raises(AuthorizationDenied):
        commands.list_related_to_process(
            _user(permissions=[MANAGE_PERMISSION]),
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
    with pytest.raises(AuthorizationDenied) as anonymous:
        commands.list_related_to_process(None, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert anonymous.value.status_code == 401


def test_http_list_processo_related_tasks():
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    from tm_app.interface.http.routes import task_routes

    repo = InMemoryTaskRepository()
    msg_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    processo_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    repo.link_message_to_process(msg_id, processo_id)
    commands = TaskCommandUseCases(repo)
    commands.create(
        _user(),
        title="Relacionada",
        description=None,
        assignee_user_id=USER,
        due_date=None,
        source_interaction_message_id=msg_id,
    )
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    processo_repo = MagicMock()
    processo_repo.get.return_value = {"processo_id": processo_id}

    with (
        patch.object(task_routes, "_commands", commands),
        patch.object(task_routes, "ProcessoRepository", return_value=processo_repo),
        patch.object(task_routes, "check_processo_view_access", return_value=None),
    ):
        ok_resp = task_routes.list_processo_related_tasks(processo_id, request)
        forbidden = task_routes.list_processo_related_tasks(
            processo_id,
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[]))),
        )
        processo_repo.get.return_value = None
        missing = task_routes.list_processo_related_tasks(processo_id, request)

    assert ok_resp.status_code == 200
    body = ok_resp.body
    import json

    payload = json.loads(body)
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["title"] == "Relacionada"
    assert forbidden.status_code == 403
    assert missing.status_code == 404


def test_delegated_scope_lists_tasks_assigned_to_others():
    commands = _commands()
    delegated = commands.create(
        _user(), title="Delegada", description=None, assignee_user_id=OTHER, due_date="2026-09-25"
    )
    commands.create(
        _user(), title="Para mim", description=None, assignee_user_id=USER, due_date=None
    )
    listed = commands.list_delegated(_user(), status="pending")
    assert [item.id for item in listed] == [delegated.id]
    assert [item.id for item in commands.list_mine(_user(), status="all")] != [delegated.id]
    assert all(item.id != delegated.id for item in commands.list_mine(_user(), status="pending"))
    assert any(item.id == delegated.id for item in commands.list_mine(_user(user_id=OTHER), status="pending"))


def test_delegated_scope_status_filters_and_completion_visibility():
    commands = _commands()
    delegated = commands.create(
        _user(), title="Delegada", description=None, assignee_user_id=OTHER, due_date=None
    )
    assert [item.id for item in commands.list_delegated(_user(), status="pending")] == [delegated.id]
    assert commands.list_delegated(_user(), status="completed") == []

    commands.complete(_user(user_id=OTHER), delegated.id)
    assert commands.list_delegated(_user(), status="pending") == []
    assert [item.id for item in commands.list_delegated(_user(), status="completed")] == [delegated.id]
    assert [item.id for item in commands.list_delegated(_user(), status="all")] == [delegated.id]


def test_delegated_scope_ignores_third_party_tasks_and_reassignment_keeps_creator():
    commands = _commands()
    mine = commands.create(
        _user(), title="Minha delegação", description=None, assignee_user_id=OTHER, due_date=None
    )
    third_party = commands.create(
        _user(user_id=OTHER), title="De terceiros", description=None, assignee_user_id=USER, due_date=None
    )
    assert [item.id for item in commands.list_delegated(_user(), status="all")] == [mine.id]

    commands.update(
        _user(),
        mine.id,
        title=mine.title,
        description=mine.description,
        assignee_user_id="33333333-3333-3333-3333-333333333333",
        due_date=None,
    )
    assert [item.id for item in commands.list_delegated(_user(), status="all")] == [mine.id]
    assert third_party.assignee_user_id == USER


def test_delegated_scope_authz_and_invalid_scope():
    commands = _commands()
    use_case = ListMyTaskItemsUseCase(commands, lambda _user: {"items": []})
    with pytest.raises(AuthorizationDenied) as anonymous:
        commands.list_delegated(None)
    assert anonymous.value.status_code == 401
    with pytest.raises(AuthorizationDenied):
        commands.list_delegated(_user(permissions=[]))
    with pytest.raises(ValueError):
        use_case.execute(_user(), scope="strangers")


def test_delegated_projection_excludes_signatures_and_exposes_context():
    repo = InMemoryTaskRepository()
    msg_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    repo.link_message_to_process(
        msg_id,
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        room_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        process_label="Compras corporativas",
    )
    commands = TaskCommandUseCases(repo)
    task = commands.create(
        _user(),
        title="Delegada com origem",
        description=None,
        assignee_user_id=OTHER,
        due_date=None,
        source_interaction_message_id=msg_id,
    )
    commands.create(_user(), title="Manual sem origem", description=None, assignee_user_id=OTHER, due_date=None)

    signatures = {"items": [{"id": "ata-9", "title": "Ata", "minute_number": "9", "unit_code": "01"}]}
    result = ListMyTaskItemsUseCase(commands, lambda _user: signatures).execute(
        _user(), status="all", scope="delegated"
    )
    assert {item["type"] for item in result["items"]} == {"manual_task"}
    assert result["partial_error"] is None

    with_origin = next(item for item in result["items"] if item["source_id"] == task.id)
    assert with_origin["context_label"] == "Compras corporativas"
    assert with_origin["route"] == "/apps/transformometro/interaction-rooms/cccccccc-cccc-cccc-cccc-cccccccccccc"
    assert with_origin["actions"]["can_open"] is True
    assert with_origin["assignee_user_id"] == OTHER
    assert with_origin["created_at_label"]

    without_origin = next(item for item in result["items"] if item["source_id"] != task.id)
    assert without_origin["route"] is None
    assert without_origin["actions"]["can_open"] is False


def test_http_my_tasks_scope_param():
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    from tm_app.interface.http.routes import task_routes

    list_items = MagicMock()
    list_items.execute.return_value = {"items": [], "summary": {"pending": 0}, "partial_error": None}
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(task_routes, "_list_items", list_items):
        resp = task_routes.list_my_tasks(request, status="all", scope="delegated")
        list_items.execute.side_effect = ValueError("Escopo de consulta inválido.")
        invalid = task_routes.list_my_tasks(request, scope="invalid")
    assert resp.status_code == 200
    list_items.execute.assert_any_call(request.state.user, status="all", scope="delegated")
    assert invalid.status_code == 400


THIRD = "33333333-3333-3333-3333-333333333333"
MANAGER = "44444444-4444-4444-4444-444444444444"


def _manager():
    return _user(user_id=MANAGER, permissions=[ACCESS_PERMISSION, MANAGE_PERMISSION])


def _delegated_task(commands: TaskCommandUseCases):
    return commands.create(
        _user(), title="Delegada", description=None, assignee_user_id=OTHER, due_date=None
    )


def test_task_get_individual_authz():
    commands = _commands()
    task = _delegated_task(commands)
    assert commands.get(_user(), task.id).id == task.id
    assert commands.get(_user(user_id=OTHER), task.id).id == task.id
    assert commands.get(_manager(), task.id).id == task.id
    with pytest.raises(AuthorizationDenied) as denied:
        commands.get(_user(user_id=THIRD), task.id)
    assert denied.value.status_code == 403
    with pytest.raises(LookupError):
        commands.get(_user(), "99999999-9999-9999-9999-999999999999")


def test_task_update_only_creator_or_manage():
    commands = _commands()
    task = _delegated_task(commands)
    for actor in (_user(user_id=OTHER), _user(user_id=THIRD)):
        with pytest.raises(AuthorizationDenied):
            commands.update(
                actor, task.id, title="Editado", description=None,
                assignee_user_id=OTHER, due_date=None,
            )
    updated = commands.update(
        _user(), task.id, title="Editado pelo criador", description=None,
        assignee_user_id=OTHER, due_date=None,
    )
    assert updated.title == "Editado pelo criador"
    by_manager = commands.update(
        _manager(), task.id, title="Editado por manage", description=None,
        assignee_user_id=OTHER, due_date=None,
    )
    assert by_manager.title == "Editado por manage"


def test_task_complete_assignee_creator_manage_only():
    commands = _commands()
    task = _delegated_task(commands)
    with pytest.raises(AuthorizationDenied):
        commands.complete(_user(user_id=THIRD), task.id)
    done = commands.complete(_user(user_id=OTHER), task.id)
    assert done.status == "completed"

    task2 = _delegated_task(commands)
    assert commands.complete(_user(), task2.id).status == "completed"
    task3 = _delegated_task(commands)
    assert commands.complete(_manager(), task3.id).status == "completed"


def test_task_cancel_creator_or_manage_only():
    commands = _commands()
    task = _delegated_task(commands)
    with pytest.raises(AuthorizationDenied):
        commands.cancel(_user(user_id=OTHER), task.id)
    with pytest.raises(AuthorizationDenied):
        commands.cancel(_user(user_id=THIRD), task.id)
    assert commands.cancel(_user(), task.id).status == "cancelled"
    task2 = _delegated_task(commands)
    assert commands.cancel(_manager(), task2.id).status == "cancelled"


def test_my_tasks_item_flags_follow_individual_authz():
    commands = _commands()
    commands.create(_user(), title="Delegada", description=None, assignee_user_id=OTHER, due_date=None)
    received = ListMyTaskItemsUseCase(commands, lambda _u: {"items": []}).execute(
        _user(user_id=OTHER), status="all"
    )
    item = next(i for i in received["items"] if i["type"] == "manual_task")
    assert item["actions"]["can_edit"] is False
    assert item["actions"]["can_complete"] is True
    assert item["actions"]["can_cancel"] is False

    delegated = ListMyTaskItemsUseCase(commands, lambda _u: {"items": []}).execute(
        _user(), status="all", scope="delegated"
    )
    ditem = delegated["items"][0]
    assert ditem["actions"]["can_edit"] is True
    assert ditem["actions"]["can_complete"] is True
    assert ditem["actions"]["can_cancel"] is True

    manager_view = ListMyTaskItemsUseCase(commands, lambda _u: {"items": []}).execute(
        _manager(), status="all"
    )
    assert all(i["type"] != "manual_task" for i in manager_view["items"])
