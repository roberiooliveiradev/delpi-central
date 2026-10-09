"""Validação do seed V016 — tipo "Solicitação Diversa" (general-request).

Os JSONB de seed são extraídos do próprio arquivo de migration para que o teste
valide o que vai para o banco (não uma cópia divergente).
"""

import json
import re
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.domain.services.attendant_portal_notification_policy import (
    resolve_queue_created_copy,
)
from requests_app.application.use_cases.request_use_cases import _validate_branch
from requests_app.domain.entities import Actor, Request
from requests_app.domain.exceptions import WorkflowEngineError
from requests_app.domain.services.creator_portal_notification_policy import (
    should_notify_creator_on_transition,
)
from requests_app.domain.services.form_schema_payload_validation_service import (
    FormSchemaPayloadValidationService,
)
from requests_app.domain.services.workflow_engine import WorkflowEngine
from requests_app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
)

MIGRATION = MIGRATIONS_DIR / "V016__seed_general_request_type.sql"


def _jsonb_blocks() -> list[dict]:
    sql = MIGRATION.read_text(encoding="utf-8")
    return [json.loads(block) for block in re.findall(r"'(\{.*?\})'::jsonb", sql, re.S)]


@pytest.fixture(scope="module")
def seed() -> tuple[dict, dict, dict]:
    form_schema, ui_schema, workflow, _destination = _jsonb_blocks()
    return form_schema, ui_schema, workflow


def _request(status: str, owner_id: str = "user-1") -> Request:
    return Request(
        id=uuid4(),
        request_number="REQ-001",
        request_type_id=uuid4(),
        type_code="general-request",
        status=status,
        created_by_user_id=owner_id,
        created_by_name="Solicitante",
        payload={"title": "Demanda", "description": "Detalhe da demanda"},
    )


def _owner() -> Actor:
    return Actor(user_id="user-1", user_name="Solicitante", has_access=True, has_create=True)


def _processor() -> Actor:
    return Actor(user_id="proc-1", user_name="Processos", has_access=True, has_process=True)


def _other_user() -> Actor:
    return Actor(user_id="user-2", user_name="Outra pessoa", has_access=True, has_create=True)


# --- form_schema -----------------------------------------------------------


def test_form_schema_requires_title_and_description(seed):
    form_schema, _, _ = seed
    service = FormSchemaPayloadValidationService()
    with pytest.raises(ApplicationError) as exc:
        service.validate({"description": "texto longo o bastante"}, form_schema)
    assert exc.value.field == "title"


def test_form_schema_accepts_valid_payload(seed):
    form_schema, _, _ = seed
    service = FormSchemaPayloadValidationService()
    out = service.validate(
        {"title": "  Revisar fluxo  ", "description": "Texto com detalhes."},
        form_schema,
    )
    assert out == {"title": "Revisar fluxo", "description": "Texto com detalhes."}


def test_form_schema_rejects_extra_fields(seed):
    form_schema, _, _ = seed
    service = FormSchemaPayloadValidationService()
    with pytest.raises(ApplicationError):
        service.validate(
            {"title": "abc", "description": "texto suficiente", "extra": "x"},
            form_schema,
        )


# --- branch_scope ----------------------------------------------------------


def test_branch_scope_none_ignores_branch(seed):
    _, _, workflow = seed
    # branch_scope=none: nenhuma filial é exigida nem validada.
    assert _validate_branch(actor=_owner(), branch_code=None, branch_scope="none") is None
    assert workflow["initialStatus"] == "submitted"


# --- workflow --------------------------------------------------------------


def test_owner_edits_and_cancels_while_submitted(seed):
    _, _, workflow = seed
    engine = WorkflowEngine()
    request = _request("submitted")
    actions = engine.compute_allowed_actions(
        request=request, actor=_owner(), workflow=workflow
    )
    assert "edit" in actions
    assert "cancel" in actions
    assert "start" not in actions  # solicitante não atende


def test_processor_full_lifecycle(seed):
    _, _, workflow = seed
    engine = WorkflowEngine()
    processor = _processor()
    request = _request("submitted")

    result = engine.apply_transition(
        request=request, actor=processor, workflow=workflow, action="start"
    )
    assert result.request.status == "in_progress"
    assert result.assignment is not None
    assert result.assignment.assignee_user_id == "proc-1"

    request = result.request
    with pytest.raises(WorkflowEngineError) as exc:
        engine.apply_transition(
            request=request, actor=processor, workflow=workflow, action="return"
        )
    assert exc.value.code == "missing_field"

    result = engine.apply_transition(
        request=request,
        actor=processor,
        workflow=workflow,
        action="return",
        body={"return_reason": "Falta detalhar o escopo."},
    )
    assert result.request.status == "needs_information"
    assert result.request.return_reason == "Falta detalhar o escopo."

    request = result.request
    result = engine.apply_transition(
        request=request, actor=_owner(), workflow=workflow, action="resubmit"
    )
    assert result.request.status == "submitted"
    assert result.request.return_reason is None

    result = engine.apply_transition(
        request=result.request, actor=processor, workflow=workflow, action="complete"
    )
    assert result.request.status == "completed"
    assert result.request.completed_by_user_id == "proc-1"


