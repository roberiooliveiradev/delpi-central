"""Etapa 4 — resumo MES do posto por período de dias civis no cockpit."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_mes_work_center_period_service import (
    PublicMesWorkCenterPeriodService,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DowntimeSourceUnavailable,
    PublicAccessDenied,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

SP = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2026, 10, 19, 13, 0, tzinfo=SP)  # 16:00 UTC — segunda-feira


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _fact(
    *,
    state: str,
    started: datetime,
    ended: datetime | None,
    run_id: str = "run-1",
    op: str = "OP-1",
    operation: str = "10",
    source: str = "operator",
    event_id: str | None = None,
    downtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "stateEventId": event_id or f"se-{state}-{started.timestamp():.0f}-{run_id}",
        "runId": run_id,
        "productionOrder": op,
        "operationCode": operation,
        "state": state,
        "startedAt": _iso(started),
        "endedAt": _iso(ended) if ended else None,
        "source": source,
        "downtime": downtime,
    }


class FakeDowntimeSource:
    def __init__(self, source: str = "mes", reason: str = "bound_counter") -> None:
        self.resolution = {
            "source": source,
            "reason": reason,
            "referenceAt": NOW.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        self.calls = 0

    def resolve(self, **kwargs: Any) -> dict[str, Any]:
        self.calls += 1
        if isinstance(self.resolution, Exception):
            raise self.resolution
        return self.resolution


class FakeIntegrationRead:
    def __init__(self, items: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.items = items or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def get_work_center_timeline(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("db down")
        return {
            "branch": kwargs["branch"],
            "workCenter": kwargs["work_center"],
            "from": kwargs["period_from"].isoformat(),
            "to": kwargs["period_to"].isoformat(),
            "referenceAt": NOW.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "items": self.items,
        }


class FakeRunService:
    def __init__(self, session: dict[str, Any] | None = None) -> None:
        self.session = session or {"branch": "01", "work_center": "CT-01A"}

    def resolve_bench_session(self, raw_token: str | None) -> dict[str, Any]:
        if not raw_token or raw_token == "expired":
            raise BenchSessionRequired("Sessão inválida. Identifique-se novamente.")
        return self.session


class FakeMachineLoad:
    def __init__(self, resources: Any = ("MAQ01",)) -> None:
        self.resources = resources
        self.calls = 0

    def public_snapshot_work_center_resources(self, **kwargs: Any) -> Any:
        self.calls += 1
        return self.resources


def _service(
    *,
    source: FakeDowntimeSource | None = None,
    read: FakeIntegrationRead | None = None,
    run_service: FakeRunService | None = None,
    machine_load: FakeMachineLoad | None = None,
) -> PublicMesWorkCenterPeriodService:
    return PublicMesWorkCenterPeriodService(
        access=PublicCockpitAccessService(),
        machine_load=machine_load or FakeMachineLoad(),
        branch_access=BranchAccessService(),
        downtime_source=source or FakeDowntimeSource(),
        integration_read=read or FakeIntegrationRead(),
        run_service=run_service or FakeRunService(),
        clock=lambda: NOW,
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


def _get(service, **kw) -> dict[str, Any]:
    return service.get_period(
        token=kw.get("token", _token()),
        branch=kw.get("branch", "01"),
        work_center=kw.get("work_center", "CT-01A"),
        session_token=kw.get("session_token", "sess-1"),
        days=kw.get("days", 7),
    )


def _day(data: dict[str, Any], iso_date: str) -> dict[str, Any]:
    return next(d for d in data["days"] if d["date"] == iso_date)


def _reason(data: dict[str, Any], code: str | None) -> dict[str, Any] | None:
    for row in data["reasons"]:
        if row["reasonCode"] == code:
            return row
    return None


# --- Agregação feliz ---------------------------------------------------------

def test_period_aggregates_multiple_days_and_runs() -> None:
    d18 = NOW - timedelta(days=1)
    items = [
        # ontem: 2h produzindo + 30min parada classificada
        _fact(
            state="producing",
            started=d18.replace(hour=8, minute=0, second=0),
            ended=d18.replace(hour=10, minute=0, second=0),
            run_id="run-old",
            op="OP-OLD",
            event_id="se-p1",
        ),
        _fact(
            state="stopped",
            started=d18.replace(hour=10, minute=0, second=0),
            ended=d18.replace(hour=10, minute=30, second=0),
            run_id="run-old",
            source="system",
            event_id="se-s1",
            downtime={
                "id": "dt-1",
                "reasonCode": "setup",
                "reasonLabel": "Setup",
                "confirmed": True,
            },
        ),
        # hoje: 1h produzindo + 1h parada pendente
        _fact(
            state="producing",
            started=NOW.replace(hour=9, minute=0, second=0),
            ended=NOW.replace(hour=10, minute=0, second=0),
            run_id="run-new",
            op="OP-NEW",
            event_id="se-p2",
        ),
        _fact(
            state="stopped",
            started=NOW.replace(hour=10, minute=0, second=0),
            ended=NOW.replace(hour=11, minute=0, second=0),
            run_id="run-new",
            source="system",
            event_id="se-s2",
            downtime={
                "id": "dt-2",
                "reasonCode": None,
                "reasonLabel": None,
                "confirmed": False,
            },
        ),
    ]
    data = _get(_service(read=FakeIntegrationRead(items)), days=7)

    assert data["source"] == "mes"
    assert data["periodDays"] == 7
    assert data["totals"]["producingSeconds"] == 3 * 3600
    assert data["totals"]["stoppedSeconds"] == 5400
    assert data["totals"]["stopCount"] == 2
    assert data["totals"]["pendingReasonCount"] == 1
    # cada dia civil recebe só o seu trecho
    assert _day(data, "2026-10-18")["producingSeconds"] == 7200
    assert _day(data, "2026-10-18")["stoppedSeconds"] == 1800
    assert _day(data, "2026-10-19")["stoppedSeconds"] == 3600
    assert _day(data, "2026-10-19")["pendingReasonCount"] == 1
    # dias sem fatos existem zerados — ausência de registro não vira parada
    assert _day(data, "2026-10-17")["producingSeconds"] == 0
    assert _day(data, "2026-10-17")["stopCount"] == 0
    # ranking de motivos
    setup = _reason(data, "setup")
    assert setup["seconds"] == 1800 and setup["count"] == 1
    pending = _reason(data, None)
    assert pending["label"] == "Motivo pendente"
    assert pending["seconds"] == 3600 and pending["pendingCount"] == 1
    assert data["quality"]["stopOverlapSeconds"] == 0


def test_overnight_stop_split_across_days() -> None:
    # parada 23:00→01:00 atravessa a meia-noite civil de SP
    start = datetime(2026, 10, 18, 23, 0, tzinfo=SP)
    end = datetime(2026, 10, 19, 1, 0, tzinfo=SP)
    read = FakeIntegrationRead(
        [
            _fact(
                state="stopped",
                started=start,
                ended=end,
                source="system",
                event_id="se-ov",
                downtime={
                    "id": "dt-ov",
                    "reasonCode": "maint",
                    "reasonLabel": "Manutenção",
                    "confirmed": True,
                },
            )
        ]
    )
    data = _get(_service(read=read), days=3)
    assert _day(data, "2026-10-18")["stoppedSeconds"] == 3600
    assert _day(data, "2026-10-19")["stoppedSeconds"] == 3600
    # uma parada real, contada uma vez no total e atribuída nos dois dias
    assert data["totals"]["stoppedSeconds"] == 7200
    assert data["totals"]["stopCount"] == 1
    assert _day(data, "2026-10-18")["stopCount"] == 1
    assert _day(data, "2026-10-19")["stopCount"] == 1


def test_open_event_counts_until_reference() -> None:
    started = NOW - timedelta(hours=2)
    read = FakeIntegrationRead(
        [_fact(state="stopped", started=started, ended=None, downtime=None)]
    )
    data = _get(_service(read=read), days=1)
    assert data["totals"]["stoppedSeconds"] == 7200
    unrecorded = _reason(data, None)
    # parada sem downtime válido: aparece como fato, mas não é "pendente"
    assert unrecorded["label"] == "Motivo não registrado"
    assert unrecorded["pendingCount"] == 0
    assert data["totals"]["pendingReasonCount"] == 0


def test_overlapping_stops_never_inflate_totals() -> None:
    start = NOW - timedelta(hours=2)
    mid = NOW - timedelta(hours=1)
    items = [
        _fact(
            state="stopped",
            started=start,
            ended=NOW,
            source="system",
            event_id="se-a",
            downtime={
                "id": "dt-a",
                "reasonCode": "a",
                "reasonLabel": "Motivo A",
                "confirmed": True,
            },
        ),
        _fact(
            state="stopped",
            started=mid,
            ended=NOW,
            source="system",
            event_id="se-b",
            downtime={
                "id": "dt-b",
                "reasonCode": "b",
                "reasonLabel": "Motivo B",
                "confirmed": True,
            },
        ),
    ]
    data = _get(_service(read=FakeIntegrationRead(items)), days=1)
    # união real: 2h; atribuição por motivo soma 3h — a diferença é exposta
    assert data["totals"]["stoppedSeconds"] == 7200
    assert _reason(data, "a")["seconds"] == 7200
    assert _reason(data, "b")["seconds"] == 3600
    assert data["quality"]["stopOverlapSeconds"] == 3600


def test_confirmed_setup_is_not_pending() -> None:
    started = NOW - timedelta(hours=1)
    read = FakeIntegrationRead(
        [
            _fact(
                state="stopped",
                started=started,
                ended=NOW,
                source="system",
                event_id="se-setup",
                downtime={
                    "id": "dt-s",
                    "reasonCode": "setup",
                    "reasonLabel": "Setup",
                    "confirmed": True,
                },
            )
        ]
    )
    data = _get(_service(read=read), days=1)
    assert data["totals"]["pendingReasonCount"] == 0
    assert _reason(data, "setup")["pendingCount"] == 0


def test_event_started_before_window_is_clipped() -> None:
    start = NOW - timedelta(days=40)
    end = NOW - timedelta(days=40) + timedelta(hours=1)
    read = FakeIntegrationRead(
        [_fact(state="producing", started=start, ended=end)]
    )
    data = _get(_service(read=read), days=7)
    # fora da janela → zero; nada inventado
    assert data["totals"]["producingSeconds"] == 0


def test_read_failure_propagates_never_empty_success() -> None:
    service = _service(read=FakeIntegrationRead(fail=True))
    with pytest.raises(RuntimeError):
        _get(service)


# --- Política de fonte / autorização ----------------------------------------

def test_totvs_returns_controlled_response_without_aggregates() -> None:
    source = FakeDowntimeSource("totvs", "no_bound_counter")
    read = FakeIntegrationRead()
    data = _get(_service(source=source, read=read))
    assert data["source"] == "totvs"
    assert "totals" not in data and "series" not in data
    assert read.calls == []  # nunca consulta MES para CT TOTVS


def test_unavailable_source_raises_503_domain_error() -> None:
    source = FakeDowntimeSource("unavailable", "pulse_unreachable")
    with pytest.raises(DowntimeSourceUnavailable):
        _get(_service(source=source))


def test_invalid_token_denied() -> None:
    with pytest.raises(PublicAccessDenied):
        _get(_service(), token="bogus-token")


def test_missing_and_expired_session_denied() -> None:
    with pytest.raises(BenchSessionRequired):
        _get(_service(), session_token=None)
    with pytest.raises(BenchSessionRequired):
        _get(_service(), session_token="expired")


def test_session_from_other_work_center_denied() -> None:
    run_service = FakeRunService({"branch": "01", "work_center": "CT-99"})
    with pytest.raises(BenchSessionRequired):
        _get(_service(run_service=run_service))


def test_days_bounds_enforced() -> None:
    with pytest.raises(ValueError):
        _get(_service(), days=0)
    with pytest.raises(ValueError):
        _get(_service(), days=60)


def test_unpublished_work_center_denied() -> None:
    # CT fora da fila E sem vínculo Pulse → o resolver nega o acesso.
    # (CT sensorizado sem OP publicada é permitido — RQ-11; ver
    #  test_work_center_downtime_source.)
    denied = FakeDowntimeSource()
    denied.resolution = ValueError(
        "Centro de trabalho «CT-01A» não está na fila publicada desta filial."
    )
    with pytest.raises(ValueError):
        _get(_service(source=denied, machine_load=FakeMachineLoad(None)))


def test_sensorized_work_center_without_publication_allowed() -> None:
    """CT sensorizado fora da fila publicada: o resolver responde mes e
    a leitura segue — autorização vem da sessão de bancada (RQ-11)."""
    data = _get(_service(machine_load=FakeMachineLoad(None)))
    assert data["workCenter"] == "CT-01A"


def test_window_covers_last_civil_days_sp() -> None:
    read = FakeIntegrationRead()
    _get(_service(read=read), days=14)
    call = read.calls[0]
    assert call["period_from"].date() == (NOW.date() - timedelta(days=13))
    assert call["period_from"].hour == 0
    assert call["period_to"] == NOW


# --- Contrato HTTP ------------------------------------------------------------

class TestMesPeriodRoute:
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
            "build_public_mes_work_center_period_service",
            lambda *a, **kw: service,
        )
        monkeypatch.setattr(
            routes,
            "build_public_cockpit_access_service",
            lambda *a, **kw: PublicCockpitAccessService(),
        )
        return TestClient(app)

    def _url(self, token: str) -> str:
        return f"/public/machine-load/{token}/mes/work-centers/period"

    def test_contract_mes_shape(self, monkeypatch) -> None:
        started = NOW - timedelta(hours=1)
        service = _service(
            read=FakeIntegrationRead(
                [_fact(state="stopped", started=started, ended=None, downtime=None)]
            )
        )
        api = self._client(service, monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A", "days": 7},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["source"] == "mes"
        assert data["totals"]["stoppedSeconds"] == 3600
        assert len(data["days"]) == 7
        assert data["periodDays"] == 7
        assert isinstance(data["reasons"], list)
        assert data["quality"]["stopOverlapSeconds"] == 0

    def test_missing_session_401(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
        )
        assert resp.status_code == 401

    def test_invalid_token_404(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        resp = api.get(
            self._url("bogus"),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 404

    def test_days_out_of_range_422(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A", "days": 90},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 422

    def test_unavailable_503(self, monkeypatch) -> None:
        service = _service(source=FakeDowntimeSource("unavailable", "pulse_unreachable"))
        api = self._client(service, monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 503

    def test_totvs_controlled_response(self, monkeypatch) -> None:
        service = _service(source=FakeDowntimeSource("totvs", "no_bound_counter"))
        api = self._client(service, monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["source"] == "totvs"
