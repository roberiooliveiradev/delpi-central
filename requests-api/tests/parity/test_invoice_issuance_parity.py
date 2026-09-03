"""Paridade P0 — invoice-issuance legado × requests-api (Playbook §20.3).

Cobre fluxos automatizáveis com in-memory stack. Gaps live (TOTVS real / dual-run
homologação) estão listados em docs/.../PARITY-P0.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.services.payload_validator_registry import (
    PayloadValidatorRegistry,
)
from requests_app.application.use_cases.invoice_issuance_lookup_use_cases import (
    InvoiceIssuanceLookupUseCases,
)
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    GetRequestUseCase,
    ListWorkQueueRequestsUseCase,
    TransitionRequestUseCase,
    UpdateRequestPayloadUseCase,
)
from requests_app.domain.services.content_loader import load_workflow_definition
from requests_app.domain.services.invoice_issuance_payload_validator import (
    InvoiceIssuancePayloadValidator,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.domain.services.workflow_engine import WorkflowEngine
from requests_app.domain.entities import Actor, Request
from requests_app.infrastructure.gateways.api_delpi_adapter import (
    InMemoryOperationalLookupAdapter,
)
from requests_app.infrastructure.persistence.repositories.memory_outbox_repository import (
    InMemoryIntegrationOutboxRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)

FIXTURES = Path(__file__).parent / "fixtures" / "invoice_issuance_lookup_shapes.json"

# Aliases espelhados do legado (pending / returned / issued).
LEGACY_STATUS_ALIASES = {
    "submitted": "pending",
    "needs_information": "returned",
    "completed": "issued",
}


def _sale_payload() -> dict:
    return {
        "party_type": "customer",
        "party_code": "C001",
        "party_store": "01",
        "party_name": "Cliente Teste",
        "invoice_type": "sale",
        "freight_mode": "cif",
        "weight_kg": 1.5,
        "volume_count": 1,
        "items": [
            {
                "product_code": "P001",
                "product_description": "Item único",
                "quantity": 1,
                "unit_price": 10,
            }
        ],
    }


def _creator(**kwargs):
    base = dict(
        id="u-create",
        name="Solicitante",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            "my-requests.view.filial-01",
        ],
        access_token="Bearer test",
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _processor(**kwargs):
    base = dict(
        id="u-process",
        name="Faturamento",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
        ],
        access_token="Bearer test",
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


@pytest.fixture
def stack():
    invoice = RequestTypeRegistry.from_workflow_content(
        code="invoice-issuance",
        name="Emissão NF",
        workflow_name="invoice_issuance",
        permission_prefix="my-requests.invoice-issuance",
        branch_scope="required",
    )
    types = InMemoryRequestTypeRepository([invoice])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    registry = PayloadValidatorRegistry()
    registry.register(InvoiceIssuancePayloadValidator())
    outbox = InMemoryIntegrationOutboxRepository()
    lookups = InMemoryOperationalLookupAdapter()
    return SimpleNamespace(
        types=types,
        requests=requests,
        idem=idem,
        validators=registry,
        outbox=outbox,
        lookups=lookups,
    )


def _create(stack, user=None, payload=None, outbox=False):
    return CreateRequestUseCase(
        stack.types,
        stack.requests,
        stack.idem,
        validators=stack.validators,
        outbox=stack.outbox if outbox else None,
    ).execute(
        user=user or _creator(),
        type_code="invoice-issuance",
        branch_code="01",
        payload=payload or _sale_payload(),
        idempotency_key=str(uuid4()),
    )


# --- §20.3 casos -------------------------------------------------------------


def test_p0_status_aliases_match_legacy():
    workflow = load_workflow_definition("invoice_issuance")
    assert workflow["statusAliases"] == LEGACY_STATUS_ALIASES


def test_p0_create_sale_one_item(stack):
    """Criar solicitação venda 1 item — legado POST requests ≡ POST /v1/requests."""
    created = _create(stack)
    assert created["type_code"] == "invoice-issuance"
    assert created["status"] == "submitted"
    assert created["status_alias"] == "pending"
    assert len(created["payload"]["items"]) == 1
    assert created["payload"]["items"][0]["product_code"] == "P001"
    assert "cancel" in created["allowed_actions"]


def test_p0_work_queue_lists_pending(stack):
    """Listar fila pending — legado GET ?status=open ≡ GET work-queue."""
    _create(stack)
    queue = ListWorkQueueRequestsUseCase(stack.types, stack.requests).execute(
        user=_processor()
    )
    assert queue["total"] == 1
    assert queue["items"][0]["status"] == "submitted"
    assert queue["items"][0]["status_alias"] == "pending"


def test_p0_start_then_issue_complete(stack):
    """start → issue — legado POST start/issue ≡ transitions start + complete|issue."""
    created = _create(stack)
    started = TransitionRequestUseCase(
        stack.types, stack.requests, stack.idem
    ).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    assert started["status"] == "in_progress"
    assert {"complete", "issue"} <= set(started["allowed_actions"])

    issued = TransitionRequestUseCase(
        stack.types, stack.requests, stack.idem
    ).execute(
        user=_processor(),
        request_id=created["id"],
        action="issue",
        idempotency_key=str(uuid4()),
    )
    assert issued["status"] == "completed"
    assert issued["status_alias"] == "issued"


def test_p0_return_patch_resubmit(stack):
    """return → edit → resubmit."""
    created = _create(stack)
    TransitionRequestUseCase(stack.types, stack.requests, stack.idem).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    returned = TransitionRequestUseCase(
        stack.types, stack.requests, stack.idem
    ).execute(
        user=_processor(),
        request_id=created["id"],
        action="return",
        body={"return_reason": "Corrigir quantidade"},
        idempotency_key=str(uuid4()),
    )
    assert returned["status"] == "needs_information"
    assert returned["status_alias"] == "returned"

    patched_payload = _sale_payload()
    patched_payload["items"][0]["quantity"] = 2
    edited = UpdateRequestPayloadUseCase(
        stack.types, stack.requests, stack.idem, validators=stack.validators
    ).execute(
        user=_creator(),
        request_id=created["id"],
        payload=patched_payload,
        idempotency_key=str(uuid4()),
    )
    assert float(edited["payload"]["items"][0]["quantity"]) == 2.0
    assert "edit" in edited["allowed_actions"]

    resubmitted = TransitionRequestUseCase(
        stack.types, stack.requests, stack.idem
    ).execute(
        user=_creator(),
        request_id=created["id"],
        action="resubmit",
        idempotency_key=str(uuid4()),
    )
    assert resubmitted["status"] == "submitted"
    assert resubmitted["status_alias"] == "pending"


def test_p0_cancel_pending_owner(stack):
    created = _create(stack)
    cancelled = TransitionRequestUseCase(
        stack.types, stack.requests, stack.idem
    ).execute(
        user=_creator(),
        request_id=created["id"],
        action="cancel",
        body={"cancel_justification": "Desistiu"},
        idempotency_key=str(uuid4()),
    )
    assert cancelled["status"] == "cancelled"


def test_p0_cancel_in_progress_processor(stack):
    created = _create(stack)
    TransitionRequestUseCase(stack.types, stack.requests, stack.idem).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    cancelled = TransitionRequestUseCase(
        stack.types, stack.requests, stack.idem
    ).execute(
        user=_processor(),
        request_id=created["id"],
        action="cancel",
        body={"cancel_justification": "Duplicidade"},
        idempotency_key=str(uuid4()),
    )
    assert cancelled["status"] == "cancelled"


@pytest.mark.parametrize(
    "status,actor_factory,expected",
    [
        ("submitted", lambda: Actor(user_id="c", user_name="C", has_create=True, has_access=True), {"view", "cancel"}),
        ("submitted", lambda: Actor(user_id="p", user_name="P", has_process=True, has_access=True), {"view", "start"}),
        (
            "in_progress",
            lambda: Actor(user_id="p", user_name="P", has_process=True, has_access=True),
            {"view", "return", "complete", "issue", "cancel"},
        ),
        (
            "needs_information",
            lambda: Actor(user_id="c", user_name="C", has_create=True, has_access=True),
            {"view", "edit", "resubmit"},
        ),
    ],
)
def test_p0_allowed_actions_by_role(status, actor_factory, expected):
    engine = WorkflowEngine()
    workflow = load_workflow_definition("invoice_issuance")
    request = Request(
        id=uuid4(),
        request_number="REQ-PARITY-1",
        request_type_id=uuid4(),
        type_code="invoice-issuance",
        status=status,
        created_by_user_id="c",
        created_by_name="C",
        version=1,
    )
    actor = actor_factory()
    if actor.has_create:
        request.created_by_user_id = actor.user_id
    actions = set(
        engine.compute_allowed_actions(request=request, actor=actor, workflow=workflow)
    )
    assert actions == expected


def test_p0_branch_gate_403(stack):
    user = _creator(
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            # sem my-requests.view.filial-01
        ]
    )
    with pytest.raises(ApplicationError) as exc:
        CreateRequestUseCase(
            stack.types, stack.requests, stack.idem, validators=stack.validators
        ).execute(
            user=user,
            type_code="invoice-issuance",
            branch_code="01",
            payload=_sale_payload(),
            idempotency_key=str(uuid4()),
        )
    assert exc.value.status_code == 403
    assert exc.value.code == "branch_forbidden"


def test_p0_notification_outbox_on_create(stack):
    created = _create(stack, outbox=True)
    pending = stack.outbox.list_pending()
    assert len(pending) == 1
    assert pending[0].event_type == "request.created"
    assert pending[0].payload["category"] == "my_requests"
    assert pending[0].request_id == created["id"]


def test_p0_lookup_shapes_match_golden(stack):
    """Lookups via adapter — chaves canônicas ≡ fixture golden (espelho api-delpi)."""
    golden = json.loads(FIXTURES.read_text(encoding="utf-8"))
    uc = InvoiceIssuanceLookupUseCases(stack.types, stack.lookups)
    user = _creator()

    parties = uc.search_parties(user=user, party_type="customer", query="cli")
    assert set(golden["parties"]["required_item_keys"]) <= set(parties["items"][0].keys())

    products = uc.search_products(user=user, query="prod")
    assert set(golden["products"]["required_item_keys"]) <= set(products["items"][0].keys())

    carriers = uc.search_carriers(user=user, query="trans")
    assert set(golden["carriers"]["required_item_keys"]) <= set(carriers["items"][0].keys())

    orders = uc.list_open_sales_orders(
        user=user, branch="01", party_code="C001", party_store="01"
    )
    assert set(golden["open_sales_orders"]["required_keys"]) <= set(orders.keys())

    balance = uc.warehouse_balance(user=user, product_code="P001", branch="01")
    assert set(golden["warehouse_01_balance"]["required_keys"]) <= set(balance.keys())
    assert balance["warehouse"] == "01"


def test_p0_get_detail_exposes_issue_alias(stack):
    created = _create(stack)
    TransitionRequestUseCase(stack.types, stack.requests, stack.idem).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    detail = GetRequestUseCase(stack.types, stack.requests).execute(
        user=_processor(), request_id=created["id"]
    )
    assert "issue" in detail["allowed_actions"]
    assert "complete" in detail["allowed_actions"]
