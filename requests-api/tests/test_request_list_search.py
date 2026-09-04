"""E11 — busca textual nas listas mine / work-queue."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    ListMyRequestsUseCase,
    ListWorkQueueRequestsUseCase,
)
from requests_app.domain.services.request_list_search import (
    ilike_contains_pattern,
    normalize_list_search_query,
    request_matches_search,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)


def _user(*, user_id: str = "u-create", permissions: list[str] | None = None):
    return SimpleNamespace(
        id=user_id,
        name="Usuário Teste",
        permissions=permissions
        or [
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            "my-requests.view.filial-01",
        ],
    )


def _processor():
    return _user(
        user_id="u-process",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
        ],
    )


def _harness():
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
    return types, requests, idem


def test_normalize_list_search_query_min_length():
    assert normalize_list_search_query(None) is None
    assert normalize_list_search_query("") is None
    assert normalize_list_search_query(" a ") is None
    assert normalize_list_search_query("ab") == "ab"
    assert normalize_list_search_query("  Delpi  ") == "Delpi"


def test_ilike_contains_pattern_escapes_wildcards():
    assert ilike_contains_pattern("a%b_c") == r"%a\%b\_c%"


def test_request_matches_search_number_and_payload_keys():
    assert request_matches_search(
        request_number="REQ-2026-0042",
        payload={"party_name": "Acme Ltda"},
        q="0042",
    )
    assert request_matches_search(
        request_number="REQ-1",
        payload={"party_name": "Cliente Delpi"},
        q="delpi",
    )
    assert request_matches_search(
        request_number="REQ-1",
        payload={"party_code": "C0001"},
        q="c0001",
    )
    assert request_matches_search(
        request_number="REQ-1",
        payload={"description": "Pedido urgente"},
        q="urgente",
    )
    assert not request_matches_search(
        request_number="REQ-1",
        payload={"other": "não indexado"},
        q="indexado",
    )


def test_list_mine_search_by_number_and_party_name():
    types, requests, idem = _harness()
    CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"party_name": "Metalúrgica Alfa", "party_code": "A100"},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"party_name": "Outro Cliente", "description": "frete CIF"},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )

    uc = ListMyRequestsUseCase(types, requests)
    all_mine = uc.execute(user=_user())
    assert all_mine["total"] == 2

    by_party = uc.execute(user=_user(), q="alfa")
    assert by_party["total"] == 1
    assert by_party["items"][0]["payload"]["party_name"] == "Metalúrgica Alfa"

    number = all_mine["items"][0]["request_number"]
    fragment = number[-4:]
    by_number = uc.execute(user=_user(), q=fragment)
    assert by_number["total"] >= 1
    assert any(row["request_number"] == number for row in by_number["items"])

    short = uc.execute(user=_user(), q="a")
    assert short["total"] == 2


def test_list_work_queue_search_by_description():
    types, requests, idem = _harness()
    CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"description": "urgente exportação"},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"description": "rotina mensal"},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )

    queue = ListWorkQueueRequestsUseCase(types, requests).execute(
        user=_processor(), q="export"
    )
    assert queue["total"] == 1
    assert "exportação" in (queue["items"][0]["payload"].get("description") or "")
