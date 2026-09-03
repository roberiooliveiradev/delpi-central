from __future__ import annotations

from uuid import uuid4

import pytest

from requests_app.domain.entities import Actor, Request
from requests_app.domain.exceptions import WorkflowEngineError
from requests_app.domain.services.content_loader import load_workflow_definition
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.domain.services.workflow_engine import WorkflowEngine


def _creator(**kwargs) -> Actor:
    base = dict(user_id="u-create", user_name="Criador", has_create=True, has_access=True)
    base.update(kwargs)
    return Actor(**base)


def _processor(**kwargs) -> Actor:
    base = dict(user_id="u-process", user_name="Faturamento", has_process=True, has_access=True)
    base.update(kwargs)
    return Actor(**base)


def _manager(**kwargs) -> Actor:
    base = dict(user_id="u-manage", user_name="Gestor", has_manage=True, has_access=True)
    base.update(kwargs)
    return Actor(**base)


def _request(
    *,
    status: str = "submitted",
    owner: str = "u-create",
    version: int = 1,
    type_code: str = "invoice-issuance",
) -> Request:
    return Request(
        id=uuid4(),
        request_number="REQ-2026-000001",
        request_type_id=uuid4(),
        type_code=type_code,
        status=status,
        created_by_user_id=owner,
        created_by_name="Criador",
        version=version,
    )


@pytest.fixture
def invoice_workflow() -> dict:
    return load_workflow_definition("invoice_issuance")


@pytest.fixture
def engine() -> WorkflowEngine:
    return WorkflowEngine()


def test_registry_loads_invoice_and_generic_without_engine_branch():
    registry = RequestTypeRegistry()
    invoice = RequestTypeRegistry.from_workflow_content(
        code="invoice-issuance",
        name="Emissão NF",
        workflow_name="invoice_issuance",
        permission_prefix="my-requests.invoice-issuance",
        branch_scope="required",
    )
    generic = RequestTypeRegistry.from_workflow_content(
        code="generic-simple",
        name="Genérico",
        workflow_name="generic_simple",
        permission_prefix="my-requests.generic-simple",
    )
    registry.register(invoice)
    registry.register(generic)
    assert registry.get("invoice-issuance").code == "invoice-issuance"
    assert registry.get("generic-simple").workflow_definition["initialStatus"] == "submitted"


@pytest.mark.parametrize(
    "status,actor_factory,expected",
    [
        ("submitted", _processor, {"view", "start"}),
        ("submitted", _creator, {"view", "cancel"}),
        ("submitted", _manager, {"view", "start", "cancel"}),
        ("in_progress", _processor, {"view", "return", "complete", "issue", "cancel"}),
        ("in_progress", _creator, {"view"}),
        ("needs_information", _creator, {"view", "edit", "resubmit"}),
        ("needs_information", _processor, {"view"}),
        ("needs_information", _manager, {"view", "cancel"}),
        ("completed", _creator, {"view"}),
        ("completed", _processor, {"view"}),
        ("cancelled", _manager, {"view"}),
    ],
)
def test_invoice_allowed_actions_parity(engine, invoice_workflow, status, actor_factory, expected):
    actions = set(
        engine.compute_allowed_actions(
            request=_request(status=status),
            actor=actor_factory(),
            workflow=invoice_workflow,
        )
    )
    assert actions == expected


def test_creator_cannot_start_submitted(engine, invoice_workflow):
    actions = engine.compute_allowed_actions(
        request=_request(status="submitted"),
        actor=_creator(),
        workflow=invoice_workflow,
    )
    assert "start" not in actions


def test_apply_start_assigns_processor(engine, invoice_workflow):
    result = engine.apply_transition(
        request=_request(status="submitted"),
        actor=_processor(),
        workflow=invoice_workflow,
        action="start",
        expected_version=1,
    )
    assert result.request.status == "in_progress"
    assert result.request.version == 2
    assert result.assignment is not None
    assert result.assignment.assignee_user_id == "u-process"
    assert result.history.action == "start"


def test_apply_issue_alias_completes(engine, invoice_workflow):
    result = engine.apply_transition(
        request=_request(status="in_progress"),
        actor=_processor(),
        workflow=invoice_workflow,
        action="issue",
        expected_version=1,
    )
    assert result.request.status == "completed"
    assert result.history.action == "complete"


def test_return_requires_reason(engine, invoice_workflow):
    with pytest.raises(WorkflowEngineError) as exc:
        engine.apply_transition(
            request=_request(status="in_progress"),
            actor=_processor(),
            workflow=invoice_workflow,
            action="return",
            body={},
            expected_version=1,
        )
    assert exc.value.code == "missing_field"
    assert exc.value.field == "return_reason"


def test_stale_version(engine, invoice_workflow):
    with pytest.raises(WorkflowEngineError) as exc:
        engine.apply_transition(
            request=_request(status="submitted", version=3),
            actor=_processor(),
            workflow=invoice_workflow,
            action="start",
            expected_version=1,
        )
    assert exc.value.code == "stale_version"


def test_cancel_create_only_on_submitted(engine, invoice_workflow):
    ok, code, _ = engine.can_transition(
        request=_request(status="in_progress"),
        actor=_creator(),
        workflow=invoice_workflow,
        action="cancel",
        body={"cancel_justification": "desistiu"},
        require_fields=True,
    )
    assert ok is False
    assert code == "forbidden"


def test_generic_workflow_independent_of_invoice(engine):
    workflow = load_workflow_definition("generic_simple")
    actions = engine.compute_allowed_actions(
        request=_request(status="submitted", type_code="generic-simple"),
        actor=_processor(),
        workflow=workflow,
    )
    assert "start" in actions
    assert "issue" not in actions
    result = engine.apply_transition(
        request=_request(status="in_progress"),
        actor=_processor(),
        workflow=workflow,
        action="reject",
        expected_version=1,
    )
    assert result.request.status == "rejected"
