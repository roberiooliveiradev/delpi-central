from __future__ import annotations

from requests_app.domain.services.creator_portal_notification_policy import (
    resolve_creator_gate_copy,
    should_notify_creator_on_transition,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry


def _invoice_workflow() -> dict:
    return RequestTypeRegistry.from_workflow_content(
        code="invoice-issuance",
        name="Emissão NF",
        workflow_name="invoice_issuance",
        permission_prefix="my-requests.invoice-issuance",
        branch_scope="required",
    ).workflow_definition


def _generic_workflow() -> dict:
    return RequestTypeRegistry.from_workflow_content(
        code="generic-simple",
        name="Genérico",
        workflow_name="generic_simple",
        permission_prefix="my-requests.generic-simple",
        branch_scope="optional",
    ).workflow_definition


def test_positive_start_by_processor_notifies_creator():
    assert should_notify_creator_on_transition(
        workflow=_invoice_workflow(),
        from_status="submitted",
        to_status="in_progress",
        actor_user_id="proc",
        owner_user_id="owner",
    )


def test_positive_return_complete_reject_cancel_by_processor():
    workflow = _invoice_workflow()
    for to_status in (
        "needs_information",
        "awaiting_requester_confirmation",
        "completed",
        "rejected",
        "cancelled",
    ):
        assert should_notify_creator_on_transition(
            workflow=workflow,
            from_status="in_progress",
            to_status=to_status,
            actor_user_id="proc",
            owner_user_id="owner",
        )


def test_creator_gate_copy_confirmation_awaiting():
    title, message, variant = resolve_creator_gate_copy(
        workflow=_invoice_workflow(),
        to_status="awaiting_requester_confirmation",
        request_number="REQ-9",
        actor_name="Proc",
    )
    assert title == "Confirme o atendimento"
    assert "REQ-9" in message
    assert variant == "warning"


def test_negative_owner_self_transition_skipped():
    assert not should_notify_creator_on_transition(
        workflow=_invoice_workflow(),
        from_status="needs_information",
        to_status="submitted",
        actor_user_id="owner",
        owner_user_id="owner",
    )
    assert not should_notify_creator_on_transition(
        workflow=_invoice_workflow(),
        from_status="submitted",
        to_status="cancelled",
        actor_user_id="owner",
        owner_user_id="owner",
    )


def test_sibling_without_journey_uses_fallback():
    workflow = _generic_workflow()
    assert "journey" not in workflow
    assert should_notify_creator_on_transition(
        workflow=workflow,
        from_status="submitted",
        to_status="in_progress",
        actor_user_id="proc",
        owner_user_id="owner",
    )
    assert should_notify_creator_on_transition(
        workflow=workflow,
        from_status="in_progress",
        to_status="completed",
        actor_user_id="proc",
        owner_user_id="owner",
    )
    assert not should_notify_creator_on_transition(
        workflow=workflow,
        from_status="submitted",
        to_status="cancelled",
        actor_user_id="owner",
        owner_user_id="owner",
    )


def test_creator_gate_copy_waiting_and_completed():
    title, message, variant = resolve_creator_gate_copy(
        workflow=_invoice_workflow(),
        to_status="needs_information",
        request_number="REQ-1",
        actor_name="Proc",
    )
    assert title == "Aguardando sua informação"
    assert "REQ-1" in message
    assert variant == "warning"

    title, message, variant = resolve_creator_gate_copy(
        workflow=_invoice_workflow(),
        to_status="completed",
        request_number="REQ-2",
        actor_name="Proc",
    )
    assert title == "Solicitação concluída"
    assert variant == "success"
