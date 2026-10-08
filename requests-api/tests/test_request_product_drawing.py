"""P4 — GET /v1/requests/{id}/product-drawing (desenho do PA do process-issue).

Cobre:
* autorização idêntica ao detalhe (owner / view-all / process / manage);
* escopo de filial por registro (P1);
* somente type_code=process-issue tem desenho;
* PA vem SEMPRE do payload persistido — nunca de parâmetro do cliente;
* PDF inline + filename; desenho inexistente 404; biblioteca 503;
* token interno jamais exposto na resposta.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from requests_app.application.errors import ApplicationError
from requests_app.application.use_cases.request_drawing_use_case import (
    GetRequestProductDrawingUseCase,
)
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
)
from requests_app.domain.process_issue_catalog import PROCESS_ISSUE_TYPE_CODE
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.gateways.api_delpi_product_drawing_gateway import (  # noqa: E501
    InMemoryProductDrawingGateway,
)
from requests_app.infrastructure.persistence.repositories.memory_outbox_repository import (  # noqa: E501
    InMemoryIntegrationOutboxRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (  # noqa: E501
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)
from requests_app.interface.http.routes import requests_routes


def _payload(**overrides):
    operation = {
        "productionOrder": "24640401002",
        "operationCode": "03",
        "description": "MONTAGEM",
        "reportedWorkCenter": "CT-63",
        "productCode": "10045678",
        "paProductCode": "90264238",
    }
    base = {
        "source": "operator_cockpit",
        "reportedAt": "2026-10-08T12:00:00+00:00",
        "issue": {"code": "tool_not_linked"},
        "operator": {"code": "001234", "name": "Maria Silva"},
        "operation": operation,
        "materialsSnapshotAvailable": True,
        "materials": [],
    }
    base.update(overrides)
    return base


def _type(code=PROCESS_ISSUE_TYPE_CODE, prefix="my-requests.process-issue"):
    return RequestTypeRegistry.from_workflow_content(
        code=code,
        name="Tipo",
        workflow_name=(
            "process_issue" if code == PROCESS_ISSUE_TYPE_CODE else "invoice_issuance"
        ),
        permission_prefix=prefix,
        branch_scope="required",
    )


PROCESSOR = SimpleNamespace(
    id="u-proc",
    name="Analista",
    permissions=[
        "my-requests.access",
        "my-requests.process-issue.process",
        "my-requests.view.filial-02",
    ],
)
PROCESSOR_OTHER_BRANCH = SimpleNamespace(
    id="u-proc-01",
    name="Analista Filial 01",
    permissions=[
        "my-requests.access",
        "my-requests.process-issue.process",
        "my-requests.view.filial-01",
    ],
)
PLAIN_USER = SimpleNamespace(
    id="u-plain", name="Sem Permissão", permissions=["my-requests.access"]
)


@pytest.fixture
def harness():
    types = InMemoryRequestTypeRepository([_type()])
    requests = InMemoryRequestRepository()
    create = CreateRequestUseCase(
        types, requests, InMemoryIdempotencyRepository(),
        outbox=InMemoryIntegrationOutboxRepository(),
    )
    created = create.execute_external(
        requester_id="operator:02:12345",
        requester_name="Maria Silva",
        type_code=PROCESS_ISSUE_TYPE_CODE,
        payload=_payload(),
        branch_code="02",
        idempotency_key=str(uuid4()),
    )
    gateway = InMemoryProductDrawingGateway()
    uc = GetRequestProductDrawingUseCase(types, requests, gateway)
    return types, requests, created, gateway, uc


def test_drawing_resolves_pa_from_persisted_payload(harness):
    *_, created, gateway, uc = harness
    drawing = uc.execute(user=PROCESSOR, request_id=created["id"])
    assert gateway.calls == ["90264238"]
    assert drawing.content.startswith(b"%PDF")
    assert drawing.filename == "90264238.pdf"
    assert drawing.media_type == "application/pdf"


def test_drawing_requires_request_detail_access(harness):
    *_, created, _g, uc = harness
    with pytest.raises(ApplicationError) as exc:
        uc.execute(user=PLAIN_USER, request_id=created["id"])
    assert exc.value.code == "forbidden"
    assert exc.value.status_code == 403


def test_drawing_respects_branch_scope(harness):
    *_, created, _g, uc = harness
    with pytest.raises(ApplicationError) as exc:
        uc.execute(user=PROCESSOR_OTHER_BRANCH, request_id=created["id"])
    assert exc.value.code == "branch_forbidden"


def test_drawing_404_unknown_request(harness):
    *_, _r, _c, _g, uc = harness
    with pytest.raises(ApplicationError) as exc:
        uc.execute(user=PROCESSOR, request_id=str(uuid4()))
    assert exc.value.code == "not_found"


def test_drawing_not_applicable_to_other_types(harness):
    types, requests = harness[0], harness[1]
    types.save(
        _type(code="invoice-issuance", prefix="my-requests.invoice-issuance")
    )
    create = CreateRequestUseCase(
        types, requests, InMemoryIdempotencyRepository(),
        outbox=InMemoryIntegrationOutboxRepository(),
    )
    other = create.execute(
        user=SimpleNamespace(
            id="u-user",
            name="User",
            permissions=[
                "my-requests.invoice-issuance.create",
                "my-requests.view.filial-02",
            ],
        ),
        type_code="invoice-issuance",
        payload={},
        branch_code="02",
        idempotency_key=str(uuid4()),
    )
    *_, gateway, uc = harness
    viewer = SimpleNamespace(
        id="u-viewer",
        name="Viewer",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-02",
        ],
    )
    with pytest.raises(ApplicationError) as exc:
        uc.execute(user=viewer, request_id=other["id"])
    assert exc.value.code == "drawing_not_applicable"
    assert gateway.calls == []


def test_drawing_404_when_pa_missing(harness):
    types, requests, _created, gateway, _uc = harness
    create = CreateRequestUseCase(
        types, requests, InMemoryIdempotencyRepository(),
        outbox=InMemoryIntegrationOutboxRepository(),
    )
    without_pa = create.execute_external(
        requester_id="operator:02:99999",
        requester_name="Joao",
        type_code=PROCESS_ISSUE_TYPE_CODE,
        payload=_payload(
            operation={
                "productionOrder": "1",
                "operationCode": "03",
                "reportedWorkCenter": "CT-63",
            }
        ),
        branch_code="02",
        idempotency_key=str(uuid4()),
    )
    uc = GetRequestProductDrawingUseCase(types, requests, gateway)
    with pytest.raises(ApplicationError) as exc:
        uc.execute(user=PROCESSOR, request_id=without_pa["id"])
    assert exc.value.code == "pa_missing"
    assert gateway.calls == []


def test_drawing_upstream_404_and_503_propagate(harness):
    *_, created, _g, uc = harness
    for code, status in (
        ("drawing_not_found", 404),
        ("drawing_source_unavailable", 503),
    ):
        failing = InMemoryProductDrawingGateway(
            exc=ApplicationError(code=code, status_code=status, detail="x")
        )
        types, requests = harness[0], harness[1]
        uc_fail = GetRequestProductDrawingUseCase(types, requests, failing)
        with pytest.raises(ApplicationError) as exc:
            uc_fail.execute(user=PROCESSOR, request_id=created["id"])
        assert exc.value.code == code
        assert exc.value.status_code == status


# --- rota ---------------------------------------------------------------


class _SpyUseCase:
    def __init__(self, result=None, exc=None):
        self.calls = []
        self._result = result
        self._exc = exc

    def execute(self, *, user, request_id):
        self.calls.append({"user": user, "request_id": request_id})
        if self._exc is not None:
            raise self._exc
        return self._result


def _app(use_case, monkeypatch):
    app = FastAPI()
    app.include_router(requests_routes.router)
    monkeypatch.setattr(
        requests_routes,
        "build_request_product_drawing_use_case",
        lambda: use_case,
    )
    monkeypatch.setattr(
        requests_routes, "_current_user", lambda: PROCESSOR
    )
    return TestClient(app)


def test_route_returns_pdf_inline(harness, monkeypatch):
    *_, created, gateway, uc = harness
    api = _app(uc, monkeypatch)
    resp = api.get(f"/v1/requests/{created['id']}/product-drawing")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert "inline" in resp.headers["content-disposition"]
    assert "90264238.pdf" in resp.headers["content-disposition"]
    assert resp.content.startswith(b"%PDF")
    # nenhum token/URL interno na resposta
    assert "service" not in resp.headers["content-disposition"].lower()


def test_route_maps_domain_errors(monkeypatch):
    for exc, status in (
        (ApplicationError(code="not_found", status_code=404), 404),
        (ApplicationError(code="forbidden", status_code=403), 403),
        (ApplicationError(code="branch_forbidden", status_code=403), 403),
        (
            ApplicationError(code="drawing_not_applicable", status_code=404),
            404,
        ),
        (
            ApplicationError(
                code="drawing_source_unavailable",
                status_code=503,
                detail="Não foi possível consultar o desenho neste momento.",
            ),
            503,
        ),
    ):
        api = _app(_SpyUseCase(exc=exc), monkeypatch)
        resp = api.get(f"/v1/requests/{uuid4()}/product-drawing")
        assert resp.status_code == status
        assert resp.headers["content-type"].startswith("application/json")


def test_route_has_no_code_query_param(harness, monkeypatch):
    """O cliente não escolhe o produto — o PA vem do payload persistido."""
    *_, created, gateway, uc = harness
    api = _app(uc, monkeypatch)
    resp = api.get(
        f"/v1/requests/{created['id']}/product-drawing",
        params={"code": "99999999", "product": "00000001"},
    )
    assert resp.status_code == 200
    assert gateway.calls == ["90264238"]


def test_use_case_receives_request_id_and_user(harness, monkeypatch):
    spy = _SpyUseCase(
        result=SimpleNamespace(
            filename="d.pdf", content=b"%PDF-1.4", media_type="application/pdf"
        )
    )
    api = _app(spy, monkeypatch)
    *_, created = harness[:3]
    resp = api.get(f"/v1/requests/{created['id']}/product-drawing")
    assert resp.status_code == 200
    assert spy.calls[0]["request_id"] == created["id"]
    assert spy.calls[0]["user"].id == "u-proc"
