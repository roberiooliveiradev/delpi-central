from datetime import datetime, timezone

import httpx
import pytest

from delpi_mes_app.domain.errors import (
    MesSourceInvalidResponse, MesSourceNotFound, MesSourceUnauthorized,
    MesSourceUnavailable, MesSourceValidationError,
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
