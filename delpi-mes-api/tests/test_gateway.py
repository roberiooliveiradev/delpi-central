from datetime import datetime, timezone

import httpx
import pytest

from delpi_mes_app.domain.errors import (
    MesSourceConflict, MesSourceInvalidResponse, MesSourceNotFound,
    MesSourceUnauthorized, MesSourceUnavailable, MesSourceValidationError,
)
from delpi_mes_app.infrastructure.gateways.production_control_mes_gateway import (
    ProductionControlMesGateway,
)


def gateway(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return ProductionControlMesGateway(base_url="http://production-control-api:8000", timeout=5, client=client), client


def test_sends_s2s_headers_and_preserves_query(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    seen = {}
    def handler(request):
        seen["request"] = request
        return httpx.Response(200, json={"success": True, "message": "OK", "data": {"items": []}})
    subject, _ = gateway(handler)
    subject.get_downtimes(
        branch="01", work_center="CT-35",
        period_from=datetime(2026, 9, 29, 10, tzinfo=timezone.utc),
        period_to=datetime(2026, 9, 29, 11, tzinfo=timezone.utc), page=2, page_size=25,
    )
    request = seen["request"]
    assert request.headers["X-Delpi-Service-Token"] == "secret"
    assert request.headers["X-Delpi-Caller-App"] == "delpi-mes-api"
    assert dict(request.url.params)["workCenter"] == "CT-35"
    assert dict(request.url.params)["pageSize"] == "25"


def test_work_center_timeline_targets_consolidated_s2s_route(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    seen = {}
    def handler(request):
        seen["request"] = request
        return httpx.Response(200, json={"success": True, "message": "OK", "data": {"items": []}})
    subject, _ = gateway(handler)
    subject.get_work_center_timeline(
        branch="01", work_center="CT 35",
        period_from=datetime(2026, 9, 29, 3, tzinfo=timezone.utc), period_to=None,
    )
    request = seen["request"]
    assert request.headers["X-Delpi-Service-Token"] == "secret"
    assert request.url.path == "/integrations/mes/work-centers/CT 35/timeline"
    assert b"CT%2035" in request.url.raw_path or request.url.raw_path.endswith(b"/CT%2035/timeline")
    params = dict(request.url.params)
    assert params["branch"] == "01"
    assert params["from"] == "2026-09-29T03:00:00+00:00"
    assert "to" not in params


@pytest.mark.parametrize(
    ("status", "error"),
    [(401, MesSourceUnauthorized), (404, MesSourceNotFound), (422, MesSourceValidationError), (500, MesSourceUnavailable)],
)
def test_maps_upstream_status(status, error):
    subject, _ = gateway(lambda request: httpx.Response(status, json={"message": "safe"}))
    with pytest.raises(error):
        subject.get_monitoring(branch="01")


def test_maps_timeout_and_network_errors():
    for exception in (httpx.ReadTimeout("slow"), httpx.ConnectError("down")):
        subject, _ = gateway(lambda request, exc=exception: (_ for _ in ()).throw(exc))
        with pytest.raises(MesSourceUnavailable):
            subject.get_monitoring(branch="01")


def test_rejects_invalid_json_and_envelope():
    subject, _ = gateway(lambda request: httpx.Response(200, content=b"not-json"))
    with pytest.raises(MesSourceInvalidResponse):
        subject.get_monitoring(branch="01")
    subject, _ = gateway(lambda request: httpx.Response(200, json={"success": True, "data": []}))
    with pytest.raises(MesSourceInvalidResponse):
        subject.get_monitoring(branch="01")


# ---------------------------------------------------------------------------
# Administração do catálogo de motivos (S2S write)
# ---------------------------------------------------------------------------

import json as _json  # noqa: E402

_ADMIN_CASES = [
    ("list_downtime_reasons", {}, "GET", "/integrations/mes/downtime-reasons", None),
    (
        "create_downtime_reason",
        {"payload": {"code": "x", "label": "l", "category": "c",
                     "requiresNote": False, "sortOrder": 1}},
        "POST", "/integrations/mes/downtime-reasons",
        {"code": "x", "label": "l", "category": "c",
         "requiresNote": False, "sortOrder": 1},
    ),
    (
        "update_downtime_reason",
        {"code": "raw material", "payload": {"label": "l"}},
        "PUT", "/integrations/mes/downtime-reasons/raw material",
        {"label": "l"},
    ),
    (
        "set_downtime_reason_active",
        {"code": "raw_material", "active": False},
        "PATCH", "/integrations/mes/downtime-reasons/raw_material/active",
        {"active": False},
    ),
]


@pytest.mark.parametrize(
    ("method_name", "kwargs", "http_method", "path", "expected_json"),
    _ADMIN_CASES,
    ids=[case[0] for case in _ADMIN_CASES],
)
def test_admin_methods_hit_correct_endpoint_with_s2s_headers(
    monkeypatch, method_name, kwargs, http_method, path, expected_json
):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    seen = {}

    def handler(request):
        seen["request"] = request
        return httpx.Response(
            200, json={"success": True, "message": "OK", "data": {"items": []}}
        )

    subject, _ = gateway(handler)
    getattr(subject, method_name)(**kwargs)
    request = seen["request"]
    assert request.method == http_method
    assert request.url.path == path
    assert request.headers["X-Delpi-Service-Token"] == "secret"
    assert request.headers["X-Delpi-Caller-App"] == "delpi-mes-api"
    if expected_json is None:
        assert not request.content
    else:
        assert _json.loads(request.content) == expected_json


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, MesSourceUnauthorized),
        (403, MesSourceUnauthorized),
        (404, MesSourceNotFound),
        (409, MesSourceConflict),
        (422, MesSourceValidationError),
        (500, MesSourceUnavailable),
    ],
)
def test_admin_write_maps_upstream_status(status, error):
    subject, _ = gateway(
        lambda request: httpx.Response(
            status, json={"message": "motivo protegido"}
        )
    )
    with pytest.raises(error) as excinfo:
        subject.set_downtime_reason_active("setup", active=False)
    if error is MesSourceConflict:
        assert "protegido" in str(excinfo.value)


