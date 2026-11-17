"""List sort contract for mine / work-queue (sort=field:dir[,field:dir])."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.use_cases.request_use_cases import (
    ListMyRequestsUseCase,
    ListWorkQueueRequestsUseCase,
)
from requests_app.domain.entities import Request
from requests_app.domain.services.request_list_sort import (
    LIST_SORT_MAX_LEVELS,
    parse_list_sort,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)

_BASE = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)


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


def _harness() -> tuple[
    InMemoryRequestTypeRepository, InMemoryRequestRepository
]:
    invoice = RequestTypeRegistry.from_workflow_content(
        code="invoice-issuance",
        name="Emissão NF",
        workflow_name="invoice_issuance",
        permission_prefix="my-requests.invoice-issuance",
        branch_scope="required",
    )
    types = InMemoryRequestTypeRepository([invoice])
    requests = InMemoryRequestRepository()
    return types, requests


def _seed(
    requests: InMemoryRequestRepository,
    *,
    number: str,
    status: str,
    branch: str | None,
    minutes_old: int,
    user_id: str = "u-create",
    type_code: str = "invoice-issuance",
) -> None:
    rid = uuid4()
    requests._requests[str(rid)] = Request(
        id=rid,
        request_number=number,
        request_type_id=rid,
        type_code=type_code,
        status=status,
        created_by_user_id=user_id,
        created_by_name="Usuário Teste",
        branch_code=branch,
        created_at=_BASE - timedelta(minutes=minutes_old),
        updated_at=_BASE - timedelta(minutes=minutes_old),
    )


def test_parse_list_sort_levels():
    assert parse_list_sort(None) is None
    assert parse_list_sort("") is None
    assert parse_list_sort("created_at:asc") == [("created_at", "asc")]
    assert parse_list_sort("status:asc,created_at:desc") == [
        ("status", "asc"),
        ("created_at", "desc"),
    ]
    assert parse_list_sort("branch") == [("branch", "asc")]


def test_parse_list_sort_rejects_bad_input():
    for bad in (
        "payload:desc",          # not whitelisted
        "created_at:sideways",   # bad direction
        "status:asc,status:desc",  # duplicate field
        ",".join(["status"] * (LIST_SORT_MAX_LEVELS + 1)),
    ):
        with pytest.raises(ValueError):
            parse_list_sort(bad)


def test_list_mine_sort_created_at_asc_and_desc():
    types, requests = _harness()
    _seed(requests, number="REQ-001", status="submitted", branch="01", minutes_old=30)
    _seed(requests, number="REQ-002", status="submitted", branch="01", minutes_old=10)
    _seed(requests, number="REQ-003", status="submitted", branch="01", minutes_old=20)

    uc = ListMyRequestsUseCase(types, requests)
    desc = uc.execute(user=_user())
    assert [r["request_number"] for r in desc["items"]] == [
        "REQ-002", "REQ-003", "REQ-001",
    ]
    asc = uc.execute(user=_user(), sort="created_at:asc")
    assert [r["request_number"] for r in asc["items"]] == [
        "REQ-001", "REQ-003", "REQ-002",
    ]


def test_list_mine_sort_multi_level_and_validation():
    types, requests = _harness()
    _seed(requests, number="REQ-A", status="in_progress", branch="01", minutes_old=10)
    _seed(requests, number="REQ-B", status="submitted", branch="01", minutes_old=5)
    _seed(requests, number="REQ-C", status="in_progress", branch="01", minutes_old=20)

    uc = ListMyRequestsUseCase(types, requests)
    rows = uc.execute(user=_user(), sort="status:asc,created_at:desc")
    assert [r["request_number"] for r in rows["items"]] == [
        "REQ-A", "REQ-C", "REQ-B",  # in_progress (asc) por data desc, depois submitted
    ]
    with pytest.raises(ApplicationError) as err:
        uc.execute(user=_user(), sort="nonsense:asc")
    assert err.value.code == "invalid_sort"
    assert err.value.status_code == 422


def test_list_work_queue_sort_branch_then_date():
    types, requests = _harness()
    processor = _user(
        user_id="u-process",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
            "my-requests.view.filial-02",
        ],
    )
    _seed(requests, number="REQ-1", status="submitted", branch="02", minutes_old=5)
    _seed(requests, number="REQ-2", status="submitted", branch="01", minutes_old=15)
    _seed(requests, number="REQ-3", status="submitted", branch="01", minutes_old=3)

    uc = ListWorkQueueRequestsUseCase(types, requests)
    rows = uc.execute(user=processor, sort="branch:asc,created_at:desc")
    assert [r["request_number"] for r in rows["items"]] == [
        "REQ-3", "REQ-2", "REQ-1",  # filial 01 (data desc) antes de 02
    ]


def _processor() -> object:
    return _user(
        user_id="u-process",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
        ],
    )


def test_list_work_queue_sort_requester_and_completed_by():
    types, requests = _harness()
    seed_data = [
        ("REQ-1", "Zuleica", "Bruno"),
        ("REQ-2", "Ana", None),
        ("REQ-3", "Mario", "Ana"),
    ]
    for number, requester, completed_by in seed_data:
        rid = uuid4()
        requests._requests[str(rid)] = Request(
            id=rid,
            request_number=number,
            request_type_id=rid,
            type_code="invoice-issuance",
            status="submitted",
            created_by_user_id="u-create",
            created_by_name=requester,
            completed_by_name=completed_by,
            branch_code="01",
            created_at=_BASE,
            updated_at=_BASE,
        )

    uc = ListWorkQueueRequestsUseCase(types, requests)

    rows = uc.execute(user=_processor(), sort="requester:asc")
    assert [r["request_number"] for r in rows["items"]] == [
        "REQ-2", "REQ-3", "REQ-1",  # Ana < Mario < Zuleica
    ]

    rows = uc.execute(user=_processor(), sort="completed_by:desc")
    assert [r["request_number"] for r in rows["items"]] == [
        "REQ-1", "REQ-3", "REQ-2",  # Bruno > Ana > pendente ("" por último)
    ]
