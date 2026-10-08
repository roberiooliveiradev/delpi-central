"""P2 — Problema de Processo no cockpit público (Production Control → Requests API).

Cobre:
* segurança pública: cockpit token, bench session, honeypot, anti-oracle;
* snapshot: identidade/branch/CT da sessão, OP/operação/produto/PA/ferramenta
  da fila PUBLISHED, materiais SD4 congelados;
* degradação: falha SD4 não bloqueia o reporte;
* gateway S2S: headers, idempotência ponta a ponta, mapeamento de erros;
* indisponibilidade do Requests API → erro, nunca sucesso falso.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.public_process_issue_service import (  # noqa: E501
    PublicProcessIssueService,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    RequestsGatewayRejected,
    RequestsGatewayUnauthorized,
    RequestsGatewayUnavailable,
    SnapshotNotFound,
)
from production_control_app.infrastructure.gateways.requests_api_gateway import (
    RequestsApiGateway,
)
from production_control_app.interface.http.routes import (
    public_machine_load_routes as public_routes,
)
from production_control_app.interface.http.routes import (
    public_process_issue_routes as issue_routes,
)

S2S_TOKEN = "internal-s2s-token"


# --- fakes ----------------------------------------------------------------------


class FakeSessionResolver:
    """Espelha resolve_bench_session (regras da sessão)."""

    def __init__(self, session: dict[str, Any] | None) -> None:
        self.session = session
        self.calls: list[str | None] = []

    def resolve_bench_session(self, raw_token: str | None) -> dict[str, Any]:
        self.calls.append(raw_token)
        if self.session is None or raw_token != "sess-token":
            raise BenchSessionRequired("Sessão inválida. Identifique-se novamente.")
        return self.session


def _session(**overrides: Any) -> dict[str, Any]:
    base = {
        "id": str(uuid.uuid4()),
        "branch": "02",
        "work_center": "CT-63",
        "operator_code": "001234",
        "operator_name": "Maria Silva",
    }
    base.update(overrides)
    return base


class FakeMachineLoad:
    """Só o lookup do contexto estendido da PUBLISHED."""

    def __init__(self, context: dict[str, Any] | None) -> None:
        self.context = context
        self.calls: list[dict[str, Any]] = []

    def public_operation_process_issue_context(self, **kwargs: Any):
        self.calls.append(kwargs)
        return self.context


def _context(**overrides: Any) -> dict[str, Any]:
    base = {
        "production_order": "24640401002",
        "operation_code": "03",
        "operation_description": "MONTAGEM",
        "work_center": "CT-63",
        "work_center_name": "Montagem 03",
        "product_code": "10045678",
        "product_description": "Componente semifinished",
        "unit": "PC",
        "pa_product_code": "90264238",
        "pa_product_description": "Produto acabado X",
        "tool": "F99999",
        "resource": "RES-01",
        "planned_qty": 100.0,
        "pending_qty": 50.0,
        "operation_pending_qty": 50.0,
        "scheduled_date": "2026-10-09",
        "scheduled_start_time": "07:30",
        "scheduled_end_date": "2026-10-09",
        "scheduled_end_time": "17:30",
        "due_date": "2026-10-15",
        "pa_due_date": "2026-10-15",
    }
    base.update(overrides)
    return base


def _sd4_material(code: str, **overrides: Any) -> dict[str, Any]:
    base = {
        "product_code": code,
        "description": "TERMINAL FASTON",
        "unit": "PC",
        "original_qty": 500.0,
        "open_qty": 120.0,
        "consumed_qty": 380.0,
    }
    base.update(overrides)
    return base


class FakeOperationMaterials:
    """Espelha PublicOperationMaterialsService.list_for_feedback (SD4)."""

    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self.items = items if items is not None else [_sd4_material("10081234")]
        self._fail = fail
        self.calls: list[dict[str, Any]] = []

    def list_for_feedback(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        if self._fail:
            raise RuntimeError("SD4 indisponível")
        return [dict(item) for item in self.items]


class FakeRequestsGateway:
    """Espelha RequestsGatewayPort.create_request."""

    def __init__(
        self,
        result: dict[str, Any] | None = None,
        *,
        exc: Exception | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self._result = result or {
            "id": "req-9",
            "request_number": "REQ-2026-000123",
            "type_code": "process-issue",
            "status": "submitted",
            "branch_code": "02",
        }
        self._exc = exc

    def create_request(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return dict(self._result)


def _service(
    *,
    session: dict[str, Any] | None = "default",
    context: dict[str, Any] | None = "default",
    gateway: FakeRequestsGateway | None = None,
    materials: FakeOperationMaterials | None = "default",
) -> tuple[PublicProcessIssueService, dict[str, Any]]:
    resolver = FakeSessionResolver(_session() if session == "default" else session)
    machine = FakeMachineLoad(_context() if context == "default" else context)
    gw = gateway or FakeRequestsGateway()
    mats = (
        FakeOperationMaterials()
        if materials == "default"
        else materials
    )
    svc = PublicProcessIssueService(
        run_service=resolver,
        machine_load=machine,
        requests_gateway=gw,
        operation_materials=mats,
    )
    return svc, {
        "resolver": resolver,
        "machine": machine,
        "gateway": gw,
        "materials": mats,
    }


def _report(svc: PublicProcessIssueService, **overrides: Any) -> dict[str, Any]:
    kwargs = {
        "session_token": "sess-token",
        "production_order": "24640401002",
        "operation_code": "03",
        "issue_code": "tool_not_linked",
        "idempotency_key": "idem-key-1",
        "tool_code": "F12345",
        "note": "Ferramenta utilizada no processo não consta na operação.",
    }
    kwargs.update(overrides)
    return svc.report(**kwargs)


def _sent_payload(parts: dict[str, Any]) -> dict[str, Any]:
    return parts["gateway"].calls[0]["body"]["payload"]


# --- sessão / identidade ----------------------------------------------------------


def test_missing_session_is_rejected() -> None:
    svc, _ = _service(session=None)
    with pytest.raises(BenchSessionRequired):
        _report(svc)


def test_invalid_session_never_touches_published_queue() -> None:
    svc, parts = _service(session=None)
    with pytest.raises(BenchSessionRequired):
        _report(svc)
    assert parts["machine"].calls == []
    assert parts["gateway"].calls == []


def test_identity_branch_and_work_center_come_from_session() -> None:
    svc, parts = _service()
    _report(svc)
    body = parts["gateway"].calls[0]["body"]
    assert body["branch"] == "02"
    assert body["requester"]["externalId"] == "operator:02:001234"
    assert body["requester"]["name"] == "Maria Silva"
    payload = _sent_payload(parts)
    assert payload["operator"] == {"code": "001234", "name": "Maria Silva"}
    assert payload["operation"]["reportedWorkCenter"] == "CT-63"


# --- validação contra a PUBLISHED (anti-oracle) ------------------------------------


def test_operation_absent_from_published_is_rejected() -> None:
    svc, parts = _service(context=None)
    with pytest.raises(SnapshotNotFound):
        _report(svc)
    assert parts["gateway"].calls == []


def test_operation_published_on_another_post_same_response() -> None:
    svc_missing, _ = _service(context=None)
    svc_foreign, _ = _service(context=_context(work_center="CT-99"))
    with pytest.raises(SnapshotNotFound) as exc_missing:
        _report(svc_missing)
    with pytest.raises(SnapshotNotFound) as exc_foreign:
        _report(svc_foreign)
    # mesma mensagem: o link anônimo não distingue inexistente de outro posto
    assert str(exc_missing.value) == str(exc_foreign.value)


# --- snapshot -----------------------------------------------------------------------


def test_operation_snapshot_is_frozen_from_published() -> None:
    svc, parts = _service()
    _report(svc)
    operation = _sent_payload(parts)["operation"]
    assert operation["productionOrder"] == "24640401002"
    assert operation["operationCode"] == "03"
    assert operation["description"] == "MONTAGEM"
    assert operation["workCenterName"] == "Montagem 03"
    assert operation["productCode"] == "10045678"
    assert operation["productDescription"] == "Componente semifinished"
    assert operation["unit"] == "PC"
    # PA preservado para o botão "Abrir desenho" da P4
    assert operation["paProductCode"] == "90264238"
    assert operation["paProductDescription"] == "Produto acabado X"
    assert operation["plannedQty"] == 100.0
    assert operation["pendingQty"] == 50.0
    assert operation["operationPendingQty"] == 50.0
    assert operation["scheduledDate"] == "2026-10-09"
    assert operation["scheduledStartTime"] == "07:30"
    assert operation["dueDate"] == "2026-10-15"


def test_tool_snapshot_is_separate_from_reported_tool_code() -> None:
    svc, parts = _service()
    _report(svc)
    payload = _sent_payload(parts)
    assert payload["operation"]["toolSnapshot"] == "F99999"  # o que estava publicado
    assert payload["issue"]["reportedToolCode"] == "F12345"  # o que o operador viu


def test_reported_at_is_backend_generated_and_tz_aware() -> None:
    from datetime import datetime

    svc, parts = _service()
    _report(svc)
    reported_at = datetime.fromisoformat(_sent_payload(parts)["reportedAt"])
    assert reported_at.tzinfo is not None


def test_materials_snapshot_freezes_sd4_rows() -> None:
    svc, parts = _service()
    _report(svc)
    payload = _sent_payload(parts)
    assert payload["materialsSnapshotAvailable"] is True
    assert payload["materials"] == [
        {
            "productCode": "10081234",
            "description": "TERMINAL FASTON",
            "unit": "PC",
            "originalQty": 500.0,
            "openQty": 120.0,
            "consumedQty": 380.0,
        }
    ]
    assert parts["materials"].calls[0]["production_order"] == "24640401002"


def test_optional_operator_fields_may_be_absent() -> None:
    """toolCode/materialCode/note não podem bloquear o reporte."""
    svc, parts = _service()
    _report(svc, tool_code=None, material_code=None, note=None)
    issue = _sent_payload(parts)["issue"]
    assert issue["reportedToolCode"] is None
    assert issue["reportedMaterialCode"] is None
    assert issue["note"] is None


def test_reported_material_code_is_not_checked_against_sd4() -> None:
    """material_not_linked: o código declarado pode estar FORA da SD4."""
    svc, parts = _service()
    _report(
        svc,
        issue_code="material_not_linked",
        material_code="99999999",  # não existe no snapshot SD4 do fake
        tool_code=None,
    )
    issue = _sent_payload(parts)["issue"]
    assert issue["code"] == "material_not_linked"
    assert issue["reportedMaterialCode"] == "99999999"


# --- degradação ---------------------------------------------------------------------


def test_sd4_failure_does_not_block_the_report() -> None:
    svc, parts = _service(materials=FakeOperationMaterials(fail=True))
    result = _report(svc)
    assert result["requestNumber"] == "REQ-2026-000123"
    payload = _sent_payload(parts)
    assert payload["materialsSnapshotAvailable"] is False
    assert payload["materials"] == []


def test_missing_pa_does_not_block_the_report() -> None:
    svc, parts = _service(
        context=_context(pa_product_code=None, pa_product_description=None)
    )
    _report(svc)
    operation = _sent_payload(parts)["operation"]
    assert operation["paProductCode"] is None


# --- gateway / resultado --------------------------------------------------------------


def test_same_idempotency_key_is_forwarded() -> None:
    svc, parts = _service()
    _report(svc, idempotency_key="key-ponta-a-ponta")
    assert parts["gateway"].calls[0]["idempotency_key"] == "key-ponta-a-ponta"


def test_requests_api_down_raises_never_fakes_success() -> None:
    svc, parts = _service(
        gateway=FakeRequestsGateway(
            exc=RequestsGatewayUnavailable("Serviço de solicitações indisponível.")
        )
    )
    with pytest.raises(RequestsGatewayUnavailable):
        _report(svc)


def test_result_returns_request_number_and_status() -> None:
    svc, _ = _service()
    result = _report(svc)
    assert result["requestId"] == "req-9"
    assert result["requestNumber"] == "REQ-2026-000123"
    assert result["status"] == "submitted"
    assert result["message"] == "Solicitação enviada para Processos."


# --- gateway HTTP (httpx MockTransport) -------------------------------------------------


def _gateway(handler) -> RequestsApiGateway:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    return RequestsApiGateway(
        base_url="http://requests-api:8000", timeout=5.0, client=client
    )


def _s2s_body() -> dict[str, Any]:
    return {
        "sourceApp": "production-control",
        "typeCode": "process-issue",
        "branch": "02",
        "requester": {"externalId": "operator:02:001234", "name": "Maria"},
        "payload": {"issue": {"code": "other"}},
    }


def test_gateway_sends_service_headers_and_idempotency_key(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(201, json={"data": {"id": "r1", "status": "submitted"}})

    gw = _gateway(handler)
    result = gw.create_request(body=_s2s_body(), idempotency_key="idem-1")
    assert result["id"] == "r1"
    assert captured["url"] == "http://requests-api:8000/integrations/requests"
    headers = captured["headers"]
    assert headers["x-delpi-caller-app"] == "production-control-api"
    assert headers["idempotency-key"] == "idem-1"
    assert headers["x-delpi-service-token"] == S2S_TOKEN


def test_gateway_maps_timeout_to_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    gw = _gateway(handler)
    with pytest.raises(RequestsGatewayUnavailable):
        gw.create_request(body=_s2s_body(), idempotency_key="k")


def test_gateway_maps_4xx_to_rejected_with_upstream_message(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422, json={"success": False, "message": "Motivo de problema desconhecido."}
        )

    gw = _gateway(handler)
    with pytest.raises(RequestsGatewayRejected) as exc:
        gw.create_request(body=_s2s_body(), idempotency_key="k")
    assert "Motivo de problema desconhecido" in str(exc.value)


def test_gateway_maps_401_403_to_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)
    gw = _gateway(lambda request: httpx.Response(401, json={"success": False}))
    with pytest.raises(RequestsGatewayUnauthorized):
        gw.create_request(body=_s2s_body(), idempotency_key="k")
    assert issubclass(RequestsGatewayUnauthorized, RequestsGatewayUnavailable)


def test_gateway_maps_5xx_to_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)
    gw = _gateway(lambda request: httpx.Response(503, json={"success": False}))
    with pytest.raises(RequestsGatewayUnavailable):
        gw.create_request(body=_s2s_body(), idempotency_key="k")


def test_gateway_maps_malformed_response_to_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)
    gw = _gateway(lambda request: httpx.Response(200, content=b"not-json"))
    with pytest.raises(RequestsGatewayUnavailable):
        gw.create_request(body=_s2s_body(), idempotency_key="k")


def test_gateway_token_never_appears_in_errors(monkeypatch, caplog) -> None:
    import logging

    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", S2S_TOKEN)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    gw = _gateway(handler)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RequestsGatewayUnavailable) as exc:
            gw.create_request(body=_s2s_body(), idempotency_key="k")
    assert S2S_TOKEN not in str(exc.value)
    assert S2S_TOKEN not in caplog.text


# --- contrato HTTP ------------------------------------------------------------------


class _Access:
    def is_valid_token(self, token: str | None) -> bool:
        return token == "valid-token"


def _app(svc: PublicProcessIssueService) -> TestClient:
    app = FastAPI()
    app.include_router(issue_routes.router)
    issue_routes.build_public_process_issue_service = lambda: svc  # type: ignore[assignment]
    public_routes.build_public_cockpit_access_service = lambda: _Access()  # type: ignore[assignment]
    return TestClient(app)


def _post(api: TestClient, headers: dict[str, str] | None = None, **overrides: Any):
    body = {
        "productionOrder": "24640401002",
        "operationCode": "03",
        "issueCode": "tool_not_linked",
        "toolCode": "F12345",
        "note": "Ferramenta não consta na operação.",
        "website": "",
    }
    body.update(overrides)
    merged = {
        "X-Delpi-Bench-Session": "sess-token",
        "Idempotency-Key": "idem-http-1",
    }
    merged.update(headers or {})
    return api.post(
        "/public/machine-load/valid-token/process-issues", json=body, headers=merged
    )


def test_http_invalid_cockpit_token_returns_404() -> None:
    svc, _ = _service()
    api = _app(svc)
    resp = api.post(
        "/public/machine-load/bad-token/process-issues",
        json={"productionOrder": "1", "operationCode": "03", "issueCode": "other"},
    )
    assert resp.status_code == 404
    assert resp.json()["success"] is False


def test_http_missing_session_returns_401() -> None:
    svc, _ = _service(session=None)
    api = _app(svc)
    assert _post(api).status_code == 401


def test_http_missing_idempotency_key_returns_422() -> None:
    svc, parts = _service()
    api = _app(svc)
    body = {
        "productionOrder": "1",
        "operationCode": "03",
        "issueCode": "other",
    }
    resp = api.post(
        "/public/machine-load/valid-token/process-issues",
        json=body,
        headers={"X-Delpi-Bench-Session": "sess-token"},
    )
    assert resp.status_code == 422
    assert parts["gateway"].calls == []


def test_http_honeypot_accepts_silently() -> None:
    svc, parts = _service()
    api = _app(svc)
    resp = _post(api, website="http://bot.example")
    assert resp.status_code == 200
    assert resp.json()["data"]["accepted"] is True
    assert parts["gateway"].calls == []


def test_http_create_returns_public_dto() -> None:
    svc, _ = _service()
    api = _app(svc)
    resp = _post(api)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["requestNumber"] == "REQ-2026-000123"
    assert data["status"] == "submitted"
    # DTO público nunca carrega sessão, credenciais nem snapshot
    assert "benchSessionId" not in data
    assert "payload" not in data


def test_http_operation_not_in_published_and_other_post_same_404() -> None:
    svc_missing, _ = _service(context=None)
    svc_foreign, _ = _service(context=_context(work_center="CT-99"))
    resp_missing = _post(_app(svc_missing))
    resp_foreign = _post(_app(svc_foreign))
    assert resp_missing.status_code == resp_foreign.status_code == 404
    assert resp_missing.json()["message"] == resp_foreign.json()["message"]
    assert "não está disponível neste posto" in resp_missing.json()["message"]


def test_http_requests_api_down_returns_503_friendly() -> None:
    svc, _ = _service(
        gateway=FakeRequestsGateway(
            exc=RequestsGatewayUnavailable("Serviço de solicitações indisponível.")
        )
    )
    api = _app(svc)
    resp = _post(api)
    assert resp.status_code == 503
    assert "Não foi possível enviar a solicitação para Processos" in resp.json()[
        "message"
    ]


def test_http_upstream_rejection_propagates_safe_message() -> None:
    svc, _ = _service(
        gateway=FakeRequestsGateway(
            exc=RequestsGatewayRejected("Motivo de problema de processo desconhecido.")
        )
    )
    api = _app(svc)
    resp = _post(api)
    assert resp.status_code == 422
    assert "desconhecido" in resp.json()["message"]