@pytest.mark.parametrize(
    "call",
    [
        lambda subject: subject.list_downtime_reasons(),
        lambda subject: subject.create_downtime_reason({"code": "x"}),
    ],
)
def test_admin_read_and_write_map_network_and_bad_body(call):
    for exception in (httpx.ReadTimeout("slow"), httpx.ConnectError("down")):
        subject, _ = gateway(
            lambda request, exc=exception: (_ for _ in ()).throw(exc)
        )
        with pytest.raises(MesSourceUnavailable):
            call(subject)
    subject, _ = gateway(lambda request: httpx.Response(200, content=b"bad"))
    with pytest.raises(MesSourceInvalidResponse):
        call(subject)
    subject, _ = gateway(
        lambda request: httpx.Response(
            200, json={"success": True, "data": []}
        )
    )
    with pytest.raises(MesSourceInvalidResponse):
        call(subject)


def test_owned_client_is_reused_and_closed(monkeypatch):
    created = []
    class FakeClient:
        def __init__(self, **kwargs):
            self.closed = False
            created.append(self)
        def close(self):
            self.closed = True
    monkeypatch.setattr(httpx, "Client", FakeClient)
    subject = ProductionControlMesGateway(base_url="http://owner", timeout=5)
    assert len(created) == 1
    subject.close()
    assert created[0].closed is True


def test_run_performance_targets_s2s_route(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    seen = {}
    def handler(request):
        seen["request"] = request
        return httpx.Response(200, json={"success": True, "message": "OK", "data": {"performance": {}}})
    subject, _ = gateway(handler)
    subject.get_run_performance("run abc")
    request = seen["request"]
    assert request.headers["X-Delpi-Service-Token"] == "secret"
    assert request.url.path == "/integrations/mes/runs/run%20abc/performance" or request.url.raw_path.endswith(b"/run%20abc/performance")


def test_run_performance_404_maps_to_not_found(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    def handler(request):
        return httpx.Response(404, json={"success": False, "message": "Produção não encontrada."})
    subject, _ = gateway(handler)
    with pytest.raises(MesSourceNotFound):
        subject.get_run_performance("missing")


def test_run_performance_upstream_down_maps_to_unavailable(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    def handler(request):
        return httpx.Response(503, json={"success": False, "message": "down"})
    subject, _ = gateway(handler)
    with pytest.raises(MesSourceUnavailable):
        subject.get_run_performance("run-1")
