"""Plugabilidade E7 — raw-material-creation sem alterar WorkflowEngine."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.services.payload_validator_registry import (
    PayloadValidatorRegistry,
)
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    ListWorkQueueRequestsUseCase,
    TransitionRequestUseCase,
)
from requests_app.domain.services.form_schema_payload_validation_service import (
    FormSchemaPayloadValidationService,
)
from requests_app.domain.services.invoice_issuance_payload_validator import (
    InvoiceIssuancePayloadValidator,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.domain.services.workflow_engine import WorkflowEngine
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "requests_app" / "domain" / "services" / "workflow_engine.py"

FORM_SCHEMA = {
    "type": "object",
    "required": ["description", "unit"],
    "properties": {
        "description": {"type": "string", "minLength": 1, "title": "Descrição"},
        "unit": {"type": "string", "enum": ["UN", "KG", "M"], "title": "Unidade"},
        "notes": {"type": "string", "title": "Observações"},
    },
    "additionalProperties": False,
}


def _raw_type():
    return RequestTypeRegistry.from_workflow_content(
        code="raw-material-creation",
        name="Criação de MP",
        workflow_name="raw_material_creation",
        permission_prefix="my-requests.raw-material-creation",
        presentation_mode="schema_driven",
        branch_scope="optional",
        form_schema=FORM_SCHEMA,
        ui_schema={"notes": {"widget": "textarea"}},
    )


def _creator():
    return SimpleNamespace(
        id="u-create",
        name="Engenharia",
        permissions=[
            "my-requests.access",
            "my-requests.raw-material-creation.create",
        ],
    )


def _processor():
    return SimpleNamespace(
        id="u-process",
        name="Processador",
        permissions=[
            "my-requests.access",
            "my-requests.raw-material-creation.process",
        ],
    )


def _stack():
    types = InMemoryRequestTypeRepository([_raw_type()])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    registry = PayloadValidatorRegistry()
    registry.register(InvoiceIssuancePayloadValidator())
    return types, requests, idem, registry


def test_workflow_engine_has_no_raw_material_branch():
    """Critério §11.3: engine não conhece type codes de domínio."""
    source = ENGINE_PATH.read_text(encoding="utf-8")
    assert "raw-material" not in source
    assert "invoice-issuance" not in source
    assert "if request_type" not in source
    assert "type_code ==" not in source


def test_form_schema_rejects_missing_required():
    svc = FormSchemaPayloadValidationService()
    with pytest.raises(ApplicationError) as exc:
        svc.validate({"unit": "UN"}, FORM_SCHEMA)
    assert exc.value.status_code == 422
    assert exc.value.code == "payload_invalid"


def test_form_schema_rejects_invalid_enum():
    svc = FormSchemaPayloadValidationService()
    with pytest.raises(ApplicationError) as exc:
        svc.validate({"description": "Aço", "unit": "LT"}, FORM_SCHEMA)
    assert exc.value.status_code == 422


def test_registry_uses_form_schema_when_no_typed_validator():
    registry = PayloadValidatorRegistry()
    registry.register(InvoiceIssuancePayloadValidator())
    out = registry.validate(
        "raw-material-creation",
        {"description": "Parafuso", "unit": "UN", "notes": "M6"},
        form_schema=FORM_SCHEMA,
    )
    assert out["description"] == "Parafuso"
    assert out["unit"] == "UN"


def test_create_list_start_complete_raw_material():
    types, requests, idem, registry = _stack()
    created = CreateRequestUseCase(types, requests, idem, validators=registry).execute(
        user=_creator(),
        type_code="raw-material-creation",
        payload={"description": "Chapa 2mm", "unit": "KG", "notes": ""},
        idempotency_key=str(uuid4()),
    )
    assert created["type_code"] == "raw-material-creation"
    assert created["status"] == "submitted"
    assert created["payload"]["unit"] == "KG"

    queue = ListWorkQueueRequestsUseCase(types, requests).execute(user=_processor())
    assert queue["total"] == 1

    started = TransitionRequestUseCase(types, requests, idem).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    assert started["status"] == "in_progress"

    completed = TransitionRequestUseCase(types, requests, idem).execute(
        user=_processor(),
        request_id=created["id"],
        action="complete",
        idempotency_key=str(uuid4()),
    )
    assert completed["status"] == "completed"


def test_create_incomplete_payload_422():
    types, requests, idem, registry = _stack()
    with pytest.raises(ApplicationError) as exc:
        CreateRequestUseCase(types, requests, idem, validators=registry).execute(
            user=_creator(),
            type_code="raw-material-creation",
            payload={"description": "Sem unidade"},
            idempotency_key=str(uuid4()),
        )
    assert exc.value.status_code == 422


def test_engine_computes_raw_material_actions():
    engine = WorkflowEngine()
    workflow = _raw_type().workflow_definition
    from requests_app.domain.entities import Actor, Request

    request = Request(
        id=uuid4(),
        request_number="REQ-MP-1",
        request_type_id=uuid4(),
        type_code="raw-material-creation",
        status="submitted",
        created_by_user_id="u-create",
        created_by_name="E",
        version=1,
    )
    actions = set(
        engine.compute_allowed_actions(
            request=request,
            actor=Actor(
                user_id="u-process",
                user_name="P",
                has_process=True,
                has_access=True,
            ),
            workflow=workflow,
        )
    )
    assert actions == {"view", "start"}
