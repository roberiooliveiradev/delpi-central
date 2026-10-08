"""P1 — tipo process-issue (Problema de Processo) + isolamento de filial.

Cobre:
* seed/configuração do tipo (branch_scope=required, permission_prefix, workflow);
* fluxo submitted -> in_progress -> completed com assignSelf no start;
* política de filial: process sozinho NÃO destrava filiais; fila sem filtro
  fica limitada às filiais do usuário; detalhe/transição por UUID respeitam a
  filial do registro; manage/view-all mantêm escopo global.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    GetRequestUseCase,
    ListWorkQueueRequestsUseCase,
    TransitionRequestUseCase,
    UpdateRequestPayloadUseCase,
)
from requests_app.domain.process_issue_catalog import (
    ISSUE_CODES,
    PROCESS_ISSUE_PROCESS_PERMISSION,
    PROCESS_ISSUE_TYPE_CODE,
    issue_code_label,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)


def _user(*, user_id: str, permissions: list[str]):
    return SimpleNamespace(id=user_id, name="Usuário Teste", permissions=permissions)


def _admin():
    return _user(
        user_id="u-admin",
        permissions=["my-requests.access", "my-requests.manage"],
    )


def _process_analyst(*branches: str):
    return _user(
        user_id=f"u-proc-{'-'.join(branches) or 'none'}",
        permissions=[
            "my-requests.access",
            PROCESS_ISSUE_PROCESS_PERMISSION,
            *[f"my-requests.view.filial-{b}" for b in branches],
        ],
    )


@pytest.fixture
def harness():
    process_issue = RequestTypeRegistry.from_workflow_content(
        code=PROCESS_ISSUE_TYPE_CODE,
        name="Problema de Processo",
        workflow_name="process_issue",
        permission_prefix="my-requests.process-issue",
        presentation_mode="schema_driven",
        branch_scope="required",
    )
    types = InMemoryRequestTypeRepository([process_issue])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    return types, requests, idem


def _payload(**overrides):
    """Contrato P2 do snapshot reportado pelo cockpit."""
    base = {
        "source": "operator_cockpit",
        "reportedAt": "2026-10-08T12:00:00+00:00",
        "issue": {"code": "tool_not_linked", "reportedToolCode": "F12345"},
        "operator": {"code": "001234", "name": "Maria Silva"},
        "operation": {
            "productionOrder": "24640401002",
            "operationCode": "03",
            "reportedWorkCenter": "CT-02",
        },
        "materialsSnapshotAvailable": True,
        "materials": [],
    }
    base.update(overrides)
    return base


def _create(harness, *, branch: str) -> dict:
    types, requests, idem = harness
    return CreateRequestUseCase(types, requests, idem).execute(
        user=_admin(),
        type_code=PROCESS_ISSUE_TYPE_CODE,
        payload=_payload(),
        branch_code=branch,
        idempotency_key=str(uuid4()),
    )


# --- configuração do tipo -----------------------------------------------------


def test_process_issue_type_loads_and_requires_branch(harness):
    types, _, _ = harness
    request_type = types.get_by_code(PROCESS_ISSUE_TYPE_CODE)
    assert request_type is not None
    assert request_type.active is True
    assert request_type.name == "Problema de Processo"
    assert request_type.branch_scope == "required"
    assert request_type.permission_prefix == "my-requests.process-issue"


def test_issue_code_catalog_covers_expected_codes():
    assert ISSUE_CODES == frozenset(
        {
            "work_center_incompatible",
            "machine_limitation",
            "tool_not_linked",
            "material_not_linked",
            "process_information_missing",
            "other",
        }
    )
    assert issue_code_label("tool_not_linked") == (
        "Ferramenta não informada ou não vinculada"
    )


def test_create_requires_branch(harness):
    types, requests, idem = harness
    with pytest.raises(ApplicationError) as exc:
        CreateRequestUseCase(types, requests, idem).execute(
            user=_admin(),
            type_code=PROCESS_ISSUE_TYPE_CODE,
            payload={},
            branch_code=None,
            idempotency_key=str(uuid4()),
        )
    assert exc.value.code == "branch_required"


def test_snapshot_payload_accepts_optional_fields(harness):
    """toolCode/materialCode/note são opcionais — schema permissivo."""
    created = _create(harness, branch="01")
    assert created["status"] == "submitted"
    assert created["payload"]["issue"]["code"] == "tool_not_linked"


# --- workflow ------------------------------------------------------------------


def test_start_requires_process_and_assigns_analyst(harness):
    types, requests, idem = harness
    created = _create(harness, branch="01")

    outsider = _user(
        user_id="u-outsider",
        permissions=["my-requests.access", "my-requests.view.filial-01"],
    )
    with pytest.raises(ApplicationError) as exc:
        TransitionRequestUseCase(types, requests, idem).execute(
            user=outsider,
            request_id=created["id"],
            action="start",
            idempotency_key=str(uuid4()),
        )
    assert exc.value.status_code == 403

    analyst = _process_analyst("01")
    started = TransitionRequestUseCase(types, requests, idem).execute(
        user=analyst,
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    assert started["status"] == "in_progress"
    assignee = requests.get_active_processor_assignee_user_id(created["id"])
    assert str(assignee) == analyst.id


def test_complete_reaches_terminal_without_return_flow(harness):
    types, requests, idem = harness
    created = _create(harness, branch="01")
    analyst = _process_analyst("01")
    TransitionRequestUseCase(types, requests, idem).execute(
        user=analyst,
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    done = TransitionRequestUseCase(types, requests, idem).execute(
        user=analyst,
        request_id=created["id"],
        action="complete",
        idempotency_key=str(uuid4()),
    )
    assert done["status"] == "completed"
    workflow = types.get_by_code(PROCESS_ISSUE_TYPE_CODE).workflow_definition
    assert workflow["terminalStatuses"] == ["completed"]
    # sem retorno ao operador: nenhuma transição devolve a submitted
    for transition in workflow["transitions"]:
        assert transition["to"] != "submitted"


def test_process_issue_has_no_reject_or_requester_return(harness):
    workflow = harness[0].get_by_code(PROCESS_ISSUE_TYPE_CODE).workflow_definition
    actions = {t["action"] for t in workflow["transitions"]}
    assert actions == {"start", "complete"}


# --- isolamento de filial na fila ---------------------------------------------


def test_work_queue_scopes_to_user_branches(harness):
    created_01 = _create(harness, branch="01")
    created_02 = _create(harness, branch="02")
    types, requests, _ = harness
    queue = ListWorkQueueRequestsUseCase(types, requests)

    items_01 = queue.execute(user=_process_analyst("01"))["items"]
    assert {i["id"] for i in items_01} == {created_01["id"]}

    items_02 = queue.execute(user=_process_analyst("02"))["items"]
    assert {i["id"] for i in items_02} == {created_02["id"]}

    items_both = queue.execute(user=_process_analyst("01", "02"))["items"]
    assert {i["id"] for i in items_both} == {
        created_01["id"],
        created_02["id"],
    }

    # process sem nenhuma filial não vê registros com filial
    items_none = queue.execute(user=_process_analyst())["items"]
    assert items_none == []


def test_work_queue_admin_keeps_global_scope(harness):
    _create(harness, branch="01")
    _create(harness, branch="02")
    types, requests, _ = harness
    queue = ListWorkQueueRequestsUseCase(types, requests)

    admin_items = queue.execute(user=_admin())["items"]
    assert len(admin_items) == 2

    viewer = _user(
        user_id="u-viewall",
        permissions=["my-requests.access", "my-requests.view-all"],
    )
    assert len(queue.execute(user=viewer)["items"]) == 2


def test_work_queue_explicit_foreign_branch_is_403(harness):
    types, requests, _ = harness
    with pytest.raises(ApplicationError) as exc:
        ListWorkQueueRequestsUseCase(types, requests).execute(
            user=_process_analyst("01"), branch_code="02"
        )
    assert exc.value.status_code == 403
    assert exc.value.code == "branch_forbidden"


# --- isolamento por registro ---------------------------------------------------


def test_detail_by_uuid_respects_branch(harness):
    created_02 = _create(harness, branch="02")
    types, requests, _ = harness
    with pytest.raises(ApplicationError) as exc:
        GetRequestUseCase(types, requests).execute(
            user=_process_analyst("01"), request_id=created_02["id"]
        )
    assert exc.value.status_code == 403

    ok = GetRequestUseCase(types, requests).execute(
        user=_process_analyst("02"), request_id=created_02["id"]
    )
    assert ok["id"] == created_02["id"]


def test_transition_on_foreign_branch_is_403(harness):
    created_02 = _create(harness, branch="02")
    types, requests, idem = harness
    analyst_01 = _process_analyst("01")
    with pytest.raises(ApplicationError) as exc:
        TransitionRequestUseCase(types, requests, idem).execute(
            user=analyst_01,
            request_id=created_02["id"],
            action="start",
            idempotency_key=str(uuid4()),
        )
    assert exc.value.status_code == 403
    assert exc.value.code == "branch_forbidden"


def test_owner_keeps_access_to_own_record_any_branch(harness):
    """O solicitante continua vendo o próprio registro mesmo fora do escopo."""
    types, requests, idem = harness
    creator = _user(
        user_id="u-creator",
        permissions=[
            "my-requests.access",
            "my-requests.manage",
        ],
    )
    created = CreateRequestUseCase(types, requests, idem).execute(
        user=creator,
        type_code=PROCESS_ISSUE_TYPE_CODE,
        payload=_payload(issue={"code": "other"}),
        branch_code="02",
        idempotency_key=str(uuid4()),
    )
    seen = GetRequestUseCase(types, requests).execute(
        user=creator, request_id=created["id"]
    )
    assert seen["id"] == created["id"]


def test_payload_edit_respects_branch(harness):
    created_02 = _create(harness, branch="02")
    types, requests, idem = harness
    with pytest.raises(ApplicationError) as exc:
        UpdateRequestPayloadUseCase(types, requests, idem).execute(
            user=_process_analyst("01"),
            request_id=created_02["id"],
            payload={"issueCode": "other"},
            idempotency_key=str(uuid4()),
        )
    assert exc.value.status_code == 403
    assert exc.value.code == "branch_forbidden"