def test_flexible_complete_from_submitted(seed):
    """Nada engessado: processador pode concluir direto da fila."""
    _, _, workflow = seed
    result = WorkflowEngine().apply_transition(
        request=_request("submitted"),
        actor=_processor(),
        workflow=workflow,
        action="complete",
    )
    assert result.request.status == "completed"


def test_owner_cannot_process(seed):
    _, _, workflow = seed
    engine = WorkflowEngine()
    request = _request("submitted")
    for action in ("start", "return", "complete"):
        with pytest.raises(WorkflowEngineError) as exc:
            engine.apply_transition(
                request=request, actor=_owner(), workflow=workflow, action=action
            )
        assert exc.value.code in {"forbidden", "invalid_transition", "missing_field"}


def test_cancel_requires_justification_and_owner(seed):
    _, _, workflow = seed
    engine = WorkflowEngine()
    request = _request("submitted")

    # Outro usuário com create não cancela solicitação alheia.
    with pytest.raises(WorkflowEngineError) as exc:
        engine.apply_transition(
            request=request, actor=_other_user(), workflow=workflow, action="cancel"
        )
    assert exc.value.code == "forbidden"

    with pytest.raises(WorkflowEngineError) as exc:
        engine.apply_transition(
            request=request, actor=_owner(), workflow=workflow, action="cancel"
        )
    assert exc.value.code == "missing_field"

    result = engine.apply_transition(
        request=request,
        actor=_owner(),
        workflow=workflow,
        action="cancel",
        body={"cancel_justification": "Resolvi por outro caminho."},
    )
    assert result.request.status == "cancelled"
    assert result.request.cancelled_at is not None


# --- notificações ao solicitante -------------------------------------------


def test_creator_notified_on_key_transitions(seed):
    _, _, workflow = seed
    owner = _owner()
    assert should_notify_creator_on_transition(
        workflow=workflow,
        from_status="submitted",
        to_status="in_progress",
        actor_user_id="proc-1",
        owner_user_id=owner.user_id,
    )
    assert should_notify_creator_on_transition(
        workflow=workflow,
        from_status="in_progress",
        to_status="needs_information",
        actor_user_id="proc-1",
        owner_user_id=owner.user_id,
    )
    for terminal in ("completed", "cancelled"):
        assert should_notify_creator_on_transition(
            workflow=workflow,
            from_status="in_progress",
            to_status=terminal,
            actor_user_id="proc-1",
            owner_user_id=owner.user_id,
        )


def test_creator_not_notified_on_resubmit_or_own_action(seed):
    _, _, workflow = seed
    assert not should_notify_creator_on_transition(
        workflow=workflow,
        from_status="needs_information",
        to_status="submitted",
        actor_user_id="user-1",
        owner_user_id="user-1",
    )


def test_queue_notification_targets_process_permission(seed):
    form_schema, _, workflow = seed
    assert form_schema.get("required") == ["title", "description"]
    title, message, _kind = resolve_queue_created_copy(
        type_name="Solicitação Diversa",
        request_number="REQ-1",
    )
    assert "fila" in title
    assert "REQ-1" in message and "Solicitação Diversa" in message


def test_queue_created_copy_includes_requester_and_ticket_title():
    """O corpo do alerta de fila deve dizer quem abriu e qual o assunto."""
    title, message, _kind = resolve_queue_created_copy(
        type_name="Processos — Abertura de Chamado",
        request_number="REQ-2026-000004",
        requester_name="Michael Marotto",
        request_title="Impressão de gabarito",
    )
    assert "fila" in title
    assert "Michael Marotto" in message
    assert "Impressão de gabarito" in message
    assert "REQ-2026-000004" in message


def test_queue_created_copy_requester_without_ticket_title():
    """Tipos sem campo title no payload mantêm o formato anterior."""
    _title, message, _kind = resolve_queue_created_copy(
        type_name="Solicitação Diversa",
        request_number="REQ-2",
        requester_name="Ana",
    )
    assert message.startswith("Ana abriu")
    assert "REQ-2 (Solicitação Diversa)" in message
    assert "aguarda atendimento" in message
