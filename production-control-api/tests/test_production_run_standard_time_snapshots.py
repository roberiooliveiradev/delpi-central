"""Parte 2.2 — snapshots de Performance congelados no Play do run."""

from __future__ import annotations

import httpx
import pytest

from production_control_app.application.services.production_run_service import (
    ProductionRunService,
)
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.services.production_run_standard_time import (
    normalize_standard_time_snapshot,
    resolve_workstation_type_snapshot,
)
from production_control_app.infrastructure.gateways.delpi_production_gateway import (
    DelpiProductionGateway,
)

from tests.test_production_run_service import (
    FakePulse,
    FakeRepo,
    make_mes,
    make_service,
    service_session,
)


DEVICE = {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}

COMPLETE_PAYLOAD = {
    "branch": "01",
    "production_order": "OP1",
    "operation_code": "10",
    "product_code": "PA123",
    "unit": "MI",
    "pieces_conversion_factor": 1000,
    "standard_time_unit_hours": 0.5,
    "ideal_cycle_seconds": 1.8,
    "setup_seconds": 900,
    "standard_time_source": "shy_tempad",
    "data_quality": "complete",
}


def _make(
    repo: FakeRepo,
    *,
    lookup=None,
    queue: dict | None = None,
) -> ProductionRunService:
    pulse = FakePulse(devices=[DEVICE], device_by_id={"dev-1": DEVICE})
    kwargs: dict = {}
    if lookup is not None:
        kwargs["standard_time_lookup"] = lookup
    if queue is not None:
        kwargs["queue_lookup"] = lambda **_kw: dict(queue)
    return make_service(repo, pulse, **kwargs)


def _start(service: ProductionRunService, repo: FakeRepo) -> dict:
    token = service_session(repo)
    return service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=token,
    )


# ---------------------------------------------------------------------------
# Domínio puro — normalização do payload da api-delpi
# ---------------------------------------------------------------------------


def test_normalize_complete_payload():
    snap = normalize_standard_time_snapshot(COMPLETE_PAYLOAD)
    assert snap == {
        "ideal_cycle_seconds_snapshot": 1.8,
        "setup_seconds_snapshot": 900.0,
        "standard_time_source": "shy_tempad",
        "standard_time_data_quality_snapshot": "complete",
    }


def test_normalize_upstream_unavailable():
    snap = normalize_standard_time_snapshot(None)
    assert snap["ideal_cycle_seconds_snapshot"] is None
    assert snap["setup_seconds_snapshot"] is None
    assert snap["standard_time_source"] == "unavailable"
    assert snap["standard_time_data_quality_snapshot"] == "upstream_unavailable"


def test_normalize_standard_time_unavailable():
    snap = normalize_standard_time_snapshot(
        {"standard_time_source": "unavailable", "data_quality": "standard_time_unavailable"}
    )
    assert snap["ideal_cycle_seconds_snapshot"] is None
    assert snap["standard_time_data_quality_snapshot"] == "standard_time_unavailable"


def test_normalize_piece_conversion_unavailable():
    snap = normalize_standard_time_snapshot(
        {
            "standard_time_unit_hours": 0.5,
            "ideal_cycle_seconds": None,
            "setup_seconds": 120,
            "standard_time_source": "sg2_tempad",
            "data_quality": "piece_conversion_unavailable",
        }
    )
    assert snap["ideal_cycle_seconds_snapshot"] is None
    assert snap["setup_seconds_snapshot"] == 120.0
    assert snap["standard_time_source"] == "sg2_tempad"
    assert snap["standard_time_data_quality_snapshot"] == "piece_conversion_unavailable"


def test_normalize_degrades_contradictory_complete():
    snap = normalize_standard_time_snapshot(
        {
            "ideal_cycle_seconds": 0,
            "setup_seconds": 10,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        }
    )
    assert snap["ideal_cycle_seconds_snapshot"] is None
    assert snap["standard_time_data_quality_snapshot"] == "standard_time_unavailable"


def test_normalize_rejects_negative_setup():
    snap = normalize_standard_time_snapshot(
        {**COMPLETE_PAYLOAD, "setup_seconds": -5}
    )
    assert snap["setup_seconds_snapshot"] is None


def test_workstation_type_manual_only_for_mod_flag():
    assert (
        resolve_workstation_type_snapshot({"is_manual_operation": True})
        == "manual_workstation"
    )
    assert resolve_workstation_type_snapshot({"is_manual_operation": False}) is None
    assert resolve_workstation_type_snapshot({}) is None
    assert resolve_workstation_type_snapshot(None) is None


