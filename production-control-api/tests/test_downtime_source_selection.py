"""Etapa 1 — seleção da fonte de paradas do cockpit por (filial, CT).

Cobre a matriz de decisão: 1 contador (online/offline/stale) → mes;
sem contador + atividade MES no dia → mes; sem contador + sem atividade
→ totvs; >1 contador / Pulse fora / payload inválido / leitura MES
falhando → unavailable (nunca fallback silencioso para TOTVS).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_work_center_downtime_source_service import (
    PublicWorkCenterDowntimeSourceService,
)
from production_control_app.domain.errors import (
    InvalidBranch,
    PublicAccessDenied,
    PulseGatewayError,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService


def _device(device_id: str, **over: Any) -> dict[str, Any]:
    base = {
        "deviceId": device_id,
        "counter": 100,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    base.update(over)
    return base


class FakePulse:
    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        *,
        raw: Any = "SENTINEL",
        fail: Exception | None = None,
    ) -> None:
        self.items = items if items is not None else []
        self.raw = raw
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def fetch_work_center_snapshot(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail is not None:
            raise self.fail
        if self.raw != "SENTINEL":
            return self.raw
        return {"branch": kwargs["branch"], "workCenter": kwargs["work_center"], "items": self.items}


class FakeMonitoring:
    def __init__(self, activity: bool = False, *, fail: bool = False) -> None:
        self.activity = activity
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def has_activity_in_period(self, **kwargs: Any) -> bool:
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("db down")
        return self.activity


class FakeMachineLoad:
    def __init__(self, resources: list[str] | None = ("MAQ01",)) -> None:
        self.resources = resources
        self.calls: list[dict[str, Any]] = []

    def public_snapshot_work_center_resources(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.resources


def _service(
    *,
    pulse: FakePulse | None = None,
    monitoring: FakeMonitoring | None = None,
    machine_load: FakeMachineLoad | None = None,
) -> PublicWorkCenterDowntimeSourceService:
    return PublicWorkCenterDowntimeSourceService(
        access=PublicCockpitAccessService(),
        machine_load=machine_load or FakeMachineLoad(),
        branch_access=BranchAccessService(),
        pulse_gateway=pulse or FakePulse(),
        mes_monitoring=monitoring or FakeMonitoring(),
        clock=lambda: datetime(2026, 10, 19, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


# --- seleção MES -----------------------------------------------------------


def test_single_online_counter_selects_mes() -> None:
    data = _service(pulse=FakePulse(items=[_device("dev-1")])).resolve(
        token=_token(), branch="02", work_center="CT-02B"
    )
    assert data["source"] == "mes"
    assert data["reason"] == "bound_counter"
    assert data["branch"] == "02" and data["workCenter"] == "CT-02B"
    assert data["referenceAt"].endswith("Z")


def test_offline_counter_still_selects_mes() -> None:
    device = _device("dev-1", online=False, status="offline")
    data = _service(pulse=FakePulse(items=[device])).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "mes" and data["reason"] == "bound_counter"


def test_stale_counter_still_selects_mes() -> None:
    device = _device("dev-1", status="stale")
    data = _service(pulse=FakePulse(items=[device])).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "mes"


# --- TOTVS somente com ausência comprovada ----------------------------------


def test_no_counter_and_no_mes_activity_selects_totvs() -> None:
    monitoring = FakeMonitoring(activity=False)
    data = _service(monitoring=monitoring).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "totvs"
    assert data["reason"] == "no_bound_counter"
    assert monitoring.calls  # existência consultada antes de TOTVS


def test_unbound_with_mes_activity_today_selects_mes() -> None:
    data = _service(monitoring=FakeMonitoring(activity=True)).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "mes"
    assert data["reason"] == "mes_activity_today"


# --- indisponível, sem fallback ---------------------------------------------


def test_multiple_counters_is_unavailable() -> None:
    pulse = FakePulse(items=[_device("dev-1"), _device("dev-2")])
    monitoring = FakeMonitoring(activity=True)
    data = _service(pulse=pulse, monitoring=monitoring).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "unavailable"
    assert data["reason"] == "multiple_bound_counters"
    assert not monitoring.calls  # ambiguidade decide antes da consulta MES


def test_pulse_failure_is_unavailable_not_totvs() -> None:
    pulse = FakePulse(fail=PulseGatewayError("timeout"))
    monitoring = FakeMonitoring(activity=False)
    data = _service(pulse=pulse, monitoring=monitoring).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "unavailable"
    assert data["reason"] == "source_lookup_unavailable"
    assert not monitoring.calls


def test_malformed_pulse_payload_is_unavailable() -> None:
    for raw in ({"unexpected": True}, "not-a-dict", ["items"], None):
        pulse = FakePulse(raw=raw, fail=PulseGatewayError("malformed"))
        data = _service(pulse=pulse).resolve(
            token=_token(), branch="01", work_center="CT-01A"
        )
        assert data["source"] == "unavailable", raw


def test_mes_activity_lookup_failure_is_unavailable() -> None:
    data = _service(monitoring=FakeMonitoring(fail=True)).resolve(
        token=_token(), branch="01", work_center="CT-01A"
    )
    assert data["source"] == "unavailable"
    assert data["reason"] == "source_lookup_unavailable"


# --- escopo e segurança ------------------------------------------------------


def test_invalid_token_denied() -> None:
    with pytest.raises(PublicAccessDenied):
        _service().resolve(token="bogus", branch="01", work_center="CT-01A")


def test_invalid_branch_rejected() -> None:
    with pytest.raises(InvalidBranch):
        _service().resolve(token=_token(), branch="99", work_center="CT-01A")


def test_work_center_not_published_rejected() -> None:
    service = _service(machine_load=FakeMachineLoad(resources=None))
    with pytest.raises(ValueError, match="fila publicada"):
        service.resolve(token=_token(), branch="01", work_center="CT-XX")


def test_empty_work_center_rejected() -> None:
    with pytest.raises(ValueError):
        _service().resolve(token=_token(), branch="01", work_center=" ")


# --- somente leitura ----------------------------------------------------------


def test_repeated_calls_are_read_only() -> None:
    pulse = FakePulse()
    monitoring = FakeMonitoring(activity=False)
    machine_load = FakeMachineLoad()
    service = _service(pulse=pulse, monitoring=monitoring, machine_load=machine_load)
    for _ in range(3):
        service.resolve(token=_token(), branch="01", work_center="CT-01A")
    # Nenhum efeito: apenas leituras idempotentes (snapshot fila, Pulse, EXISTS).
    assert len(machine_load.calls) == 3
    assert len(pulse.calls) == 3
    assert len(monitoring.calls) == 3


# --- política pura ------------------------------------------------------------


def test_domain_resolver_matrix() -> None:
    from production_control_app.domain.services.downtime_source_selection import (
        resolve_downtime_source,
    )

    assert resolve_downtime_source(
        lookup_ok=True, bound_counters=1, mes_activity_today=False
    ) == ("mes", "bound_counter")
    assert resolve_downtime_source(
        lookup_ok=True, bound_counters=0, mes_activity_today=True
    ) == ("mes", "mes_activity_today")
    assert resolve_downtime_source(
        lookup_ok=True, bound_counters=0, mes_activity_today=False
    ) == ("totvs", "no_bound_counter")
    assert resolve_downtime_source(
        lookup_ok=True, bound_counters=2, mes_activity_today=True
    ) == ("unavailable", "multiple_bound_counters")
    assert resolve_downtime_source(
        lookup_ok=False, bound_counters=0, mes_activity_today=False
    ) == ("unavailable", "source_lookup_unavailable")


# --- gateway: payload malformado não vira "sem sensores" --------------------


def _gateway_for(payload_status: int, body: Any):
    import httpx

    from production_control_app.infrastructure.gateways.production_pulse_gateway import (  # noqa: E501
        ProductionPulseGateway,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        import json as _json

        raw = body if isinstance(body, str) else _json.dumps(body)
        return httpx.Response(
            payload_status,
            content=raw.encode(),
            headers={"Content-Type": "application/json"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=5)
    return ProductionPulseGateway(base_url="http://pulse.test", client=client)


def test_gateway_malformed_payload_raises_not_empty_items() -> None:
    """Resposta malformada do Pulse NÃO pode virar items=[] — isso levaria
    o seletor a escolher TOTVS por engano."""
    for body in ('"just-a-string"', "[1,2]", '{"data": "x"}', "not-json"):
        gw = _gateway_for(200, body)
        try:
            with pytest.raises(PulseGatewayError):
                gw.fetch_work_center_snapshot(branch="01", work_center="CT-01A")
        finally:
            gw.close()


def test_gateway_dict_without_items_raises() -> None:
    gw = _gateway_for(200, {"data": {"workCenter": "CT-01A"}})
    try:
        with pytest.raises(PulseGatewayError):
            gw.fetch_work_center_snapshot(branch="01", work_center="CT-01A")
    finally:
        gw.close()


def test_gateway_valid_payload_passes_through() -> None:
    gw = _gateway_for(200, {"data": {"items": [{"deviceId": "d1"}]}})
    try:
        snapshot = gw.fetch_work_center_snapshot(branch="01", work_center="CT-01A")
        assert snapshot["items"] == [{"deviceId": "d1"}]
    finally:
        gw.close()


# --- contrato HTTP -----------------------------------------------------------


class TestDowntimeSourceRoute:
    def _client(self, service, monkeypatch):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from production_control_app.interface.http.routes import (
            public_machine_load_routes as routes,
        )

        app = FastAPI()
        app.include_router(routes.router)
        monkeypatch.setattr(
            routes,
            "build_public_work_center_downtime_source_service",
            lambda *a, **kw: service,
        )
        monkeypatch.setattr(
            routes,
            "build_public_cockpit_access_service",
            lambda *a, **kw: PublicCockpitAccessService(),
        )
        monkeypatch.setattr(
            routes,
            "build_branch_access_service",
            lambda *a, **kw: BranchAccessService(),
        )
        return TestClient(app)

    def test_contract_shape_mes(self, monkeypatch) -> None:
        service = _service(pulse=FakePulse(items=[_device("dev-1")]))
        api = self._client(service, monkeypatch)
        token = _token()
        resp = api.get(
            f"/public/machine-load/{token}/downtime-source",
            params={"branch": "02", "workCenter": "CT-02B"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["source"] == "mes"
        assert data["reason"] == "bound_counter"
        assert data["branch"] == "02"
        assert data["workCenter"] == "CT-02B"
        assert set(data) == {
            "branch",
            "workCenter",
            "source",
            "reason",
            "referenceAt",
        }

    def test_contract_unavailable_is_valid_response(self, monkeypatch) -> None:
        service = _service(pulse=FakePulse(fail=PulseGatewayError("down")))
        api = self._client(service, monkeypatch)
        token = _token()
        resp = api.get(
            f"/public/machine-load/{token}/downtime-source",
            params={"branch": "01", "workCenter": "CT-01A"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["source"] == "unavailable"

    def test_invalid_token_404(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        resp = api.get(
            "/public/machine-load/bogus/downtime-source",
            params={"branch": "01", "workCenter": "CT-01A"},
        )
        assert resp.status_code == 404

    def test_invalid_branch_422(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        token = _token()
        resp = api.get(
            f"/public/machine-load/{token}/downtime-source",
            params={"branch": "99", "workCenter": "CT-01A"},
        )
        assert resp.status_code == 422

    def test_unpublished_work_center_422(self, monkeypatch) -> None:
        service = _service(machine_load=FakeMachineLoad(resources=None))
        api = self._client(service, monkeypatch)
        token = _token()
        resp = api.get(
            f"/public/machine-load/{token}/downtime-source",
            params={"branch": "01", "workCenter": "CT-XX"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Integração Postgres (banco descartável): PC_TEST_MES_DB=1 + PLUGINS_DB_*
# ---------------------------------------------------------------------------

import os

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestMesActivityPostgres:
    def test_has_activity_in_period_real_db(self):
        """EXISTS real: fato do dia retorna True; período sem fato retorna
        False — prova de que a remoção do vínculo preserva a fonte MES no
        mesmo dia civil."""
        from datetime import timedelta, timezone as tz

        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_monitoring_read_repository import (  # noqa: E501
            PostgresMesMonitoringReadRepository,
        )

        wc = "ZZ-TEST-DTSRC"
        now = datetime.now(tz.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.work_center_state_events "
                        "WHERE work_center = %s",
                        (wc,),
                    )
                conn.commit()

        _clean()
        repo = PostgresMesMonitoringReadRepository()
        try:
            assert repo.has_activity_in_period(
                branch="01",
                work_center=wc,
                period_from=day_start,
                period_to=day_start + timedelta(days=1),
            ) is False

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {PC_SCHEMA_NAME}.work_center_state_events "
                        "(branch, work_center, state, source, started_at) "
                        "VALUES ('01', %s, 'producing', 'operator', %s)",
                        (wc, now),
                    )
                conn.commit()

            assert repo.has_activity_in_period(
                branch="01",
                work_center=wc,
                period_from=day_start,
                period_to=day_start + timedelta(days=1),
            ) is True

            yesterday_start = day_start - timedelta(days=1)
            assert repo.has_activity_in_period(
                branch="01",
                work_center=wc,
                period_from=yesterday_start,
                period_to=day_start,
            ) is False  # fato começou hoje, não ontem
        finally:
            _clean()