# ---------------------------------------------------------------------------
# Gateway — contrato HTTP com a api-delpi
# ---------------------------------------------------------------------------


def _gateway_with(handler, monkeypatch: pytest.MonkeyPatch) -> tuple[DelpiProductionGateway, list]:
    requests: list[httpx.Request] = []

    def _record(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    transport = httpx.MockTransport(_record)
    real_client = httpx.Client
    gateway = DelpiProductionGateway(base_url="http://api-delpi", timeout=5)
    monkeypatch.setattr(
        httpx, "Client", lambda **kw: real_client(transport=transport, **kw)
    )
    return gateway, requests


def test_gateway_fetches_standard_time_path_and_branch(monkeypatch):
    gateway, requests = _gateway_with(
        lambda request: httpx.Response(200, json={"success": True, "data": COMPLETE_PAYLOAD}),
        monkeypatch,
    )
    data = gateway.fetch_operation_standard_time(
        branch="01", production_order="OP 9/X", operation_code="10"
    )
    assert data["ideal_cycle_seconds"] == 1.8
    request = requests[0]
    assert request.method == "GET"
    assert request.url.raw_path.startswith(
        b"/production/orders/OP%209%2FX/operations/10/standard-time"
    )
    assert request.url.params["branch"] == "01"


def test_gateway_applies_internal_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-token-1")
    gateway, requests = _gateway_with(
        lambda request: httpx.Response(200, json={"success": True, "data": COMPLETE_PAYLOAD}),
        monkeypatch,
    )
    gateway.fetch_operation_standard_time(
        branch="01", production_order="OP1", operation_code="10"
    )
    headers = requests[0].headers
    assert headers["X-Delpi-Service-Token"] == "svc-token-1"
    assert headers["X-Delpi-Caller-App"] == "production-control-api"
    assert headers["Authorization"] == "Bearer svc-token-1"


def test_gateway_maps_404_to_delpi_error(monkeypatch):
    gateway, _ = _gateway_with(
        lambda request: httpx.Response(404, json={"message": "não encontrada"}),
        monkeypatch,
    )
    with pytest.raises(DelpiGatewayError) as exc:
        gateway.fetch_operation_standard_time(
            branch="01", production_order="OP1", operation_code="99"
        )
    assert exc.value.status_code == 404


def test_gateway_maps_network_error(monkeypatch):
    gateway, _ = _gateway_with(
        lambda request: (_ for _ in ()).throw(httpx.ConnectError("down")),
        monkeypatch,
    )
    with pytest.raises(DelpiGatewayError):
        gateway.fetch_operation_standard_time(
            branch="01", production_order="OP1", operation_code="10"
        )


def test_gateway_rejects_invalid_payload(monkeypatch):
    gateway, _ = _gateway_with(
        lambda request: httpx.Response(200, json={"success": True, "data": "oops"}),
        monkeypatch,
    )
    with pytest.raises(DelpiGatewayError):
        gateway.fetch_operation_standard_time(
            branch="01", production_order="OP1", operation_code="10"
        )


# ---------------------------------------------------------------------------
# Service — congelamento no Play
# ---------------------------------------------------------------------------


def test_start_run_freezes_complete_standard_time():
    repo = FakeRepo()
    service = _make(repo, lookup=lambda **_kw: dict(COMPLETE_PAYLOAD))
    started = _start(service, repo)
    run = repo.runs[started["id"]]
    assert run["ideal_cycle_seconds_snapshot"] == 1.8
    assert run["setup_seconds_snapshot"] == 900.0
    assert run["standard_time_source"] == "shy_tempad"
    assert run["standard_time_data_quality_snapshot"] == "complete"
    assert run["pieces_per_pulse_snapshot"] == 1


def test_start_run_manual_workstation_from_mod():
    repo = FakeRepo()
    service = _make(
        repo,
        lookup=lambda **_kw: dict(COMPLETE_PAYLOAD),
        queue={"operation_pending_qty": 1.0, "is_manual_operation": True},
    )
    started = _start(service, repo)
    assert repo.runs[started["id"]]["workstation_type_snapshot"] == "manual_workstation"


def test_start_run_unknown_workstation_stays_null():
    repo = FakeRepo()
    service = _make(
        repo,
        lookup=lambda **_kw: dict(COMPLETE_PAYLOAD),
        queue={"operation_pending_qty": 1.0, "is_manual_operation": False},
    )
    started = _start(service, repo)
    assert repo.runs[started["id"]]["workstation_type_snapshot"] is None


def test_start_run_succeeds_without_lookup():
    repo = FakeRepo()
    service = _make(repo)
    started = _start(service, repo)
    run = repo.runs[started["id"]]
    assert run["ideal_cycle_seconds_snapshot"] is None
    assert run["standard_time_data_quality_snapshot"] == "upstream_unavailable"
    assert run["pieces_per_pulse_snapshot"] == 1


@pytest.mark.parametrize(
    "payload,expected_quality",
    [
        (
            {"standard_time_source": "unavailable", "data_quality": "standard_time_unavailable"},
            "standard_time_unavailable",
        ),
        (
            {
                "standard_time_source": "shy_tempad",
                "data_quality": "piece_conversion_unavailable",
                "setup_seconds": 30,
            },
            "piece_conversion_unavailable",
        ),
    ],
)
def test_start_run_persists_degraded_quality(payload, expected_quality):
    repo = FakeRepo()
    service = _make(repo, lookup=lambda **_kw: dict(payload))
    started = _start(service, repo)
    run = repo.runs[started["id"]]
    assert run["ideal_cycle_seconds_snapshot"] is None
    assert run["standard_time_data_quality_snapshot"] == expected_quality


def test_start_run_survives_gateway_error():
    repo = FakeRepo()

    def _boom(**_kw):
        raise DelpiGatewayError("timeout", status_code=None)

    service = _make(repo, lookup=_boom)
    started = _start(service, repo)
    run = repo.runs[started["id"]]
    assert run["ideal_cycle_seconds_snapshot"] is None
    assert run["standard_time_data_quality_snapshot"] == "upstream_unavailable"


def test_pulse_still_blocks_play_even_with_standard_time():
    repo = FakeRepo()
    pulse = FakePulse(devices=[])  # nenhum contador no posto
    service = make_service(
        repo,
        pulse,
        standard_time_lookup=lambda **_kw: dict(COMPLETE_PAYLOAD),
    )
    token = service_session(repo)
    from production_control_app.domain.errors import PulseDeviceUnavailable

    with pytest.raises(PulseDeviceUnavailable):
        service.start_run(
            branch="01",
            work_center="CT01",
            production_order="OP1",
            operation_code="10",
            session_token=token,
        )
    assert repo.runs == {}


def test_external_calls_happen_before_transaction():
    calls: list[str] = []

    class SpyRepo(FakeRepo):
        def transaction(self):
            calls.append("tx_open")
            return super().transaction()

        def create_run_with_segment(self, **kwargs):
            calls.append("insert")
            return super().create_run_with_segment(**kwargs)

    repo = SpyRepo()
    pulse = FakePulse(devices=[DEVICE], device_by_id={"dev-1": DEVICE})

    def _pulse_snapshot(**kw):
        calls.append("pulse")
        return FakePulse(devices=[DEVICE]).fetch_work_center_snapshot(**kw)

    pulse.fetch_work_center_snapshot = _pulse_snapshot  # type: ignore[assignment]

    service = make_service(
        repo,
        pulse,
        standard_time_lookup=lambda **_kw: (calls.append("std_time"), dict(COMPLETE_PAYLOAD))[1],
        queue_lookup=lambda **_kw: (calls.append("queue"), {})[1],
    )
    _start(service, repo)
    assert calls.index("pulse") < calls.index("tx_open")
    assert calls.index("queue") < calls.index("tx_open")
    assert calls.index("std_time") < calls.index("tx_open")
    assert calls.index("insert") > calls.index("tx_open")


def test_snapshots_immutable_across_pause_resume_stop():
    repo = FakeRepo()
    calls: list[int] = []

    def _lookup(**_kw):
        calls.append(1)
        return dict(COMPLETE_PAYLOAD)

    mes, _states, downtimes = make_mes()
    service = make_service(
        repo,
        FakePulse(devices=[DEVICE], device_by_id={"dev-1": DEVICE}),
        mes_lifecycle=mes,
        standard_time_lookup=_lookup,
    )
    started = _start(service, repo)
    token = service_session(repo)  # nova sessão válida (a anterior segue válida)
    run_id = started["id"]

    service.pause_run(run_id, session_token=token)
    open_dt = downtimes.get_open(branch="01", work_center="CT01")
    downtimes.classify(
        open_dt["id"],
        reason_code="setup",
        planned=False,
        counts_as_availability_loss=True,
    )
    service.resume_run(run_id, session_token=token)
    service.tick_running_runs()
    service.stop_run(run_id, session_token=token)

    run = repo.runs[run_id]
    assert run["ideal_cycle_seconds_snapshot"] == 1.8
    assert run["standard_time_source"] == "shy_tempad"
    assert calls == [1]  # consultado apenas no Play


def test_mi_target_independent_of_ideal_cycle():
    repo = FakeRepo()
    service = _make(
        repo,
        lookup=lambda **_kw: dict(COMPLETE_PAYLOAD),
        queue={
            "operation_pending_qty": 2.5,
            "pieces_conversion_factor": 1000,
        },
    )
    started = _start(service, repo)
    run = repo.runs[started["id"]]
    assert run["target_pieces_snapshot"] == 2500
    assert run["ideal_cycle_seconds_snapshot"] == 1.8
    assert run["pieces_per_pulse_snapshot"] == 1  # nunca 1000


# ---------------------------------------------------------------------------
# Integração Postgres — migration + persistência real (PC_TEST_MES_DB=1)
# ---------------------------------------------------------------------------

import os

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestPerformanceSnapshotsPostgres:
    @pytest.fixture()
    def repo(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        wc = "ZZ-TEST-SNAP"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_run_segments "
                    f"WHERE run_id IN (SELECT id FROM {PC_SCHEMA_NAME}.production_runs "
                    "WHERE work_center = %s)",
                    (wc,),
                )
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE work_center = %s",
                    (wc,),
                )
            conn.commit()
        yield PostgresProductionRunRepository()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_run_segments "
                    f"WHERE run_id IN (SELECT id FROM {PC_SCHEMA_NAME}.production_runs "
                    "WHERE work_center = %s)",
                    (wc,),
                )
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE work_center = %s",
                    (wc,),
                )
            conn.commit()

    def _create(self, repo, **kwargs):
        base = {
            "branch": "01",
            "work_center": "ZZ-TEST-SNAP",
            "production_order": "OPSNAP",
            "operation_code": "10",
            "device_id": "00000000-0000-4000-8000-0000000000a1",
            "operator_code": "USR01",
            "operator_name": None,
            "bench_session_id": None,
            "planned_qty_snapshot": 1.0,
            "target_pieces_snapshot": 1000,
            "anchor_counter": 0,
            "anchor_epoch": 0,
        }
        base.update(kwargs)
        return repo.create_run_with_segment(**base)

    def test_snapshots_roundtrip(self, repo):
        run = self._create(
            repo,
            ideal_cycle_seconds_snapshot=1.8,
            setup_seconds_snapshot=900.0,
            standard_time_source="shy_tempad",
            standard_time_data_quality_snapshot="complete",
            workstation_type_snapshot="manual_workstation",
            pieces_per_pulse_snapshot=1,
        )
        assert float(run["ideal_cycle_seconds_snapshot"]) == 1.8
        assert float(run["setup_seconds_snapshot"]) == 900.0
        assert run["standard_time_source"] == "shy_tempad"
        assert run["standard_time_data_quality_snapshot"] == "complete"
        assert run["workstation_type_snapshot"] == "manual_workstation"
        assert float(run["pieces_per_pulse_snapshot"]) == 1.0

        fetched = repo.get_run(run["id"])
        assert float(fetched["ideal_cycle_seconds_snapshot"]) == 1.8
        active = repo.get_active_run(branch="01", work_center="ZZ-TEST-SNAP")
        assert active["standard_time_source"] == "shy_tempad"
        with repo.transaction() as conn:
            locked = repo.lock_run(run["id"], conn=conn)
        assert float(locked["pieces_per_pulse_snapshot"]) == 1.0
        listed = repo.list_open_running_runs()
        assert any(
            r["workstation_type_snapshot"] == "manual_workstation" for r in listed
        )

    def test_legacy_run_accepts_null_snapshots(self, repo):
        run = self._create(repo)
        assert run["ideal_cycle_seconds_snapshot"] is None
        assert run["standard_time_source"] is None
        assert run["pieces_per_pulse_snapshot"] is None

    def test_check_constraint_rejects_bad_values(self, repo):
        import psycopg

        with pytest.raises(psycopg.errors.CheckViolation):
            self._create(repo, ideal_cycle_seconds_snapshot=0)
        with pytest.raises(psycopg.errors.CheckViolation):
            self._create(repo, setup_seconds_snapshot=-1)
        with pytest.raises(psycopg.errors.CheckViolation):
            self._create(repo, pieces_per_pulse_snapshot=0)
