from __future__ import annotations

import copy
import uuid

from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_machine_load_drawing_service import (
    PublicMachineLoadDrawingService,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    DrawingNotFound,
    InvalidBranch,
    MachineLoadSequenceConflict,
    SnapshotNotFound,
)
from production_control_app.domain.product_drawing_pdf import DrawingFile
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PluginsDatabaseConnectionError,
)
_WORK_CENTERS = [
    {
        "work_center": "CT-01A",
        "work_center_name": "CORTE E DECAPE",
        "operation_count": 6,
        "in_production_count": 1,
    },
    {
        "work_center": "CT-02",
        "work_center_name": "APLICAÇÃO DE TERMINAIS",
        "operation_count": 19,
        "in_production_count": 0,
    },
]

_OPERATION = {
    "work_center": "CT-02",
    "scheduled_date": "2026-08-20",
    "scheduled_start_time": "05:00",
    "production_order": "24640401002",
    "operation_code": "03",
    "operation_description": "CORTAR E APLICAR 10080059 E 10080568",
    "tool": "23-B31",
    "product_code": "50320064",
    "product_description": "CF1,5BRAN-00148/06/05-5900-6800",
    "planned_qty": 7.1,
    "pending_qty": 7.1,
    "pa_due_date": "2026-08-21",
    "production_status": "not_started",
    "is_in_production": False,
    "production_started_date": None,
    "production_started_time": None,
    "active_operator_code": None,
    "active_operator_name": None,
    "active_operator_count": 0,
    "appointment_count": 0,
}


class FakeGateway:
    def __init__(self, work_centers: list[dict[str, Any]] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.work_centers = _WORK_CENTERS if work_centers is None else work_centers
        self.status_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        self.balances_by_key: dict[tuple[str, str], dict[str, Any]] = {}

    def fetch_machine_load_work_centers(
        self,
        *,
        branch: str,
        delivery_start: str | None,
        delivery_end: str,
        include_in_production_outside_period: bool | None = None,
        include_operations_outside_period: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "work_centers",
                {
                    "branch": branch,
                    "delivery_start": delivery_start,
                    "delivery_end": delivery_end,
                    "include_in_production_outside_period": (
                        include_in_production_outside_period
                    ),
                    "include_operations_outside_period": (
                        include_operations_outside_period
                    ),
                },
            )
        )
        return {
            "success": True,
            "data": {
                "items": self.work_centers,
                "summary": {
                    "work_center_count": len(self.work_centers),
                    "operation_count": sum(
                        int(item.get("operation_count") or 0) for item in self.work_centers
                    ),
                    "order_count": 21,
                    "in_production_count": sum(
                        int(item.get("in_production_count") or 0) for item in self.work_centers
                    ),
                },
            },
        }

    def fetch_machine_load_operations(
        self,
        *,
        branch: str,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
        production_order: str | None = None,
        work_center: str | None = None,
        include_in_production_outside_period: bool | None = None,
        include_operations_outside_period: Sequence[str] | None = None,
        sort: str = "schedule_asc",
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "operations",
                {
                    "branch": branch,
                    "delivery_start": delivery_start,
                    "delivery_end": delivery_end,
                    "scheduled_start": scheduled_start,
                    "scheduled_end": scheduled_end,
                    "production_order": production_order,
                    "work_center": work_center,
                    "include_in_production_outside_period": (
                        include_in_production_outside_period
                    ),
                    "include_operations_outside_period": (
                        include_operations_outside_period
                    ),
                    "sort": sort,
                    "page": page,
                    "page_size": page_size,
                },
            )
        )
        items = []
        for center in self.work_centers:
            items.append({**_OPERATION, "work_center": center["work_center"]})
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": len(items),
                    "is_complete": True,
                },
            },
        }

    def fetch_machine_load_appointment_status(
        self,
        *,
        branch: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        self.calls.append(("appointment_status", {"branch": branch, "count": len(items)}))
        result = []
        for item in items:
            key = (item["production_order"], item["operation_code"])
            hit = self.status_by_key.get(key)
            if hit:
                result.append({**item, **hit, "branch": branch})
            else:
                result.append(
                    {
                        **item,
                        "branch": branch,
                        "production_status": "not_started",
                        "is_in_production": False,
                        "active_operator_count": 0,
                        "appointment_count": 0,
                    }
                )
        return {"success": True, "data": {"items": result, "summary": {}}}

    def fetch_machine_load_operation_balances(
        self,
        *,
        branch: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        self.calls.append(("operation_balances", {"branch": branch, "count": len(items)}))
        result = []
        for item in items:
            key = (item["production_order"], item["operation_code"])
            hit = self.balances_by_key.get(key)
            if hit is not None:
                result.append({**item, **hit, "branch": branch})
        return {"success": True, "data": {"items": result, "summary": {}}}


class FakeSnapshotRepo:
    """Uma fila viva por filial (WORKING) — igual ao Postgres depois da V003/V015."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        # PUBLISHED: cópia congelada do WORKING no instante da «publicação».
        # Nada escreve aqui a não ser publish() — refresh nunca toca a fila das bancadas.
        self.published: dict[str, dict[str, Any]] = {}
        self.upserts = 0
        self.payload_updates = 0
        self.for_update_reads = 0

    def get(self, *, branch: str) -> dict[str, Any] | None:
        return self.rows.get(branch)

    def get_for_update(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        """Emula SELECT ... FOR UPDATE: leitura autoritativa sob lock da linha."""
        self.for_update_reads += 1
        row = self.rows.get(branch)
        return copy.deepcopy(row) if row is not None else None

    @contextmanager
    def transaction(self):
        """Rollback emulado: exceção dentro do bloco restaura WORKING e PUBLISHED."""
        rows_backup = copy.deepcopy(self.rows)
        published_backup = copy.deepcopy(self.published)
        try:
            yield self
        except Exception:
            # restore in-place: FakePublicationRepo segura a referência de published.
            self.rows.clear()
            self.rows.update(rows_backup)
            self.published.clear()
            self.published.update(published_backup)
            raise

    def publish(self, branch: str = "01") -> None:
        """Emula «Enviar para máquinas»: copia o WORKING vigente para o PUBLISHED."""
        row = self.rows.get(branch)
        if row is None:
            raise AssertionError(f"Sem WORKING para publicar na filial {branch}")
        self.published[branch] = {
            **copy.deepcopy(row),
            "source_refreshed_at": row.get("refreshed_at"),
            "source_refreshed_by": row.get("refreshed_by"),
            "published_at": datetime(2026, 8, 19, 22, 30, tzinfo=timezone.utc),
            "published_by": row.get("refreshed_by"),
        }

    def upsert(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
        generation_id: str = "gen-test",
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        self.upserts += 1
        row = {
            "id": "snap-1",
            "branch": branch,
            "start_date": start_date,
            "end_date": end_date,
            "generation_id": generation_id,
            "payload_json": payload,
            "schema_version": schema_version,
            "source": source,
            "refreshed_at": datetime(2026, 8, 19, 22, 0, tzinfo=timezone.utc),
            "refreshed_by": refreshed_by,
        }
        row["row_version"] = row["row_version"] if "row_version" in row else str(uuid.uuid4())
        self.rows[branch] = row
        return row

    def update_payload(
        self, *, branch: str, payload: dict[str, Any], conn: Any = None
    ) -> dict[str, Any]:
        existing = self.rows.get(branch)
        if existing is None:
            raise RuntimeError("Snapshot da carga máquina não encontrado para atualizar.")
        self.payload_updates += 1
        updated = {
            **existing,
            "payload_json": payload,
            "row_version": str(uuid.uuid4()),
        }
        self.rows[branch] = updated
        return updated


class FakePublicationRepo:
    """Uma publicação vigente por filial — igual ao Postgres depois da V015."""

    def __init__(self, rows: dict[str, dict[str, Any]] | None = None) -> None:
        self.rows: dict[str, dict[str, Any]] = rows if rows is not None else {}
        self.upserts = 0

    def get(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        row = self.rows.get(branch)
        return copy.deepcopy(row) if row is not None else None

    def upsert(self, conn: Any = None, **kwargs: Any) -> dict[str, Any]:
        self.upserts += 1
        branch = kwargs["branch"]
        row = {
            "id": f"pub-{branch}",
            "branch": branch,
            "generation_id": kwargs["generation_id"],
            "start_date": kwargs["start_date"],
            "end_date": kwargs["end_date"],
            "payload_json": copy.deepcopy(kwargs["payload"]),
            "schema_version": kwargs.get("schema_version", 1),
            "source": kwargs.get("source", "api-delpi"),
            "source_refreshed_at": kwargs.get("source_refreshed_at"),
            "source_refreshed_by": kwargs.get("source_refreshed_by"),
            "published_at": datetime(2026, 8, 19, 22, 30, tzinfo=timezone.utc),
            "published_by": kwargs.get("published_by"),
        }
        self.rows[branch] = row
        return copy.deepcopy(row)

    def update_payload(
        self, *, branch: str, payload: dict[str, Any], conn: Any = None
    ) -> dict[str, Any]:
        row = self.rows.get(branch)
        if row is None:
            raise AssertionError(f"Sem publicação na filial {branch} para atualizar.")
        row["payload_json"] = copy.deepcopy(payload)
        return copy.deepcopy(row)


def _user(*permissions: str):
    return SimpleNamespace(is_superadmin=False, permissions=list(permissions), id="user-1")


FULL_PERMS = (
    "production-control.access",
    "production-control.machine-load.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _service(
    gateway: FakeGateway,
    snapshots: FakeSnapshotRepo | None = None,
    *,
    open_runs: list[dict[str, Any]] | None = None,
) -> MachineLoadService:
    snapshots = snapshots or FakeSnapshotRepo()
    run_items = list(open_runs) if open_runs is not None else []
    return MachineLoadService(
        gateway,
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: list(run_items),
    )


@pytest.fixture(autouse=True)
def _isolate_live_status_cache():
    """O cache de status é do processo: cada teste começa e termina frio."""
    from production_control_app.application.services.machine_load_live_status_cache import (
        clear_live_status_cache,
    )

    clear_live_status_cache()
    yield
    clear_live_status_cache()


def test_delivery_window_defaults_to_open_start_and_fourteen_days_ahead() -> None:
    """O PCP precisa ver o atrasado; o horizonte é a entrega de hoje + 14 dias."""
    start, end = _service(FakeGateway()).resolve_delivery_window(
        start_date=None, end_date=None, today=date(2026, 8, 19)
    )
    assert start is None
    assert end.isoformat() == "2026-09-02"


def test_first_visit_seeds_snapshot_from_totvs() -> None:
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    payload = _service(gateway, snapshots).build(_user(*FULL_PERMS), branch="01")

    assert snapshots.upserts == 1
    assert payload["snapshot"]["seeded"] is True
    assert payload["snapshot"]["refreshed_at"]
    assert {name for name, _ in gateway.calls} >= {"work_centers", "operations"}
    assert payload["selected"]["work_center"] == "CT-01A"


def test_second_visit_reads_snapshot_without_operations_pull() -> None:
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    gateway.calls.clear()

    payload = service.build(_user(*FULL_PERMS), branch="01")
    assert snapshots.upserts == 1
    assert payload["snapshot"]["seeded"] is False
    assert "operations" not in {name for name, _ in gateway.calls}
    assert "work_centers" not in {name for name, _ in gateway.calls}
    # Status HZA fica em cache curto — troca/releitura de CT não reconsulta api-delpi.
    assert "appointment_status" not in {name for name, _ in gateway.calls}


def test_queue_read_never_waits_for_the_shop_floor() -> None:
    """A fila congelada aparece sem consultar o TOTVS: quem faz isso é `live_status`."""
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01", work_center="CT-01A")
    assert "appointment_status" not in {name for name, _ in gateway.calls}
    gateway.calls.clear()

    payload = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    assert payload["selected"]["work_center"] == "CT-02"
    assert "appointment_status" not in {name for name, _ in gateway.calls}


def test_live_status_reuses_cache_across_readers() -> None:
    """Vários leitores no mesmo TTL não multiplicam consulta ao chão de fábrica."""
    gateway = FakeGateway()
    service = _service(gateway, FakeSnapshotRepo())
    service.build(_user(*FULL_PERMS), branch="01")
    gateway.calls.clear()

    service.live_status(_user(*FULL_PERMS), branch="01")
    assert sum(1 for name, _ in gateway.calls if name == "appointment_status") == 1
    service.live_status(_user(*FULL_PERMS), branch="01")
    assert sum(1 for name, _ in gateway.calls if name == "appointment_status") == 1


def test_refresh_invalidates_live_status_cache() -> None:
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    gateway.calls.clear()
    service.refresh(_user(*FULL_PERMS), branch="01", work_center="CT-01A")
    assert sum(1 for name, _ in gateway.calls if name == "appointment_status") == 1


def test_refresh_upserts_again_and_replaces_queue() -> None:
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    assert snapshots.upserts == 1

    payload = service.refresh(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    assert snapshots.upserts == 2
    assert payload["selected"]["work_center"] == "CT-02"
    assert payload["snapshot"]["seeded"] is False


def test_live_status_overrides_frozen_status_fields() -> None:
    gateway = FakeGateway()
    gateway.status_by_key[("24640401002", "03")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_name": "SILVANA ANDRADE DOS SANTOS",
        "production_started_time": "05:12:44",
        "active_operator_count": 1,
        "appointment_count": 3,
    }
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")

    live = service.live_status(_user(*FULL_PERMS), branch="01")
    running = next(item for item in live["items"] if item["is_in_production"])
    assert running["production_order"] == "24640401002"
    assert running["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"
    # A fila do fake repete a mesma chave nos dois centros.
    assert live["summary"]["in_production_count"] == 2
    assert live["as_of"]

    # Com o status já em cache, a fila sai da API com o override aplicado.
    payload = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    operation = payload["selected"]["items"][0]
    assert operation["is_in_production"] is True
    assert operation["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"
    assert payload["summary"]["in_production_count"] >= 1
    assert payload["work_centers"][1]["in_production_count"] == 1


def test_zero_pending_coerces_live_in_progress_to_started() -> None:
    """Saldo zerado no snapshot manda sobre HZA aberta no enrich vivo."""
    gateway = FakeGateway()
    gateway.status_by_key[("24640401002", "03")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_name": "SILVANA ANDRADE DOS SANTOS",
        "production_started_time": "05:12:44",
        "active_operator_count": 1,
        "appointment_count": 3,
    }
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")

    # Congela saldo 0 no snapshot já persistido e reaplica o enrich.
    for item in snapshots.rows["01"]["payload_json"]["operations"]:
        if item["production_order"] == "24640401002":
            item["pending_qty"] = 0.0
            item["produced_qty"] = item["planned_qty"]

    # `build` não toca o TOTVS: quem consulta a HZA e alimenta o cache é `live_status`.
    service.live_status(_user(*FULL_PERMS), branch="01")
    payload = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    operation = payload["selected"]["items"][0]
    assert operation["pending_qty"] == 0.0
    assert operation["is_in_production"] is False
    assert operation["production_status"] == "started"
    assert operation["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"


def test_public_build_applies_live_operation_balance_on_legacy_snapshot() -> None:
    """Snapshot antigo sem saldo da bancada: o enrich vivo preenche o card público."""
    gateway = FakeGateway()
    gateway.status_by_key[("10916601005", "01")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_name": "OPERADOR TESTE",
        "production_started_time": "14:00:00",
        "active_operator_count": 1,
        "appointment_count": 2,
        "operation_produced_qty": 3.5,
        "operation_pending_qty": 2.5,
    }
    snapshots = FakeSnapshotRepo()
    snapshots.upsert(
        branch="02",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload={
            "work_centers": [
                {
                    "work_center": "CT-01A",
                    "work_center_name": "CORTE E DECAPE",
                    "operation_count": 1,
                    "in_production_count": 1,
                }
            ],
            "operations": [
                {
                    "work_center": "CT-01A",
                    "production_order": "10916601005",
                    "operation_code": "01",
                    "planned_qty": 6.0,
                    "produced_qty": 0.0,
                    "pending_qty": 6.0,
                    "unit": "MI",
                    "is_in_production": True,
                    "production_status": "in_progress",
                }
            ],
            "summary": {"work_center_count": 1, "operation_count": 1},
        },
        refreshed_by="planner-1",
    )
    snapshots.publish("02")

    payload = _service(gateway, snapshots).build_public(
        branch="02", work_center="CT-01A"
    )
    operation = payload["selected"]["items"][0]
    assert operation["pending_qty"] == 6.0
    assert operation["operation_produced_qty"] == 3.5
    assert operation["operation_pending_qty"] == 2.5
    assert ("appointment_status", {"branch": "02", "count": 1}) in gateway.calls


def test_operation_balance_coerces_live_in_progress_even_with_header_pending() -> None:
    """Saldo da bancada zerado manda sobre o cabeçalho da OP e a HZA aberta."""
    gateway = FakeGateway()
    gateway.status_by_key[("24640401002", "03")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_name": "SILVANA ANDRADE DOS SANTOS",
        "production_started_time": "05:12:44",
        "active_operator_count": 1,
        "appointment_count": 4,
        "operation_produced_qty": 7.1,
        "operation_pending_qty": 0.0,
    }
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")

    for item in snapshots.rows["01"]["payload_json"]["operations"]:
        if item["production_order"] == "24640401002":
            item["pending_qty"] = 6.3
            item["planned_qty"] = 7.1

    service.live_status(_user(*FULL_PERMS), branch="01")
    payload = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    operation = payload["selected"]["items"][0]
    assert operation["pending_qty"] == 6.3
    assert operation["operation_pending_qty"] == 0.0
    assert operation["operation_produced_qty"] == 7.1
    assert operation["is_in_production"] is False
    assert operation["production_status"] == "started"


def test_live_status_exposes_only_status_fields() -> None:
    """A rota leve não vaza identidade do snapshot nem campos da fila."""
    gateway = FakeGateway()
    gateway.status_by_key[("24640401002", "03")] = {
        "production_status": "started",
        "is_in_production": False,
        "appointment_count": 2,
        "last_appointment_date": "2026-08-20",
    }
    service = _service(gateway, FakeSnapshotRepo())
    service.build(_user(*FULL_PERMS), branch="01")

    live = service.live_status(_user(*FULL_PERMS), branch="01")
    allowed = {
        "production_order",
        "operation_code",
        "production_status",
        "is_in_production",
        "production_started_date",
        "production_started_time",
        "active_operator_code",
        "active_operator_name",
        "active_operator_count",
        "appointment_count",
        "last_appointment_date",
        "operation_produced_qty",
        "operation_pending_qty",
    }
    assert live["items"]
    for item in live["items"]:
        assert set(item) <= allowed
    assert live["summary"]["operation_count"] == 2


def test_live_status_without_snapshot_is_not_found() -> None:
    service = _service(FakeGateway(), FakeSnapshotRepo())
    with pytest.raises(SnapshotNotFound):
        service.live_status(_user(*FULL_PERMS), branch="01")


def test_machine_load_honors_requested_work_center() -> None:
    gateway = FakeGateway()
    payload = _service(gateway).build(
        _user(*FULL_PERMS), branch="01", work_center="CT-02"
    )
    assert payload["selected"]["work_center"] == "CT-02"


def test_unknown_work_center_falls_back_to_the_first_tab() -> None:
    gateway = FakeGateway()
    payload = _service(gateway).build(
        _user(*FULL_PERMS), branch="01", work_center="CT-ZZZ"
    )
    assert payload["selected"]["work_center"] == "CT-01A"
    assert payload["selected"]["requested_work_center"] == "CT-ZZZ"


def test_no_work_center_skips_operations_selection() -> None:
    gateway = FakeGateway(work_centers=[])
    payload = _service(gateway).build(_user(*FULL_PERMS), branch="01")
    assert payload["selected"]["work_center"] is None
    assert payload["selected"]["items"] == []


def test_first_pull_uses_the_delivery_window_with_an_open_start() -> None:
    gateway = FakeGateway()
    _service(gateway).build(_user(*FULL_PERMS), branch="01")
    call = next(params for name, params in gateway.calls if name == "work_centers")
    assert call["delivery_start"] is None
    assert call["delivery_end"]


def test_explicit_period_is_forwarded_to_the_gateway_on_refresh() -> None:
    gateway = FakeGateway()
    _service(gateway).refresh(
        _user(*FULL_PERMS),
        branch="01",
        start_date="2026-08-24",
        end_date="2026-08-28",
    )
    call = next(params for name, params in gateway.calls if name == "work_centers")
    assert call["delivery_start"] == "2026-08-24"
    assert call["delivery_end"] == "2026-08-28"


def test_refresh_disables_hza_period_escape_and_sends_open_runs() -> None:
    """Escape de período passa a ser sustentado pelos runs do cockpit, não HZA."""
    gateway = FakeGateway()
    service = _service(
        gateway,
        open_runs=[
            _run_item(
                production_order="24640401002",
                operation_code="03",
                work_center="CT-01A",
            )
        ],
    )

    service.refresh(_user(*FULL_PERMS), branch="01")

    for name in ("work_centers", "operations"):
        call = next(params for n, params in gateway.calls if n == name)
        assert call["include_in_production_outside_period"] is False
        assert call["include_operations_outside_period"] == [
            "24640401002:03"
        ]


def test_refresh_without_open_runs_sends_no_period_exception() -> None:
    """Sem run aberto, nenhuma operação fora do período é requisitada."""
    gateway = FakeGateway()
    _service(gateway).refresh(_user(*FULL_PERMS), branch="01")

    for name in ("work_centers", "operations"):
        call = next(params for n, params in gateway.calls if n == name)
        assert call["include_in_production_outside_period"] is False
        assert call["include_operations_outside_period"] == []


def test_refresh_fails_closed_when_cockpit_source_is_down() -> None:
    """Fonte oficial indisponível: o refresh não monta fila assumindo zero runs."""
    snapshots = FakeSnapshotRepo()
    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: (_ for _ in ()).throw(
            PluginsDatabaseConnectionError("db down")
        ),
    )

    with pytest.raises(PluginsDatabaseConnectionError):
        service.refresh(_user(*FULL_PERMS), branch="01")

    assert snapshots.rows == {}


def test_inverted_period_is_rejected() -> None:
    with pytest.raises(ValueError):
        _service(FakeGateway()).refresh(
            _user(*FULL_PERMS),
            branch="01",
            start_date="2026-08-28",
            end_date="2026-08-24",
        )


def _seed_delivery_snapshot(snapshots: FakeSnapshotRepo) -> None:
    """Fila congelada com entregas em datas diferentes nos dois centros."""
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 18),
        end_date=date(2026, 9, 2),
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [
                {
                    **_OPERATION,
                    "work_center": "CT-01A",
                    "production_order": "A1",
                    "due_date": "2026-08-18",
                },
                {
                    **_OPERATION,
                    "work_center": "CT-02",
                    "production_order": "B1",
                    "due_date": "2026-08-30",
                },
            ],
            "summary": {"work_center_count": 2, "operation_count": 2},
        },
        refreshed_by="seed",
    )


def test_period_is_a_read_lens_and_does_not_pull_totvs() -> None:
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    _seed_delivery_snapshot(snapshots)

    payload = _service(gateway, snapshots).build(
        _user(*FULL_PERMS),
        branch="01",
        start_date="2026-08-25",
        end_date="2026-09-02",
    )

    assert [name for name, _ in gateway.calls if name in {"work_centers", "operations"}] == []
    assert payload["period"]["filtered"] is True
    assert [center["work_center"] for center in payload["work_centers"]] == ["CT-02"]
    assert payload["summary"]["operation_count"] == 1


def test_period_without_filter_shows_the_oldest_delivery_as_start() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_delivery_snapshot(snapshots)

    payload = _service(FakeGateway(), snapshots).build(_user(*FULL_PERMS), branch="01")

    assert payload["period"]["field"] == "delivery_date"
    assert payload["period"]["start_date"] == "2026-08-18"
    assert payload["period"]["end_date"] == "2026-09-02"
    assert payload["period"]["filtered"] is False


def test_branch_without_permission_is_denied() -> None:
    with pytest.raises(BranchAccessDenied):
        _service(FakeGateway()).build(
            _user("production-control.access", "production-control.machine-load.view"),
            branch="02",
        )


def test_missing_machine_load_permission_is_denied() -> None:
    with pytest.raises(PermissionError):
        _service(FakeGateway()).build(
            _user("production-control.access", "production-control.view.filial-01"),
            branch="01",
        )


def _seed_multi_center_snapshot(snapshots: FakeSnapshotRepo) -> tuple[date, date]:
    start = date(2026, 8, 19)
    end = date(2026, 8, 26)
    ops = [
        {**_OPERATION, "work_center": "CT-01A", "production_order": "A1", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "A2", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "A3", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "B1", "operation_code": "03"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "B2", "operation_code": "03"},
    ]
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 5},
        },
        refreshed_by="seed",
    )
    return start, end


def test_reorder_sequence_permutes_only_target_work_center() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_multi_center_snapshot(snapshots)
    refreshed_before = snapshots.get(branch="01")["refreshed_at"]
    service = _service(FakeGateway(), snapshots)

    payload = service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        ordered_keys=[
            {"production_order": "A3", "operation_code": "01"},
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A2", "operation_code": "01"},
        ],
        expected_keys=[
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A2", "operation_code": "01"},
            {"production_order": "A3", "operation_code": "01"},
        ],
    )

    assert snapshots.payload_updates == 1
    assert snapshots.upserts == 1
    row = snapshots.get(branch="01")
    assert row["refreshed_at"] == refreshed_before
    stored_ops = row["payload_json"]["operations"]
    ct01 = [op for op in stored_ops if op["work_center"] == "CT-01A"]
    ct02 = [op for op in stored_ops if op["work_center"] == "CT-02"]
    assert [op["production_order"] for op in ct01] == ["A3", "A1", "A2"]
    assert [op["production_order"] for op in ct02] == ["B1", "B2"]
    assert payload["selected"]["items"][0]["production_order"] == "A3"
    assert payload["snapshot"]["sequence_updated_at"]
    assert payload["snapshot"]["refreshed_at"]


def test_reorder_sequence_rejects_incomplete_permutation() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(ValueError, match="permutação exata"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=[
                {"production_order": "A1", "operation_code": "01"},
                {"production_order": "A2", "operation_code": "01"},
            ],
            expected_keys=[
                {"production_order": "A1", "operation_code": "01"},
                {"production_order": "A2", "operation_code": "01"},
                {"production_order": "A3", "operation_code": "01"},
            ],
        )


def test_reorder_sequence_rejects_extra_key() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(ValueError, match="permutação exata"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=[
                {"production_order": "A1", "operation_code": "01"},
                {"production_order": "A2", "operation_code": "01"},
                {"production_order": "A3", "operation_code": "01"},
                {"production_order": "ZZ", "operation_code": "99"},
            ],
            expected_keys=[
                {"production_order": "A1", "operation_code": "01"},
                {"production_order": "A2", "operation_code": "01"},
                {"production_order": "A3", "operation_code": "01"},
            ],
        )


def test_reorder_sequence_rejects_unknown_work_center() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(ValueError, match="sem operações"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-ZZZ",
            ordered_keys=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=[{"production_order": "A1", "operation_code": "01"}],
        )


def test_reorder_sequence_without_snapshot_is_not_found() -> None:
    service = _service(FakeGateway(), FakeSnapshotRepo())
    with pytest.raises(SnapshotNotFound):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=[{"production_order": "A1", "operation_code": "01"}],
        )


def _ct01a_keys(*orders: str) -> list[dict[str, str]]:
    return [{"production_order": order, "operation_code": "01"} for order in orders]


def test_reorder_sequence_rejects_stale_expected_keys() -> None:
    """Ordem-base divergente do estado vigente → 409, nada é gravado."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(MachineLoadSequenceConflict, match="mudou desde"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=_ct01a_keys("A3", "A1", "A2"),
            # Cliente leu [A2, A1, A3] — não é a ordem atual [A1, A2, A3].
            expected_keys=_ct01a_keys("A2", "A1", "A3"),
        )

    assert snapshots.payload_updates == 0


def test_reorder_sequence_rejects_expected_keys_of_wrong_set() -> None:
    """Base com chave que não existe mais no centro também é conflito."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(MachineLoadSequenceConflict):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=_ct01a_keys("A1", "A2", "A3"),
            expected_keys=_ct01a_keys("A1", "A2", "ZZ"),
        )

    assert snapshots.payload_updates == 0


def test_reorder_sequence_rejects_moved_protected_operation() -> None:
    """Run aberto no cockpit trava a posição — mover direto rejeita tudo."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(
                work_center="CT-01A", production_order="A2", operation_code="01"
            )
        ],
    )

    with pytest.raises(MachineLoadSequenceConflict, match="A2/01"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=_ct01a_keys("A2", "A1", "A3"),
            expected_keys=_ct01a_keys("A1", "A2", "A3"),
        )

    assert snapshots.payload_updates == 0


def test_reorder_sequence_rejects_indirect_displacement_of_protected() -> None:
    """Agrupar/mover outras operações não pode deslocar a protegida (D1)."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(
                work_center="CT-01A", production_order="A2", operation_code="01"
            )
        ],
    )

    with pytest.raises(MachineLoadSequenceConflict, match="A2/01"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            # «Agrupar» A1+A3 na posição de A1 deslocaria A2 para a 3ª posição.
            ordered_keys=_ct01a_keys("A1", "A3", "A2"),
            expected_keys=_ct01a_keys("A1", "A2", "A3"),
        )

    assert snapshots.payload_updates == 0


def test_reorder_sequence_allows_permutation_around_protected() -> None:
    """Protegida no mesmo índice: as posições livres continuam permutáveis."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(
                work_center="CT-01A", production_order="A2", operation_code="01"
            )
        ],
    )

    service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        ordered_keys=_ct01a_keys("A3", "A2", "A1"),
        expected_keys=_ct01a_keys("A1", "A2", "A3"),
    )

    assert snapshots.payload_updates == 1
    row = snapshots.get(branch="01")
    ct01 = [
        op
        for op in row["payload_json"]["operations"]
        if op["work_center"] == "CT-01A"
    ]
    assert [op["production_order"] for op in ct01] == ["A3", "A2", "A1"]


def test_reorder_sequence_fails_closed_when_cockpit_source_is_down() -> None:
    """Fonte de execução indisponível nunca libera a movimentação."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: (_ for _ in ()).throw(
            PluginsDatabaseConnectionError("cockpit off")
        ),
    )

    with pytest.raises(PluginsDatabaseConnectionError):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=_ct01a_keys("A3", "A1", "A2"),
            expected_keys=_ct01a_keys("A1", "A2", "A3"),
        )

    assert snapshots.payload_updates == 0


def test_patch_sequence_http_conflict_is_409(machine_load_routes_module) -> None:
    """Contrato HTTP: divergência da ordem-base volta como 409 identificável."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    client = _machine_load_client(_service(FakeGateway(), snapshots))

    response = client.patch(
        "/machine-load/sequence",
        params={"branch": "01", "workCenter": "CT-01A"},
        json={
            "ordered_keys": _ct01a_keys("A3", "A1", "A2"),
            "expected_keys": _ct01a_keys("A2", "A1", "A3"),
        },
    )

    assert response.status_code == 409
    assert snapshots.payload_updates == 0


def test_patch_sequence_http_rejects_legacy_client(
    machine_load_routes_module,
) -> None:
    """Cliente sem expected_keys (bundle antigo) recebe 409 orientando recarga — sem bypass."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    client = _machine_load_client(_service(FakeGateway(), snapshots))

    response = client.patch(
        "/machine-load/sequence",
        params={"branch": "01", "workCenter": "CT-01A"},
        json={"ordered_keys": _ct01a_keys("A3", "A1", "A2")},
    )

    assert response.status_code == 409
    assert snapshots.payload_updates == 0


def test_reorder_sequence_rejects_missing_expected_keys() -> None:
    """expected_keys=None (cliente legado) → conflito, nunca grava."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(MachineLoadSequenceConflict, match="Recarregue"):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=_ct01a_keys("A3", "A1", "A2"),
            expected_keys=None,
        )

    assert snapshots.payload_updates == 0


# ---------------------------------------------------------------------------
# Cockpit público do operador (link aberto, somente leitura)
# ---------------------------------------------------------------------------


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def __call__(self, *, branch: str, reason: str, work_center: str | None = None) -> None:
        self.events.append({"branch": branch, "reason": reason, "work_center": work_center})


def _service_with_notifier(
    gateway: FakeGateway,
    snapshots: FakeSnapshotRepo,
    notifier: RecordingNotifier,
    *,
    open_runs: list[dict[str, Any]] | None = None,
) -> MachineLoadService:
    run_items = list(open_runs) if open_runs is not None else []
    return MachineLoadService(
        gateway,
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        change_notifier=notifier,
        open_run_items=lambda **kwargs: list(run_items),
    )


def _seed_default_window_snapshot(
    service: MachineLoadService,
    snapshots: FakeSnapshotRepo,
) -> tuple[date, date]:
    """Semeia o snapshot na janela padrão — a leitura pública não aceita período custom."""
    start, end = service.resolve_delivery_window(start_date=None, end_date=None)
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [
                {**_OPERATION, "production_order": "B1"},
                {**_OPERATION, "production_order": "B2"},
            ],
            "summary": {"work_center_count": 2, "operation_count": 2},
            "sequence_updated_at": "2026-08-19T22:10:00+00:00",
            "sequence_updated_by": "planner-1",
        },
        refreshed_by="planner-1",
    )
    snapshots.publish("01")
    return start, end


def test_public_build_returns_queue_in_pcp_order() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_default_window_snapshot(service, snapshots)

    payload = service.build_public(branch="01", work_center="CT-02")

    assert payload["selected"]["work_center"] == "CT-02"
    assert [item["production_order"] for item in payload["selected"]["items"]] == ["B1", "B2"]
    assert payload["work_centers"]


def test_public_build_hides_pcp_identity() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_default_window_snapshot(service, snapshots)

    payload = service.build_public(branch="01")

    assert "refreshed_by" not in payload["snapshot"]
    assert "sequence_updated_by" not in payload["snapshot"]
    assert payload["snapshot"]["refreshed_at"]
    assert payload["snapshot"]["sequence_updated_at"]


def test_public_build_never_seeds_from_totvs() -> None:
    gateway = FakeGateway()
    service = _service(gateway, FakeSnapshotRepo())

    with pytest.raises(SnapshotNotFound):
        service.build_public(branch="01")

    assert gateway.calls == []


def test_public_build_rejects_unknown_branch() -> None:
    with pytest.raises(InvalidBranch):
        _service(FakeGateway()).build_public(branch="09")


def _open_run(
    *,
    work_center: str = "CT-02",
    production_order: str = "B1",
    operation_code: str = "03",
    operator_name: str | None = "MARIA",
) -> dict[str, Any]:
    return {
        "id": "run-1",
        "branch": "01",
        "work_center": work_center,
        "production_order": production_order,
        "operation_code": operation_code,
        "operator_code": "20040",
        "operator_name": operator_name,
        "status": "running",
        "started_at": datetime(2026, 8, 20, 8, 30, tzinfo=timezone.utc),
    }


def _run_item(
    *,
    work_center: str = "CT-01A",
    production_order: str = "99900001001",
    operation_code: str = "01",
    run_status: str = "running",
    operational_state: str | None = "producing",
    display_status: str = "producing",
    integrity_status: str = "complete",
) -> dict[str, Any]:
    """Item projetado de run aberto — shape de open_run_items/cockpit-status."""
    return {
        "run_id": "run-1",
        "work_center": work_center,
        "production_order": production_order,
        "operation_code": operation_code,
        "run_status": run_status,
        "operational_state": operational_state,
        "display_status": display_status,
        "integrity_status": integrity_status,
        "started_at": "2026-08-20T08:30:00+00:00",
    }


def test_public_build_marks_in_production_from_cockpit_run() -> None:
    """«Em produção» na fila pública vem do run MES local, não do cronômetro TOTVS."""
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    service._list_open_runs = lambda branch: [_open_run()]  # noqa: SLF001
    _seed_default_window_snapshot(service, snapshots)

    payload = service.build_public(branch="01", work_center="CT-02")
    items = payload["selected"]["items"]
    b1 = next(item for item in items if item["production_order"] == "B1")
    b2 = next(item for item in items if item["production_order"] == "B2")

    assert b1["is_in_production"] is True
    assert b1["production_status"] == "in_progress"
    assert b1["active_operator_name"] == "MARIA"
    assert b1["production_started_time"] == "08:30"
    assert b2["is_in_production"] is False


def test_public_build_ignores_totvs_cronometro_without_local_run() -> None:
    """Cronômetro aberto no TOTVS sem run do cockpit não marca «em produção»."""
    gateway = FakeGateway()
    gateway.status_by_key[("B1", "03")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_code": "TOTVS-1",
        "active_operator_name": "OPERADOR COLETOR",
        "active_operator_count": 1,
    }
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service._list_open_runs = lambda branch: []  # noqa: SLF001
    _seed_default_window_snapshot(service, snapshots)

    payload = service.build_public(branch="01", work_center="CT-02")
    b1 = next(
        item for item in payload["selected"]["items"] if item["production_order"] == "B1"
    )

    assert b1["is_in_production"] is False
    assert b1["production_status"] == "started"
    assert b1["active_operator_name"] is None
    assert b1["production_started_time"] is None


def test_public_build_run_in_other_work_center_does_not_mark() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    service._list_open_runs = lambda branch: [_open_run(work_center="CT-99")]  # noqa: SLF001
    _seed_default_window_snapshot(service, snapshots)

    payload = service.build_public(branch="01", work_center="CT-02")
    b1 = next(
        item for item in payload["selected"]["items"] if item["production_order"] == "B1"
    )

    assert b1["is_in_production"] is False


def test_managerial_build_keeps_totvs_production_status() -> None:
    """Visão gerencial continua refletindo o chão de fábrica (HZA/TOTVS)."""
    gateway = FakeGateway()
    gateway.status_by_key[("B1", "03")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_name": "OPERADOR COLETOR",
        "active_operator_count": 1,
    }
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    _seed_default_window_snapshot(service, snapshots)
    # O build gerencial lê o status só do cache — a consulta HZA vive em live_status.
    service.live_status(_user(*FULL_PERMS), branch="01")

    payload = service.build(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-02",
    )
    b1 = next(
        item for item in payload["selected"]["items"] if item["production_order"] == "B1"
    )

    assert b1["is_in_production"] is True
    assert b1["active_operator_name"] == "OPERADOR COLETOR"


def _seed_public_balance_snapshot(
    service: MachineLoadService,
    snapshots: FakeSnapshotRepo,
    operations: list[dict[str, Any]],
) -> None:
    start, end = service.resolve_delivery_window(start_date=None, end_date=None)
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": operations,
            "summary": {"work_center_count": 2, "operation_count": len(operations)},
            "sequence_updated_at": "2026-08-19T22:10:00+00:00",
        },
        refreshed_by="planner-1",
    )
    snapshots.publish("01")


def _balance_op(
    order: str,
    *,
    operation_pending: float | None | object = "missing",
    pending: float | None | object = "missing",
) -> dict[str, Any]:
    item = {**_OPERATION, "production_order": order}
    if operation_pending != "missing":
        item["operation_pending_qty"] = operation_pending
    else:
        item.pop("operation_pending_qty", None)
    if pending != "missing":
        item["pending_qty"] = pending
    return item


def _public_orders(payload: dict[str, Any], work_center: str = "CT-02") -> list[str]:
    return [
        item["production_order"]
        for item in payload["selected"]["items"]
        if item["work_center"] == work_center
    ]


def test_public_queue_open_only_keeps_positive_balance() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _balance_op("A", operation_pending=10.0),
            _balance_op("B", operation_pending=0.0),
            _balance_op("C", operation_pending=35.0),
            _balance_op("D", operation_pending=0.0),
        ],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert _public_orders(payload) == ["A", "C"]


def test_public_queue_open_only_drops_zero_and_negative_balance() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _balance_op("ZERO", operation_pending=0.0),
            _balance_op("NEG", operation_pending=-0.001),
            _balance_op("EPS", operation_pending=1e-10),
            _balance_op("OPEN", operation_pending=0.5),
        ],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert _public_orders(payload) == ["OPEN"]


def test_public_queue_open_only_keeps_unknown_balance() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _balance_op("NULL-OP", operation_pending=None, pending=None),
            _balance_op("NOFIELDS", operation_pending="missing", pending="missing"),
        ],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert _public_orders(payload) == ["NULL-OP", "NOFIELDS"]


def test_public_queue_pending_qty_is_only_fallback() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _balance_op("FB-ZERO", operation_pending=None, pending=0.0),
            _balance_op("FB-OPEN", operation_pending=None, pending=12.0),
            # Saldo da operação manda sobre o cabeçalho da OP.
            _balance_op("HDR-ONLY", operation_pending=0.0, pending=100.0),
        ],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert _public_orders(payload) == ["FB-OPEN"]


def test_public_queue_open_only_pagination_counts_open_items() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _balance_op("O1"),
            _balance_op("C1", operation_pending=0.0),
            _balance_op("O2"),
            _balance_op("C2", operation_pending=0.0),
            _balance_op("O3"),
        ],
    )

    payload = service.build_public(branch="01", work_center="CT-02")
    pagination = payload["selected"]["pagination"]

    assert _public_orders(payload) == ["O1", "O2", "O3"]
    assert pagination == {"page": 1, "page_size": 3, "total": 3, "is_complete": True}


def test_public_queue_open_only_does_not_mutate_snapshot() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _balance_op("OPEN"),
            _balance_op("DONE", operation_pending=0.0),
        ],
    )
    before = snapshots.get(branch="01")["payload_json"]

    service.build_public(branch="01", work_center="CT-02")

    after = snapshots.get(branch="01")["payload_json"]
    assert after == before
    assert [op["production_order"] for op in after["operations"]] == ["OPEN", "DONE"]
    assert snapshots.payload_updates == 0


def test_public_queue_empty_center_keeps_work_center_in_selector() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_balance_op("DONE", operation_pending=0.0)],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert payload["selected"]["items"] == []
    centers = [c["work_center"] for c in payload["work_centers"]]
    assert "CT-02" in centers


def test_public_queue_open_only_does_not_touch_open_runs() -> None:
    """OP concluída sai da projeção pública; o run aberto continua recuperável."""
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    runs = [_open_run(production_order="DONE")]
    service._list_open_runs = lambda branch: runs  # noqa: SLF001
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_balance_op("DONE", operation_pending=0.0)],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert payload["selected"]["items"] == []
    assert service._list_open_runs("01") == runs  # noqa: SLF001


def test_reorder_sequence_notifies_connected_cockpits() -> None:
    snapshots = FakeSnapshotRepo()
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), snapshots, notifier)
    start, end = _seed_multi_center_snapshot(snapshots)
    snapshots.publish("01")

    service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        ordered_keys=[
            {"production_order": "A3", "operation_code": "01"},
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A2", "operation_code": "01"},
        ],
        expected_keys=[
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A2", "operation_code": "01"},
            {"production_order": "A3", "operation_code": "01"},
        ],
    )

    assert notifier.events == [
        {"branch": "01", "reason": "sequence", "work_center": "CT-01A"}
    ]


def test_refresh_does_not_notify_connected_cockpits() -> None:
    """Atualizar reescreve só o WORKING: cockpit lê PUBLISHED, evento seria ruído."""
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), FakeSnapshotRepo(), notifier)

    service.refresh(_user(*FULL_PERMS), branch="01")

    assert notifier.events == []


def test_failed_notification_does_not_break_the_write() -> None:
    snapshots = FakeSnapshotRepo()

    def exploding_notifier(**_kwargs: Any) -> None:
        raise RuntimeError("hub fora do ar")

    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        change_notifier=exploding_notifier,
        open_run_items=lambda **kwargs: [],
    )
    start, end = _seed_multi_center_snapshot(snapshots)

    payload = service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-02",
        ordered_keys=[
            {"production_order": "B2", "operation_code": "03"},
            {"production_order": "B1", "operation_code": "03"},
        ],
        expected_keys=[
            {"production_order": "B1", "operation_code": "03"},
            {"production_order": "B2", "operation_code": "03"},
        ],
    )

    assert [item["production_order"] for item in payload["selected"]["items"]] == ["B2", "B1"]
    assert snapshots.payload_updates == 1


def test_public_cockpit_token_matches_catalog_slug() -> None:
    access = PublicCockpitAccessService()

    assert access.is_valid_token(access.token()) is True
    assert access.is_valid_token(" ABERTO ") is True
    assert access.is_valid_token("outro-token") is False
    assert access.is_valid_token(None) is False


class FakeDrawingLibrary:
    def __init__(self, *, missing: bool = False) -> None:
        self.calls: list[str] = []
        self.missing = missing
        self.file = DrawingFile(path=Path("/drawing-pdfs/90262957.pdf"), filename="90262957.pdf")

    def resolve_pdf(self, code: str) -> DrawingFile:
        self.calls.append(code)
        if self.missing:
            raise DrawingNotFound("missing on fileserver")
        return self.file


def _drawing_service(
    snapshots: FakeSnapshotRepo,
    drawings: FakeDrawingLibrary,
) -> PublicMachineLoadDrawingService:
    return PublicMachineLoadDrawingService(
        access=PublicCockpitAccessService(),
        machine_load=_service(FakeGateway(), snapshots),
        drawings=drawings,
    )


def _seed_public_queue_with_pa(
    service: MachineLoadService,
    snapshots: FakeSnapshotRepo,
    *,
    pa_code: str = "90262957",
) -> None:
    start, end = service.resolve_delivery_window(start_date=None, end_date=None)
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [
                {**_OPERATION, "production_order": "B1", "pa_product_code": pa_code},
                {**_OPERATION, "production_order": "B2", "pa_product_code": None},
            ],
            "summary": {"work_center_count": 2, "operation_count": 2},
        },
        refreshed_by="planner-1",
    )
    snapshots.publish("01")


def test_public_drawing_returns_pdf_when_pa_is_in_queue() -> None:
    snapshots = FakeSnapshotRepo()
    drawings = FakeDrawingLibrary()
    machine_load = _service(FakeGateway(), snapshots)
    _seed_public_queue_with_pa(machine_load, snapshots)
    service = _drawing_service(snapshots, drawings)

    drawing = service.open_pdf(token="aberto", branch="01", pa_code="90262957")

    assert drawing.filename == "90262957.pdf"
    assert drawings.calls == ["90262957"]


def test_public_drawing_rejects_pa_outside_published_queue() -> None:
    snapshots = FakeSnapshotRepo()
    drawings = FakeDrawingLibrary()
    machine_load = _service(FakeGateway(), snapshots)
    _seed_public_queue_with_pa(machine_load, snapshots)
    service = _drawing_service(snapshots, drawings)

    with pytest.raises(DrawingNotFound, match="não está na fila publicada"):
        service.open_pdf(token="aberto", branch="01", pa_code="99999999")

    assert drawings.calls == []


def test_public_drawing_rejects_invalid_token() -> None:
    snapshots = FakeSnapshotRepo()
    drawings = FakeDrawingLibrary()
    machine_load = _service(FakeGateway(), snapshots)
    _seed_public_queue_with_pa(machine_load, snapshots)
    service = _drawing_service(snapshots, drawings)

    with pytest.raises(DrawingNotFound, match="inválido"):
        service.open_pdf(token="outro", branch="01", pa_code="90262957")

    assert drawings.calls == []


def test_public_drawing_maps_missing_fileserver_pdf() -> None:
    snapshots = FakeSnapshotRepo()
    drawings = FakeDrawingLibrary(missing=True)
    machine_load = _service(FakeGateway(), snapshots)
    _seed_public_queue_with_pa(machine_load, snapshots)
    service = _drawing_service(snapshots, drawings)

    with pytest.raises(DrawingNotFound, match="missing on fileserver"):
        service.open_pdf(token="aberto", branch="01", pa_code="90262957")

    assert drawings.calls == ["90262957"]


def _seed_locate_snapshot(snapshots: FakeSnapshotRepo) -> tuple[date, date]:
    start = date(2026, 8, 19)
    end = date(2026, 8, 26)
    ops = [
        {
            **_OPERATION,
            "work_center": "CT-01A",
            "work_center_name": "CORTE E DECAPE",
            "production_order": "10840401003",
            "operation_code": "01",
            "operation_description": "CORTAR",
            "product_code": "50233616",
            "pa_product_code": "90262910",
            "pa_due_date": "2026-08-24",
            "scheduled_date": "2026-08-19",
            "scheduled_start_time": "06:02",
            "production_status": "started",
        },
        {
            **_OPERATION,
            "work_center": "CT-02",
            "work_center_name": "APLICAÇÃO DE TERMINAIS",
            "production_order": "10840401003",
            "operation_code": "03",
            "operation_description": "APLICAR",
            "product_code": "50233617",
            "pa_product_code": "90262910",
            "pa_due_date": "2026-08-24",
            "scheduled_date": "2026-08-20",
            "scheduled_start_time": "07:00",
            "production_status": "not_started",
        },
        {
            **_OPERATION,
            "work_center": "CT-01A",
            "work_center_name": "CORTE E DECAPE",
            "production_order": "10840402001",
            "operation_code": "01",
            "operation_description": "CORTAR",
            "product_code": "50233999",
            "pa_product_code": "90262910",
            "pa_due_date": "2026-08-24",
            "scheduled_date": "2026-08-22",
            "scheduled_start_time": "09:00",
            "production_status": "not_started",
        },
        {
            **_OPERATION,
            "work_center": "CT-01A",
            "work_center_name": "CORTE E DECAPE",
            "production_order": "24640401002",
            "operation_code": "01",
            "operation_description": "CORTAR",
            "product_code": "50234000",
            "pa_product_code": "90262910",
            "pa_due_date": "2026-08-25",
            "scheduled_date": "2026-08-23",
            "scheduled_start_time": "10:00",
            "production_status": "not_started",
        },
        {
            **_OPERATION,
            "work_center": "CT-01A",
            "work_center_name": "CORTE E DECAPE",
            "production_order": "99900001001",
            "operation_code": "01",
            "product_code": "50111111",
            "pa_product_code": "90111111",
            "scheduled_date": "2026-08-21",
            "scheduled_start_time": "08:00",
        },
    ]
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 5},
        },
        refreshed_by="seed",
    )
    return start, end


def test_locate_by_pa_lists_each_conjunto_of_product() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_locate_snapshot(snapshots)
    payload = _service(FakeGateway(), snapshots).locate(
        _user(*FULL_PERMS),
        branch="01",
        query="90262910",
    )

    assert payload["match_count"] == 4
    assert payload["journey_count"] == 2
    assert payload["message"] is None
    keys = [journey["key"] for journey in payload["journeys"]]
    assert keys == ["108404", "246404"]
    assert all(journey["kind"] == "op" for journey in payload["journeys"])
    first = payload["journeys"][0]
    assert first["pa_product_code"] == "90262910"
    assert first["pa_due_date"] == "2026-08-24"
    assert [stop["production_order"] for stop in first["stops"]] == [
        "10840401003",
        "10840401003",
        "10840402001",
    ]
    assert first["stops"][0]["queue_position"] == 1
    assert first["stops"][0]["queue_size"] == 4
    assert first["stops"][1]["queue_position"] == 1
    assert first["stops"][1]["queue_size"] == 1


def test_locate_by_op_expands_all_orders_of_conjunto_c2_num() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_locate_snapshot(snapshots)
    payload = _service(FakeGateway(), snapshots).locate(
        _user(*FULL_PERMS),
        branch="01",
        query="10840401003",
    )

    assert payload["match_count"] == 3
    assert payload["journey_count"] == 1
    journey = payload["journeys"][0]
    assert journey["kind"] == "op"
    assert journey["key"] == "108404"
    assert journey["pa_product_code"] == "90262910"
    orders = [stop["production_order"] for stop in journey["stops"]]
    assert orders == ["10840401003", "10840401003", "10840402001"]
    assert "24640401002" not in orders


def test_locate_by_c2_num_prefix_alone() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_locate_snapshot(snapshots)
    payload = _service(FakeGateway(), snapshots).locate(
        _user(*FULL_PERMS),
        branch="01",
        query="108404",
    )

    assert payload["journey_count"] == 1
    assert payload["journeys"][0]["key"] == "108404"
    assert payload["match_count"] == 3


def test_locate_no_match_returns_empty_with_message() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_locate_snapshot(snapshots)
    payload = _service(FakeGateway(), snapshots).locate(
        _user(*FULL_PERMS),
        branch="01",
        query="00000000",
    )
    assert payload["match_count"] == 0
    assert payload["journeys"] == []
    assert payload["message"]
    assert "00000000" in payload["message"]


def test_locate_empty_query_is_rejected() -> None:
    with pytest.raises(ValueError, match="OP|conjunto"):
        _service(FakeGateway()).locate(_user(*FULL_PERMS), branch="01", query="  ")


def test_locate_without_snapshot_is_not_found() -> None:
    with pytest.raises(SnapshotNotFound):
        _service(FakeGateway(), FakeSnapshotRepo()).locate(
            _user(*FULL_PERMS),
            branch="01",
            query="90262910",
        )


def _seed_priority_snapshot(snapshots: FakeSnapshotRepo) -> tuple[date, date]:
    start = date(2026, 8, 19)
    end = date(2026, 8, 26)
    ops = [
        {**_OPERATION, "work_center": "CT-01A", "production_order": "99900001001", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "88800001001", "operation_code": "02"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "10840401003", "operation_code": "03"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "77700001001", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "10840402001", "operation_code": "05"},
    ]
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 5},
        },
        refreshed_by="seed",
    )
    return start, end


def _queue(snapshots: FakeSnapshotRepo, start: date, end: date, center: str) -> list[str]:
    payload = snapshots.rows["01"]["payload_json"]
    return [
        f"{item['production_order']}:{item['operation_code']}"
        for item in payload["operations"]
        if item["work_center"] == center
    ]


def test_prioritize_conjunto_moves_all_orders_to_top_of_each_center() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    payload = _service(FakeGateway(), snapshots).prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="108404",
        work_center="CT-01A",
    )

    assert snapshots.payload_updates == 1
    assert _queue(snapshots, start, end, "CT-01A")[0] == "10840401003:03"
    assert _queue(snapshots, start, end, "CT-02")[0] == "10840402001:05"
    prioritization = payload["prioritization"]
    assert prioritization["order_number"] == "108404"
    assert sorted(prioritization["work_centers"]) == ["CT-01A", "CT-02"]
    assert prioritization["operation_count"] == 2
    assert prioritization["kept_ahead_count"] == 0
    assert "108404" in prioritization["message"]


def test_prioritize_conjunto_keeps_running_operation_ahead() -> None:
    """Run aberto no cockpit protege a posição — mesmo sem flags no snapshot."""
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    payload = _service(
        FakeGateway(), snapshots, open_runs=[_run_item()]
    ).prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="108404",
    )

    assert _queue(snapshots, start, end, "CT-01A") == [
        "99900001001:01",
        "10840401003:03",
        "88800001001:02",
    ]
    assert payload["prioritization"]["kept_ahead_count"] == 1


def test_prioritize_conjunto_hza_in_progress_without_run_does_not_protect() -> None:
    """Apontamento HZA antigo aberto não trava posição sem run do cockpit."""
    gateway = FakeGateway()
    gateway.status_by_key[("99900001001", "01")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "active_operator_name": "SILVANA ANDRADE DOS SANTOS",
        "active_operator_count": 1,
        "appointment_count": 3,
    }
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    payload = _service(gateway, snapshots).prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="108404",
    )

    assert _queue(snapshots, start, end, "CT-01A") == [
        "10840401003:03",
        "99900001001:01",
        "88800001001:02",
    ]
    assert payload["prioritization"]["kept_ahead_count"] == 0


def test_prioritize_conjunto_stopped_and_paused_runs_protect() -> None:
    """stopped e paused também travam a posição — só run fechado libera."""
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(run_status="running", operational_state="stopped",
                      display_status="stopped"),
        ],
    ).prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="108404",
    )

    assert _queue(snapshots, start, end, "CT-01A") == [
        "99900001001:01",
        "10840401003:03",
        "88800001001:02",
    ]


def test_prioritize_conjunto_inconsistent_run_keeps_protection() -> None:
    """Run aberto inconsistente protege conservadoramente — nunca libera."""
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(
                run_status="paused",
                operational_state=None,
                display_status="unknown",
                integrity_status="inconsistent",
            ),
        ],
    ).prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="108404",
    )

    assert _queue(snapshots, start, end, "CT-01A") == [
        "99900001001:01",
        "10840401003:03",
        "88800001001:02",
    ]


def test_prioritize_conjunto_fails_when_cockpit_source_is_down() -> None:
    """Falha na fonte oficial: erro controlado, fila intacta, sem HZA/broadcast."""
    snapshots = FakeSnapshotRepo()
    _seed_priority_snapshot(snapshots)
    notifier = RecordingNotifier()
    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        change_notifier=notifier,
        open_run_items=lambda **kwargs: (_ for _ in ()).throw(
            PluginsDatabaseConnectionError("db down")
        ),
    )

    with pytest.raises(PluginsDatabaseConnectionError):
        service.prioritize_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="108404",
        )

    # A fila permanece exatamente como o snapshot original e nada é notificado.
    assert [item["production_order"] for item in snapshots.rows["01"]["payload_json"]["operations"]] == [
        "99900001001",
        "88800001001",
        "10840401003",
        "77700001001",
        "10840402001",
    ]
    assert notifier.events == []


def test_prioritize_conjunto_uses_only_runs_of_the_requested_branch() -> None:
    """Runs da filial 01 não protegem operações da filial 02."""
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    snapshots.upsert(
        branch="02",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [
                {
                    **_OPERATION,
                    "work_center": "CT-01A",
                    "production_order": "99900001001",
                    "operation_code": "01",
                },
                {
                    **_OPERATION,
                    "work_center": "CT-01A",
                    "production_order": "10840401003",
                    "operation_code": "03",
                },
            ],
            "summary": {"work_center_count": 1, "operation_count": 2},
        },
        refreshed_by="seed",
    )

    def runs_by_branch(*, branch: str, **kwargs: Any) -> list[dict[str, Any]]:
        return [_run_item()] if branch == "01" else []

    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=runs_by_branch,
    )
    user = _user(*FULL_PERMS)

    service.prioritize_conjunto(user, branch="02", order_number="108404")

    # Filial 02 sem run: o conjunto vai ao topo — a proteção do run da 01 não vaza.
    assert _queue(snapshots, start, end, "CT-01A") == [
        "99900001001:01",
        "88800001001:02",
        "10840401003:03",
    ]
    queue02 = [
        f"{i['production_order']}:{i['operation_code']}"
        for i in snapshots.rows["02"]["payload_json"]["operations"]
    ]
    assert queue02 == ["10840401003:03", "99900001001:01"]


def test_prioritize_conjunto_without_run_source_fails_closed() -> None:
    """Sem fonte oficial injetada, a mutação não roda com proteção vazia."""
    snapshots = FakeSnapshotRepo()
    _seed_priority_snapshot(snapshots)
    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
    )

    with pytest.raises(RuntimeError, match="cockpit"):
        service.prioritize_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="108404",
        )


def test_prioritize_conjunto_accepts_full_production_order() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    payload = _service(FakeGateway(), snapshots).prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="10840401003",
    )

    assert payload["prioritization"]["order_number"] == "108404"
    assert _queue(snapshots, start, end, "CT-02")[0] == "10840402001:05"


def test_prioritize_conjunto_not_in_queue_is_rejected() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    with pytest.raises(ValueError, match="123456"):
        _service(FakeGateway(), snapshots).prioritize_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="123456",
        )
    assert snapshots.payload_updates == 0


def test_prioritize_conjunto_requires_order_number_with_six_digits() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    with pytest.raises(ValueError):
        _service(FakeGateway(), snapshots).prioritize_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="1084",
        )


def test_prioritize_conjunto_without_snapshot_is_not_found() -> None:
    with pytest.raises(SnapshotNotFound):
        _service(FakeGateway(), FakeSnapshotRepo()).prioritize_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="108404",
        )


def test_prioritize_conjunto_denies_user_without_permission() -> None:
    snapshots = FakeSnapshotRepo()
    start, end = _seed_priority_snapshot(snapshots)
    with pytest.raises((PermissionError, BranchAccessDenied)):
        _service(FakeGateway(), snapshots).prioritize_conjunto(
            _user("production-control.access"),
            branch="01",
            order_number="108404",
        )


def _seed_optimization_snapshot(snapshots: FakeSnapshotRepo) -> None:
    ops = [
        {**_OPERATION, "work_center": "CT-01A", "production_order": "99900001001", "operation_code": "01", "due_date": "2026-09-30"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "88800001001", "operation_code": "02", "due_date": "2026-08-21"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "10840401003", "operation_code": "03", "due_date": None, "pa_due_date": None},
        {**_OPERATION, "work_center": "CT-02", "production_order": "77700001001", "operation_code": "01", "due_date": "2026-10-15"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "10840402001", "operation_code": "05", "due_date": "2026-08-25"},
    ]
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 3),
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 5},
        },
        refreshed_by="seed",
    )


def _center_orders(snapshots: FakeSnapshotRepo, center: str) -> list[str]:
    return [
        item["production_order"]
        for item in snapshots.rows["01"]["payload_json"]["operations"]
        if item["work_center"] == center
    ]


def test_optimize_delivery_sequence_orders_every_work_center_by_pa_due_date() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_optimization_snapshot(snapshots)

    payload = _service(FakeGateway(), snapshots).optimize_delivery_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
    )

    assert snapshots.payload_updates == 1
    # Sem entrega vai para o fim da fila do próprio centro.
    assert _center_orders(snapshots, "CT-01A") == [
        "88800001001",
        "99900001001",
        "10840401003",
    ]
    assert _center_orders(snapshots, "CT-02") == ["10840402001", "77700001001"]
    optimization = payload["optimization"]
    assert sorted(optimization["work_centers"]) == ["CT-01A", "CT-02"]
    assert optimization["moved_operation_count"] == 4
    assert optimization["missing_due_date_count"] == 1
    assert snapshots.rows["01"]["payload_json"]["sequence_updated_by"]


def test_optimize_delivery_sequence_is_idempotent() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_optimization_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    service.optimize_delivery_sequence(_user(*FULL_PERMS), branch="01")
    payload = service.optimize_delivery_sequence(_user(*FULL_PERMS), branch="01")

    assert snapshots.payload_updates == 1
    assert payload["optimization"]["work_centers"] == []
    assert payload["optimization"]["moved_operation_count"] == 0


def test_optimize_delivery_sequence_keeps_withdrawn_conjunto_out_of_the_queue() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_optimization_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)
    service.withdraw_conjunto(_user(*FULL_PERMS), branch="01", order_number="108404")

    payload = service.optimize_delivery_sequence(_user(*FULL_PERMS), branch="01")

    stored = snapshots.rows["01"]["payload_json"]["operations"]
    # O conjunto retirado continua gravado na posição original do payload.
    assert [item["production_order"] for item in stored if item["work_center"] == "CT-01A"] == [
        "88800001001",
        "99900001001",
        "10840401003",
    ]
    assert payload["withdrawn"]["conjunto_count"] == 1
    visible = [item["production_order"] for item in payload["selected"]["items"]]
    assert "10840401003" not in visible


def test_optimize_delivery_sequence_notifies_connected_cockpits() -> None:
    snapshots = FakeSnapshotRepo()
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), snapshots, notifier)
    _seed_optimization_snapshot(snapshots)
    snapshots.publish("01")

    service.optimize_delivery_sequence(_user(*FULL_PERMS), branch="01", work_center="CT-01A")

    assert notifier.events == [
        {"branch": "01", "reason": "delivery_sequence", "work_center": None}
    ]


def test_optimize_delivery_sequence_without_snapshot_is_not_found() -> None:
    with pytest.raises(SnapshotNotFound):
        _service(FakeGateway(), FakeSnapshotRepo()).optimize_delivery_sequence(
            _user(*FULL_PERMS),
            branch="01",
        )


def test_optimize_delivery_sequence_denies_user_without_permission() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_optimization_snapshot(snapshots)
    with pytest.raises((PermissionError, BranchAccessDenied)):
        _service(FakeGateway(), snapshots).optimize_delivery_sequence(
            _user("production-control.access"),
            branch="01",
        )


def _withdraw(
    service: MachineLoadService,
    start: date,
    end: date,
    *,
    order_number: str = "108404",
    work_center: str | None = "CT-01A",
) -> dict[str, Any]:
    return service.withdraw_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number=order_number,
        work_center=work_center,
    )


def test_withdraw_conjunto_removes_every_operation_from_the_queue() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    payload = _withdraw(service, start, end)

    assert [item["production_order"] for item in payload["selected"]["items"]] == [
        "99900001001",
        "88800001001",
    ]
    other = service.build(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-02",
    )
    assert [item["production_order"] for item in other["selected"]["items"]] == ["77700001001"]


def test_withdraw_conjunto_reports_entry_and_counts() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    payload = _withdraw(service, start, end)

    withdrawal = payload["withdrawal"]
    assert withdrawal["order_number"] == "108404"
    assert withdrawal["action"] == "withdrawn"
    assert withdrawal["operation_count"] == 2
    assert sorted(withdrawal["work_centers"]) == ["CT-01A", "CT-02"]
    assert "108404" in withdrawal["message"]

    assert payload["withdrawn"]["conjunto_count"] == 1
    assert payload["withdrawn"]["operation_count"] == 2
    entry = payload["withdrawn"]["items"][0]
    assert entry["order_number"] == "108404"
    assert entry["withdrawn_by"]
    assert entry["withdrawn_at"]
    assert payload["summary"]["operation_count"] == 3
    counts = {item["work_center"]: item["operation_count"] for item in payload["work_centers"]}
    assert counts == {"CT-01A": 2, "CT-02": 1}


def test_withdrawn_conjunto_stays_in_the_snapshot_at_the_original_position() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    _withdraw(service, start, end)

    assert _queue(snapshots, start, end, "CT-01A") == [
        "99900001001:01",
        "88800001001:02",
        "10840401003:03",
    ]


def test_restore_conjunto_brings_the_queue_back() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _withdraw(service, start, end)

    payload = service.restore_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="10840401003",
        work_center="CT-01A",
    )

    assert payload["withdrawal"]["action"] == "restored"
    assert payload["withdrawn"]["conjunto_count"] == 0
    assert [item["production_order"] for item in payload["selected"]["items"]] == [
        "99900001001",
        "88800001001",
        "10840401003",
    ]


def test_withdraw_twice_is_rejected_and_restore_requires_a_withdrawal() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _withdraw(service, start, end)

    with pytest.raises(ValueError, match="108404"):
        _withdraw(service, start, end)
    with pytest.raises(ValueError, match="777000"):
        service.restore_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="777000",
        )


def test_withdraw_conjunto_outside_the_queue_is_rejected() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    with pytest.raises(ValueError, match="123456"):
        _withdraw(service, start, end, order_number="123456")
    with pytest.raises(ValueError):
        _withdraw(service, start, end, order_number="1084")
    with pytest.raises((PermissionError, BranchAccessDenied)):
        service.withdraw_conjunto(
            _user("production-control.access"),
            branch="01",
            order_number="108404",
        )


def test_withdraw_conjunto_without_snapshot_is_not_found() -> None:
    with pytest.raises(SnapshotNotFound):
        _service(FakeGateway(), FakeSnapshotRepo()).withdraw_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="108404",
        )


def test_withdraw_conjunto_notifies_connected_cockpits() -> None:
    snapshots = FakeSnapshotRepo()
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), snapshots, notifier)
    start, end = _seed_priority_snapshot(snapshots)
    snapshots.publish("01")

    _withdraw(service, start, end)

    assert notifier.events == [
        {"branch": "01", "reason": "withdrawal", "work_center": None}
    ]


def test_prioritize_ignores_withdrawn_operations() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _withdraw(service, start, end)

    service.prioritize_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="888000",
    )

    # A retirada segue no fim do array, na posição em que estava.
    assert _queue(snapshots, start, end, "CT-01A") == [
        "88800001001:02",
        "99900001001:01",
        "10840401003:03",
    ]
    with pytest.raises(ValueError, match="108404"):
        service.prioritize_conjunto(
            _user(*FULL_PERMS),
            branch="01",
            order_number="108404",
        )


def test_reorder_sequence_ignores_withdrawn_operations() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _withdraw(service, start, end)

    service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        ordered_keys=[
            {"production_order": "88800001001", "operation_code": "02"},
            {"production_order": "99900001001", "operation_code": "01"},
        ],
        expected_keys=[
            {"production_order": "99900001001", "operation_code": "01"},
            {"production_order": "88800001001", "operation_code": "02"},
        ],
    )

    assert _queue(snapshots, start, end, "CT-01A") == [
        "88800001001:02",
        "99900001001:01",
        "10840401003:03",
    ]


def test_locate_marks_withdrawn_stops() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _withdraw(service, start, end)

    result = service.locate(
        _user(*FULL_PERMS),
        branch="01",
        query="108404",
    )

    journey = result["journeys"][0]
    assert journey["is_withdrawn"] is True
    assert all(stop["is_withdrawn"] for stop in journey["stops"])
    assert all(stop["queue_position"] == 0 for stop in journey["stops"])


def _transfer(
    service: MachineLoadService,
    start: date,
    end: date,
    *,
    production_order: str = "10840401003",
    operation_code: str = "03",
    target: str = "CT-02",
    work_center: str | None = "CT-01A",
) -> dict[str, Any]:
    return service.transfer_operation(
        _user(*FULL_PERMS),
        branch="01",
        production_order=production_order,
        operation_code=operation_code,
        target_work_center=target,
        work_center=work_center,
    )


def test_transfer_operation_moves_it_to_the_end_of_the_target_queue() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    payload = _transfer(service, start, end)

    assert _queue(snapshots, start, end, "CT-01A") == ["99900001001:01", "88800001001:02"]
    assert _queue(snapshots, start, end, "CT-02") == [
        "77700001001:01",
        "10840402001:05",
        "10840401003:03",
    ]
    transfer = payload["transfer"]
    assert transfer["source_work_center"] == "CT-01A"
    assert transfer["target_work_center"] == "CT-02"
    assert transfer["returned_to_origin"] is False
    assert "CT-02" in transfer["message"]


def test_transfer_conjunto_moves_only_ops_in_source_center() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    # Antes: 10840401003 em CT-01A e 10840402001 em CT-02 (mesmo conjunto).
    payload = service.transfer_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="10840401003",
        source_work_center="CT-01A",
        target_work_center="CT-02",
        work_center="CT-02",
    )

    assert _queue(snapshots, start, end, "CT-01A") == ["99900001001:01", "88800001001:02"]
    assert _queue(snapshots, start, end, "CT-02") == [
        "77700001001:01",
        "10840402001:05",
        "10840401003:03",
    ]
    transfer = payload["transfer"]
    assert transfer["order_number"] == "108404"
    assert transfer["operation_count"] == 1
    assert transfer["scope"] == "conjunto_at_center"
    assert "CT-01A" in transfer["message"]
    # A OP do conjunto que já estava no CT-02 permanece sem marca de transferência.
    kept = next(
        item
        for item in payload["selected"]["items"]
        if item["production_order"] == "10840402001"
    )
    assert "transferred_from" not in kept


def test_transfer_operation_updates_center_name_and_counts() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    payload = _transfer(service, start, end, work_center="CT-02")

    moved = next(
        item
        for item in payload["selected"]["items"]
        if item["production_order"] == "10840401003"
    )
    assert moved["work_center"] == "CT-02"
    assert moved["work_center_name"] == "APLICAÇÃO DE TERMINAIS"
    assert moved["transferred_from"] == "CT-01A"
    counts = {item["work_center"]: item["operation_count"] for item in payload["work_centers"]}
    assert counts == {"CT-01A": 2, "CT-02": 3}


def test_transfer_operation_back_to_origin_clears_the_mark() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _transfer(service, start, end)

    payload = _transfer(service, start, end, target="CT-01A", work_center="CT-01A")

    assert payload["transfer"]["returned_to_origin"] is True
    moved = next(
        item
        for item in payload["selected"]["items"]
        if item["production_order"] == "10840401003"
    )
    assert "transferred_from" not in moved
    assert snapshots.rows["01"]["payload_json"]["transferred_operations"] == []


def test_transfer_operation_rejects_invalid_requests() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)

    with pytest.raises(ValueError, match="CT-99"):
        _transfer(service, start, end, target="CT-99")
    with pytest.raises(ValueError, match="CT-01A"):
        _transfer(service, start, end, target="CT-01A")
    with pytest.raises(ValueError, match="12345678901"):
        _transfer(service, start, end, production_order="12345678901")
    with pytest.raises(ValueError):
        _transfer(service, start, end, target="  ")
    with pytest.raises((PermissionError, BranchAccessDenied)):
        service.transfer_operation(
            _user("production-control.access"),
            branch="01",
            production_order="10840401003",
            operation_code="03",
            target_work_center="CT-02",
        )


def test_transfer_operation_of_withdrawn_conjunto_is_rejected() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_priority_snapshot(snapshots)
    _withdraw(service, start, end)

    with pytest.raises(ValueError, match="10840401003"):
        _transfer(service, start, end)


def test_transfer_operation_without_snapshot_is_not_found() -> None:
    with pytest.raises(SnapshotNotFound):
        _service(FakeGateway(), FakeSnapshotRepo()).transfer_operation(
            _user(*FULL_PERMS),
            branch="01",
            production_order="10840401003",
            operation_code="03",
            target_work_center="CT-02",
        )


def test_transfer_operation_notifies_connected_cockpits() -> None:
    snapshots = FakeSnapshotRepo()
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), snapshots, notifier)
    start, end = _seed_priority_snapshot(snapshots)
    snapshots.publish("01")

    _transfer(service, start, end)

    assert notifier.events == [
        {"branch": "01", "reason": "transfer", "work_center": "CT-02"}
    ]


def test_refresh_replays_transfers_over_the_new_queue() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = service.resolve_delivery_window(start_date=None, end_date=None)
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [
                {**_OPERATION, "work_center": center["work_center"]} for center in _WORK_CENTERS
            ],
            "summary": {"work_center_count": 2, "operation_count": 2},
        },
        refreshed_by="planner-1",
    )
    service.transfer_operation(
        _user(*FULL_PERMS),
        branch="01",
        production_order="24640401002",
        operation_code="03",
        target_work_center="CT-02",
        work_center="CT-01A",
    )

    payload = service.refresh(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
    )

    # O TOTVS devolve a OP no CT-01A; o replay a leva de volta ao CT-02.
    assert payload["selected"]["items"] == []
    stored = snapshots.rows["01"]["payload_json"]
    assert [item["work_center"] for item in stored["operations"]] == ["CT-02", "CT-02"]
    assert len(stored["transferred_operations"]) == 1


def _seed_withdrawal_public_snapshot(
    service: MachineLoadService,
    snapshots: FakeSnapshotRepo,
) -> tuple[date, date]:
    """Janela padrão com o conjunto 246404 — o mesmo que o FakeGateway devolve no refresh."""
    start, end = service.resolve_delivery_window(start_date=None, end_date=None)
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [
                {**_OPERATION, "work_center": center["work_center"], "pa_product_code": "90262910"}
                for center in _WORK_CENTERS
            ],
            "summary": {"work_center_count": 2, "operation_count": 2},
        },
        refreshed_by="planner-1",
    )
    snapshots.publish("01")
    return start, end


def test_refresh_keeps_conjunto_out_of_the_schedule() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_withdrawal_public_snapshot(service, snapshots)
    service.withdraw_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="246404",
    )

    payload = service.refresh(
        _user(*FULL_PERMS),
        branch="01",
    )

    assert payload["withdrawn"]["conjunto_count"] == 1
    assert payload["selected"]["items"] == []
    assert payload["summary"]["operation_count"] == 0


def test_public_cockpit_sees_withdrawn_queue_when_live() -> None:
    """LIVE: withdraw já propaga para o PUBLISHED na mesma transação (E4)."""
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    start, end = _seed_withdrawal_public_snapshot(service, snapshots)
    service.withdraw_conjunto(
        _user(*FULL_PERMS),
        branch="01",
        order_number="246404",
    )

    public_payload = service.build_public(branch="01", work_center="CT-02")

    assert public_payload["selected"]["items"] == []
    assert service.public_snapshot_contains_pa(branch="01", pa_code="90262910") is False


def _machine_load_client(service: MachineLoadService) -> TestClient:
    """App mínimo com o router real — valida o contrato HTTP, não só o service."""
    from production_control_app.interface.http.routes import machine_load_routes

    machine_load_routes.build_machine_load_service = lambda: service  # type: ignore[assignment]
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = _user(*FULL_PERMS)
        return await call_next(request)

    app.include_router(machine_load_routes.router)
    return TestClient(app)


@pytest.fixture
def machine_load_routes_module():
    from production_control_app.interface.http.routes import machine_load_routes

    original = machine_load_routes.build_machine_load_service
    yield machine_load_routes
    machine_load_routes.build_machine_load_service = original  # type: ignore[assignment]


def test_include_all_centers_returns_the_whole_branch_queue(machine_load_routes_module) -> None:
    """Fila completa + recorte do CT pedido: o MFE troca de aba sem nova leitura."""
    service = _service(FakeGateway(), FakeSnapshotRepo())
    client = _machine_load_client(service)

    response = client.get(
        "/machine-load",
        params={"branch": "01", "workCenter": "CT-02", "includeAllCenters": "true"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    centers = {item["work_center"] for item in data["operations"]}
    assert centers == {"CT-01A", "CT-02"}
    assert data["selected"]["work_center"] == "CT-02"
    assert {item["work_center"] for item in data["selected"]["items"]} == {"CT-02"}


def test_machine_load_without_opt_in_stays_lean(machine_load_routes_module) -> None:
    service = _service(FakeGateway(), FakeSnapshotRepo())
    client = _machine_load_client(service)

    data = client.get("/machine-load", params={"branch": "01"}).json()["data"]

    assert "operations" not in data
    assert data["selected"]["items"]


def test_mutation_returns_the_queue_so_the_client_cache_stays_whole(
    machine_load_routes_module,
) -> None:
    """Depois de reordenar, o MFE precisa da fila inteira — não só do CT ativo."""
    service = _service(FakeGateway(), FakeSnapshotRepo())
    client = _machine_load_client(service)
    client.get("/machine-load", params={"branch": "01"})

    response = client.post(
        "/machine-load/optimize-delivery",
        params={"branch": "01", "workCenter": "CT-02", "includeAllCenters": "true"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert {item["work_center"] for item in data["operations"]} == {"CT-01A", "CT-02"}
    assert data["selected"]["work_center"] == "CT-02"


def test_live_status_route_answers_404_without_snapshot(machine_load_routes_module) -> None:
    gateway = FakeGateway()
    gateway.status_by_key[("24640401002", "03")] = {
        "production_status": "in_progress",
        "is_in_production": True,
    }
    service = _service(gateway, FakeSnapshotRepo())
    client = _machine_load_client(service)

    missing = client.get("/machine-load/live-status", params={"branch": "01"})
    assert missing.status_code == 404

    client.get("/machine-load", params={"branch": "01"})
    live = client.get("/machine-load/live-status", params={"branch": "01"})
    assert live.status_code == 200
    body = live.json()["data"]
    assert body["as_of"]
    assert body["items"][0]["is_in_production"] is True
    assert body["summary"]["in_production_count"] == 2


def test_public_cockpit_never_receives_the_whole_queue() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    snapshots.publish("01")

    public_payload = service.build_public(branch="01", work_center="CT-02")

    assert "operations" not in public_payload
    assert public_payload["selected"]["items"]


def test_live_status_omits_operations_that_match_the_frozen_queue() -> None:
    """Polling a cada 30 s não repete as ~1780 operações sem novidade."""
    gateway = FakeGateway()
    service = _service(gateway, FakeSnapshotRepo())
    service.build(_user(*FULL_PERMS), branch="01")

    live = service.live_status(_user(*FULL_PERMS), branch="01")

    # O TOTVS responde por todas as chaves, mas nenhuma diverge do snapshot.
    assert live["items"] == []
    assert live["summary"]["operation_count"] == 2
    assert live["summary"]["in_production_count"] == 0


def _snapshots_with_run_target_operation() -> FakeSnapshotRepo:
    snapshots = FakeSnapshotRepo()
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload={
            "work_centers": [
                {
                    "work_center": "CT-35",
                    "work_center_name": "MONTAGEM",
                    "operation_count": 1,
                    "in_production_count": 0,
                }
            ],
            "operations": [
                {
                    "work_center": "CT-35",
                    "production_order": "24822601002",
                    "operation_code": "02",
                    "planned_qty": 0.5,
                    "pending_qty": 0.5,
                    "unit": "MI",
                    "pieces_conversion_factor": 1000.0,
                }
            ],
            "summary": {"work_center_count": 1, "operation_count": 1},
        },
        refreshed_by="planner-1",
    )
    snapshots.publish("01")
    return snapshots


def test_public_operation_run_quantity_returns_pending_and_factor() -> None:
    """O target do run usa saldo vivo + fator de peças da fila publicada."""
    gateway = FakeGateway()
    gateway.status_by_key[("24822601002", "02")] = {
        "production_status": "in_progress",
        "is_in_production": True,
        "operation_produced_qty": 0.1,
        "operation_pending_qty": 0.4,
    }
    service = _service(gateway, _snapshots_with_run_target_operation())

    result = service.public_operation_run_quantity(
        branch="01",
        production_order="24822601002",
        operation_code="02",
    )

    assert result == {
        "operation_pending_qty": 0.4,
        "pending_qty": 0.5,
        "operation_produced_qty": 0.1,
        "pieces_conversion_factor": 1000.0,
    }


def test_public_operation_run_quantity_returns_none_for_unknown_operation() -> None:
    service = _service(FakeGateway(), _snapshots_with_run_target_operation())

    result = service.public_operation_run_quantity(
        branch="01",
        production_order="00000000000",
        operation_code="02",
    )

    assert result is None


def _scoped_op(order: str, work_center: str) -> dict[str, Any]:
    return {
        **_OPERATION,
        "work_center": work_center,
        "production_order": order,
        "operation_code": "010",
        "pending_qty": 5.0,
    }


def _appointment_calls(gateway: FakeGateway) -> list[int]:
    return [
        call[1]["count"] for call in gateway.calls if call[0] == "appointment_status"
    ]


def test_public_enrich_scopes_to_requested_work_center() -> None:
    """F2: o cockpit enriquece só o CT pedido, não a filial inteira."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_scoped_op(f"A{i}", "CT-01A") for i in range(4)]
        + [_scoped_op(f"B{i}", "CT-02") for i in range(6)],
    )

    service.build_public(branch="01", work_center="CT-01A")

    assert _appointment_calls(gateway) == [4]


def test_public_enrich_scopes_to_the_other_work_center() -> None:
    """F2: CT-B recebe somente suas próprias operações no enrich."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_scoped_op(f"A{i}", "CT-01A") for i in range(4)]
        + [_scoped_op(f"B{i}", "CT-02") for i in range(6)],
    )

    payload = service.build_public(branch="01", work_center="CT-02")

    assert _appointment_calls(gateway) == [6]
    assert payload["selected"]["work_center"] == "CT-02"


def test_public_without_work_center_skips_remote_status() -> None:
    """F2: o seletor de postos usa o snapshot congelado — sem chão de fábrica."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_scoped_op(f"A{i}", "CT-01A") for i in range(4)]
        + [_scoped_op(f"B{i}", "CT-02") for i in range(6)],
    )

    payload = service.build_public(branch="01")

    assert _appointment_calls(gateway) == []
    assert [wc["work_center"] for wc in payload["work_centers"]] == [
        "CT-01A",
        "CT-02",
    ]


def test_public_unknown_work_center_skips_remote_status() -> None:
    """F2: CT inexistente não vira fallback de consulta da filial inteira."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service, snapshots, [_scoped_op(f"A{i}", "CT-01A") for i in range(4)]
    )

    payload = service.build_public(branch="01", work_center="CT-999")

    assert _appointment_calls(gateway) == []
    assert payload["selected"]["requested_work_center"] == "CT-999"
    assert payload["selected"]["work_center"] == "CT-01A"


def test_public_enrich_cache_is_scoped_per_work_center() -> None:
    """F2: o cache parcial de um CT nunca responde pelo mapa de outro CT."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_scoped_op(f"A{i}", "CT-01A") for i in range(4)]
        + [_scoped_op(f"B{i}", "CT-02") for i in range(6)],
    )

    service.build_public(branch="01", work_center="CT-01A")
    service.build_public(branch="01", work_center="CT-02")
    # Repetição do mesmo CT usa o cache do próprio escopo.
    service.build_public(branch="01", work_center="CT-01A")

    assert _appointment_calls(gateway) == [4, 6]


def test_public_enrich_cardinality_is_the_center_not_the_branch() -> None:
    """F2: prova estrutural — 1000 operações na filial, 10 no CT → 10 ao gateway."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_scoped_op(f"X{i}", "CT-01A") for i in range(990)]
        + [_scoped_op(f"T{i}", "CT-02") for i in range(10)],
    )

    service.build_public(branch="01", work_center="CT-02")

    assert _appointment_calls(gateway) == [10]


def test_public_scoped_enrich_keeps_open_only_and_order() -> None:
    """F1+F2: saldo vivo chega via enrich do CT e a fila sai open-only ordenada."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _scoped_op("KEEP-1", "CT-02"),
            _scoped_op("DONE", "CT-02"),
            _scoped_op("KEEP-2", "CT-02"),
            _scoped_op("OTHER-CT", "CT-01A"),
        ],
    )
    gateway.status_by_key[("DONE", "010")] = {"operation_pending_qty": 0.0}

    payload = service.build_public(branch="01", work_center="CT-02")

    assert _public_orders(payload) == ["KEEP-1", "KEEP-2"]
    assert payload["selected"]["pagination"]["total"] == 2


def _seed_granular_cache(
    branch: str, pairs: list[tuple[str, str]], status: dict[str, Any] | None = None
) -> None:
    from production_control_app.application.services.machine_load_live_status_cache import (
        put_live_status_many,
    )

    put_live_status_many(
        branch, {pair: dict(status or {"production_status": "started"}) for pair in pairs}
    )


def test_public_enrich_partial_hit_fetches_only_misses() -> None:
    """F3: 7 quentes no cache → gateway recebe só as 3 frias, em lote."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service, snapshots, [_scoped_op(f"K{i}", "CT-02") for i in range(10)]
    )
    _seed_granular_cache("01", [(f"K{i}", "010") for i in range(7)])

    service.build_public(branch="01", work_center="CT-02")

    assert _appointment_calls(gateway) == [3]


def test_public_enrich_cross_center_reuses_operation_hits() -> None:
    """F3: OP compartilhada entre CTs não é reconsultada — cache não depende de CT."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [
            _scoped_op("OP1", "CT-01A"),
            _scoped_op("OP2", "CT-01A"),
            _scoped_op("SHARED", "CT-01A"),
            _scoped_op("SHARED", "CT-02"),
            _scoped_op("OP4", "CT-02"),
        ],
    )

    service.build_public(branch="01", work_center="CT-01A")
    service.build_public(branch="01", work_center="CT-02")

    assert _appointment_calls(gateway) == [3, 1]


def test_public_enrich_second_read_within_ttl_is_pure_cache() -> None:
    """F3: releitura dentro do TTL não toca a api-delpi."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service, snapshots, [_scoped_op(f"K{i}", "CT-02") for i in range(10)]
    )

    service.build_public(branch="01", work_center="CT-02")
    service.build_public(branch="01", work_center="CT-02")
    service.build_public(branch="01", work_center="CT-02")

    assert _appointment_calls(gateway) == [10]


def test_public_enrich_invalidate_operation_fetches_only_it() -> None:
    """F3: invalidação cirúrgica — só a OP alvo volta para o remote."""
    from production_control_app.application.services.machine_load_live_status_cache import (
        invalidate_live_status_operation,
    )

    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service, snapshots, [_scoped_op(f"K{i}", "CT-02") for i in range(10)]
    )

    service.build_public(branch="01", work_center="CT-02")
    invalidate_live_status_operation("01", "K4", "010")
    service.build_public(branch="01", work_center="CT-02")

    assert _appointment_calls(gateway) == [10, 1]


def test_public_enrich_partial_remote_response_never_invents_status() -> None:
    """F3: resposta parcial cacheia só o que voltou — ausente segue desconhecido."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service,
        snapshots,
        [_scoped_op("MISSING", "CT-02"), _scoped_op("ANSWERED", "CT-02")],
    )
    original = gateway.fetch_machine_load_appointment_status
    requested: list[int] = []

    def partial_fetch(*, branch, items):
        requested.append(len(items))
        kept = [
            item for item in items if item["production_order"] != "MISSING"
        ]
        return original(branch=branch, items=kept)

    gateway.fetch_machine_load_appointment_status = partial_fetch  # type: ignore[method-assign]

    payload = service.build_public(branch="01", work_center="CT-02")
    # Segunda leitura: ANSWERED sai do cache, MISSING é reconsultada de novo.
    service.build_public(branch="01", work_center="CT-02")

    assert len(payload["selected"]["items"]) == 2  # desconhecida permanece (F1)
    assert requested == [2, 1]


def test_public_enrich_remote_failure_keeps_cache_hits() -> None:
    """F3: gateway falhando não apaga hits nem derruba o cockpit."""
    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_public_balance_snapshot(
        service, snapshots, [_scoped_op(f"K{i}", "CT-02") for i in range(10)]
    )
    _seed_granular_cache(
        "01",
        [(f"K{i}", "010") for i in range(7)],
        {"production_status": "in_progress", "operation_pending_qty": 3.0},
    )

    def boom(*, branch, items):
        raise RuntimeError("api-delpi fora do ar")

    gateway.fetch_machine_load_appointment_status = boom  # type: ignore[method-assign]

    payload = service.build_public(branch="01", work_center="CT-02")

    enriched = [
        i for i in payload["selected"]["items"] if i["production_order"] == "K0"
    ]
    # Saldo vivo do hit aplicado mesmo com remote fora; «em produção» é domínio
    # do run MES, não do cache HZA — por isso prova-se pelo saldo.
    assert enriched[0]["operation_pending_qty"] == 3.0
    assert _appointment_calls(gateway) == []


def test_refresh_clears_only_that_branch_live_status_cache() -> None:
    """F3: novo snapshot invalida a filial inteira; a vizinha permanece quente."""
    from production_control_app.application.services.machine_load_live_status_cache import (
        get_live_status_many,
    )

    snapshots = FakeSnapshotRepo()
    gateway = FakeGateway()
    service = _service(gateway, snapshots)
    _seed_granular_cache("01", [("A", "010")])
    _seed_granular_cache("02", [("B", "010")])

    service.refresh(_user(*FULL_PERMS), branch="01")

    assert get_live_status_many("01", [("A", "010")])[1] == {("A", "010")}
    assert ("B", "010") in get_live_status_many("02", [("B", "010")])[0]


def _cockpit_run(
    *, order: str, operation: str, work_center: str = "CT-01A", **over: Any
) -> dict[str, Any]:
    """Item na projeção open_run_items do cockpit-status."""
    return {
        "run_id": f"run-{order}-{operation}",
        "work_center": work_center,
        "production_order": order,
        "operation_code": operation,
        "run_status": "running",
        "operational_state": "producing",
        "display_status": "producing",
        "integrity_status": "complete",
        "started_at": "2026-08-19T07:30:00Z",
        **over,
    }


def test_operation_balances_returns_queue_scoped_items() -> None:
    """Lote SH6/SC2 só das operações visíveis da fila — sem HZA."""
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    gateway = FakeGateway()
    gateway.balances_by_key = {
        ("10840401003", "01"): {
            "operation_produced_qty": 4.0,
            "operation_pending_qty": 0.0,
        },
        ("10840401003", "03"): {
            "operation_produced_qty": 1.5,
            "operation_pending_qty": 2.5,
        },
    }

    payload = _service(gateway, snapshots).operation_balances(
        _user(*FULL_PERMS), branch="01"
    )

    assert payload["branch"] == "01"
    assert payload["summary"]["item_count"] == 2
    keys = [
        (item["production_order"], item["operation_code"])
        for item in payload["items"]
    ]
    assert keys == [("10840401003", "01"), ("10840401003", "03")]
    assert payload["items"][0]["operation_pending_qty"] == 0.0
    batch_calls = [call for call in gateway.calls if call[0] == "operation_balances"]
    assert len(batch_calls) == 1
    # Nenhuma consulta HZA de apontamento participou da leitura de saldos.
    assert not [call for call in gateway.calls if call[0] == "appointment_status"]


def test_operation_balances_gateway_failure_surfaces_as_error() -> None:
    """No endpoint dedicado, silêncio não pode passar por «sem saldo».

    O MFE trata o erro como indisponibilidade e mantém o último saldo
    conhecido na tela — diferente do mapa tolerante do rastreio.
    """
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    gateway = FakeGateway()

    def boom(**kwargs: Any) -> dict[str, Any]:
        raise DelpiGatewayError("api-delpi indisponível")

    gateway.fetch_machine_load_operation_balances = boom  # type: ignore[method-assign]

    with pytest.raises(DelpiGatewayError):
        _service(gateway, snapshots).operation_balances(
            _user(*FULL_PERMS), branch="01"
        )


def test_locate_stop_execution_comes_from_cockpit_runs() -> None:
    """Stopped do cockpit; op sem run = None mesmo com HZA congelada."""
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _cockpit_run(
                order="10840401003",
                operation="01",
                operational_state="stopped",
                display_status="stopped",
            )
        ],
    )

    payload = service.locate(_user(*FULL_PERMS), branch="01", query="10840401003")

    stops = payload["journeys"][0]["stops"]
    by_key = {
        (stop["production_order"], stop["operation_code"]): stop for stop in stops
    }
    run_stop = by_key[("10840401003", "01")]
    assert run_stop["work_center"] == "CT-01A"
    assert run_stop["execution_status"] == "stopped"
    assert run_stop["execution_integrity_status"] == "complete"
    assert run_stop["execution_started_at"] == "2026-08-19T07:30:00Z"
    # OP "started" no snapshot congelado mas sem run: ausência nunca produz.
    assert by_key[("10840401003", "03")]["execution_status"] is None
    assert by_key[("10840402001", "01")]["execution_status"] is None


def test_locate_stop_execution_unknown_when_cockpit_read_fails() -> None:
    """Fonte do cockpit fora do ar = «não confirmado», nunca falso ausente."""
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)

    def failing_runs(**kwargs: Any) -> list[dict[str, Any]]:
        raise PluginsDatabaseConnectionError("postgres fora")

    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=failing_runs,
    )

    payload = service.locate(_user(*FULL_PERMS), branch="01", query="10840401003")

    for stop in payload["journeys"][0]["stops"]:
        assert stop["execution_status"] == "unknown"
        assert stop["execution_integrity_status"] == "inconsistent"


def test_locate_stops_apply_batch_balance_without_hza() -> None:
    """Saldo SH6/SC2 chega pelo lote; apontamento HZA não é consultado."""
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    gateway = FakeGateway()
    gateway.balances_by_key = {
        ("10840401003", "01"): {
            "operation_produced_qty": 4.0,
            "operation_pending_qty": 0.0,
        },
    }

    payload = _service(gateway, snapshots).locate(
        _user(*FULL_PERMS), branch="01", query="10840401003"
    )

    stops = payload["journeys"][0]["stops"]
    done = next(
        s
        for s in stops
        if s["work_center"] == "CT-01A" and s["operation_code"] == "01"
    )
    assert done["operation_pending_qty"] == 0.0
    assert not [call for call in gateway.calls if call[0] == "appointment_status"]


def test_locate_survives_balance_batch_failure() -> None:
    """Rastreio tolerante: saldo falha, execução do cockpit continua."""
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    gateway = FakeGateway()

    def boom(**kwargs: Any) -> dict[str, Any]:
        raise DelpiGatewayError("api-delpi fora")

    gateway.fetch_machine_load_operation_balances = boom  # type: ignore[method-assign]
    service = _service(
        gateway,
        snapshots,
        open_runs=[_cockpit_run(order="10840401003", operation="01")],
    )

    payload = service.locate(_user(*FULL_PERMS), branch="01", query="10840401003")

    stop = next(
        s
        for s in payload["journeys"][0]["stops"]
        if s["work_center"] == "CT-01A" and s["operation_code"] == "01"
    )
    assert stop["execution_status"] == "producing"
    # Saldo do snapshot permanece — desconhecido não zera nem esconde.
    assert stop["operation_pending_qty"] is None


def test_locate_stop_execution_does_not_cross_work_centers() -> None:
    """Run no CT-01A não produz na parada de mesmo OP+op do CT-02.

    Cenário de transferência: a parada de OP 10840401003 operação 03 está no
    CT-02; um run aberto para o mesmo par no CT-01A pertence à bancada de
    origem e não pode marcar a parada do CT-02 como produzindo.
    """
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _cockpit_run(
                order="10840401003",
                operation="03",
                work_center="CT-01A",
            )
        ],
    )

    payload = service.locate(_user(*FULL_PERMS), branch="01", query="10840401003")

    by_key = {
        (stop["work_center"], stop["production_order"], stop["operation_code"]): stop
        for stop in payload["journeys"][0]["stops"]
    }
    # Parada no CT-02: sem run correspondente nesse centro → sem execução.
    assert by_key[("CT-02", "10840401003", "03")]["execution_status"] is None
    # Parada irmã no CT-01A com mesmo OP mas outra operação também fica sem.
    assert by_key[("CT-01A", "10840401003", "01")]["execution_status"] is None


def test_locate_stop_execution_same_pair_two_centers() -> None:
    """Dois runs com estados distintos no mesmo par OP+op: cada CT recebe o seu."""
    snapshots = FakeSnapshotRepo()
    _seed_locate_snapshot(snapshots)
    # Ordem invertida de propósito — o resultado não pode depender dela.
    runs = [
        _cockpit_run(
            order="10840401003",
            operation="03",
            work_center="CT-02",
            run_status="stopped",
            operational_state="stopped",
            display_status="stopped",
        ),
        _cockpit_run(
            order="10840401003",
            operation="01",
            work_center="CT-01A",
        ),
    ]
    service = _service(FakeGateway(), snapshots, open_runs=runs)

    payload = service.locate(_user(*FULL_PERMS), branch="01", query="10840401003")

    by_key = {
        (stop["work_center"], stop["production_order"], stop["operation_code"]): stop
        for stop in payload["journeys"][0]["stops"]
    }
    assert by_key[("CT-01A", "10840401003", "01")]["execution_status"] == "producing"
    assert by_key[("CT-02", "10840401003", "03")]["execution_status"] == "stopped"

def _source_keys_ct01a() -> list[dict[str, str]]:
    return _ct01a_keys("A1", "A2", "A3")


# ============ E4 — Transferência coletiva ============


def test_transfer_operations_moves_only_selected_to_end_of_target() -> None:
    """B, E, G saem de CT-01A e entram no fim de CT-02, na ordem relativa."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    payload = service.transfer_operations(
        _user(*FULL_PERMS),
        branch="01",
        source_work_center="CT-01A",
        target_work_center="CT-02",
        operations=[
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A3", "operation_code": "01"},
        ],
        expected_keys=_source_keys_ct01a(),
    )

    ops = snapshots.get(branch="01")["payload_json"]["operations"]
    ct01a = [o["production_order"] for o in ops if o["work_center"] == "CT-01A"]
    ct02 = [o["production_order"] for o in ops if o["work_center"] == "CT-02"]
    assert ct01a == ["A2"]
    assert ct02 == ["B1", "B2", "A1", "A3"]
    assert payload["transfer"]["operation_count"] == 2
    assert snapshots.payload_updates == 1


def test_transfer_operations_rejects_stale_expected_keys() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(MachineLoadSequenceConflict):
        service.transfer_operations(
            _user(*FULL_PERMS),
            branch="01",
            source_work_center="CT-01A",
            target_work_center="CT-02",
            operations=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=_ct01a_keys("A2", "A1", "A3"),
        )
    assert snapshots.payload_updates == 0


def test_transfer_operations_rejects_missing_and_ambiguous() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(ValueError, match="CT-01A"):
        service.transfer_operations(
            _user(*FULL_PERMS),
            branch="01",
            source_work_center="CT-01A",
            target_work_center="CT-02",
            operations=[{"production_order": "B1", "operation_code": "03"}],
            expected_keys=_source_keys_ct01a(),
        )
    assert snapshots.payload_updates == 0


def test_transfer_operations_rejects_same_center_and_unknown_target() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)
    user = _user(*FULL_PERMS)

    with pytest.raises(ValueError, match="mesmo centro|já está"):
        service.transfer_operations(
            user, branch="01", source_work_center="CT-01A",
            target_work_center="CT-01A",
            operations=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=_source_keys_ct01a(),
        )
    with pytest.raises(ValueError, match="não existe"):
        service.transfer_operations(
            user, branch="01", source_work_center="CT-01A",
            target_work_center="CT-99",
            operations=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=_source_keys_ct01a(),
        )
    assert snapshots.payload_updates == 0


def test_transfer_operations_rejects_protected_run() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(
                work_center="CT-01A", production_order="A3", operation_code="01"
            )
        ],
    )

    with pytest.raises(MachineLoadSequenceConflict, match="execução"):
        service.transfer_operations(
            _user(*FULL_PERMS),
            branch="01",
            source_work_center="CT-01A",
            target_work_center="CT-02",
            operations=[
                {"production_order": "A1", "operation_code": "01"},
                {"production_order": "A3", "operation_code": "01"},
            ],
            expected_keys=_source_keys_ct01a(),
        )
    assert snapshots.payload_updates == 0


def test_transfer_operations_fail_closed_when_runs_source_fails() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("runs down")
        ),
    )

    with pytest.raises(RuntimeError, match="runs down"):
        service.transfer_operations(
            _user(*FULL_PERMS),
            branch="01",
            source_work_center="CT-01A",
            target_work_center="CT-02",
            operations=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=_source_keys_ct01a(),
        )
    assert snapshots.payload_updates == 0


def test_transfer_operations_duplicate_order_in_two_centers_moves_only_source() -> None:
    """Mesma OP+op em dois CTs: só a instância do CT de origem se move."""
    snapshots = FakeSnapshotRepo()
    ops = [
        {**_OPERATION, "work_center": "CT-01A", "production_order": "X1", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "X1", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-02", "production_order": "B2", "operation_code": "03"},
    ]
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 8, 26),
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 3},
        },
        refreshed_by="seed",
    )
    service = _service(FakeGateway(), snapshots)

    service.transfer_operations(
        _user(*FULL_PERMS),
        branch="01",
        source_work_center="CT-01A",
        target_work_center="CT-02",
        operations=[{"production_order": "X1", "operation_code": "01"}],
        expected_keys=[{"production_order": "X1", "operation_code": "01"}],
    )

    ops = snapshots.get(branch="01")["payload_json"]["operations"]
    ct01a = [o["production_order"] for o in ops if o["work_center"] == "CT-01A"]
    x1_in_ct02 = [
        o for o in ops if o["work_center"] == "CT-02" and o["production_order"] == "X1"
    ]
    assert ct01a == []
    assert len(x1_in_ct02) == 2  # a instância transferida + a que já estava


def test_transfer_operations_replay_after_refresh_uses_erp_origin() -> None:
    """A → B → C: refresh reaplica só a última posição, casando pela origem ERP."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)
    user = _user(*FULL_PERMS)

    service.transfer_operations(
        user, branch="01", source_work_center="CT-01A", target_work_center="CT-02",
        operations=[{"production_order": "A1", "operation_code": "01"}],
        expected_keys=_source_keys_ct01a(),
    )
    service.transfer_operations(
        user, branch="01", source_work_center="CT-02", target_work_center="CT-01A",
        operations=[{"production_order": "A1", "operation_code": "01"}],
        expected_keys=[
            {"production_order": "B1", "operation_code": "03"},
            {"production_order": "B2", "operation_code": "03"},
            {"production_order": "A1", "operation_code": "01"},
        ],
    )
    entries = snapshots.get(branch="01")["payload_json"]["transferred_operations"]
    assert entries == []  # voltou à origem ERP — nada a reaplicar


def test_transfer_operations_requires_permission() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises((PermissionError, BranchAccessDenied)):
        service.transfer_operations(
            _user("production-control.access"),
            branch="01",
            source_work_center="CT-01A",
            target_work_center="CT-02",
            operations=[{"production_order": "A1", "operation_code": "01"}],
            expected_keys=_source_keys_ct01a(),
        )


def test_transfer_operations_http_returns_409_on_stale(
    machine_load_routes_module,
) -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    client = _machine_load_client(_service(FakeGateway(), snapshots))

    response = client.post(
        "/machine-load/transfer-operations",
        params={"branch": "01", "workCenter": "CT-01A"},
        json={
            "source_work_center": "CT-01A",
            "target_work_center": "CT-02",
            "operations": [{"production_order": "A1", "operation_code": "01"}],
            "expected_keys": _ct01a_keys("A9", "A1", "A2"),
        },
    )
    assert response.status_code == 409
    assert snapshots.payload_updates == 0


# ============ E4 — Retirada/restauração por operação ============


def test_withdraw_operations_hides_only_selected_ops() -> None:
    """Retirar A1 e A3 esconde só elas — A2 continua; conjunto não é afetado."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    payload = service.withdraw_operations(
        _user(*FULL_PERMS),
        branch="01",
        operations=[
            {
                "work_center": "CT-01A",
                "production_order": "A1",
                "operation_code": "01",
            },
            {
                "work_center": "CT-01A",
                "production_order": "A3",
                "operation_code": "01",
            },
        ],
        expected_keys=_source_keys_ct01a(),
        work_center="CT-01A",
    )

    stored = snapshots.get(branch="01")["payload_json"]
    entries = stored["withdrawn_operations"]
    assert len(entries) == 2
    visible = [
        o["production_order"]
        for o in payload["selected"]["items"]
    ]
    assert visible == ["A2"]
    assert payload["withdrawal"]["operation_count"] == 2
    # Operação retirada continua no snapshot (restaurável).
    all_ops = [o["production_order"] for o in stored["operations"]]
    assert "A1" in all_ops and "A3" in all_ops


def test_withdraw_operations_rejects_stale_expected_keys() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(MachineLoadSequenceConflict):
        service.withdraw_operations(
            _user(*FULL_PERMS),
            branch="01",
            operations=[
                {
                    "work_center": "CT-01A",
                    "production_order": "A1",
                    "operation_code": "01",
                }
            ],
            expected_keys=_ct01a_keys("A3", "A2", "A1"),
        )
    assert snapshots.payload_updates == 0


def test_withdraw_operations_rejects_protected_run() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(
        FakeGateway(),
        snapshots,
        open_runs=[
            _run_item(
                work_center="CT-01A", production_order="A2", operation_code="01"
            )
        ],
    )

    with pytest.raises(MachineLoadSequenceConflict, match="execução"):
        service.withdraw_operations(
            _user(*FULL_PERMS),
            branch="01",
            operations=[
                {
                    "work_center": "CT-01A",
                    "production_order": "A1",
                    "operation_code": "01",
                },
                {
                    "work_center": "CT-01A",
                    "production_order": "A2",
                    "operation_code": "01",
                },
            ],
            expected_keys=_source_keys_ct01a(),
        )
    assert snapshots.payload_updates == 0


def test_withdraw_operations_all_or_nothing() -> None:
    """Um item inválido rejeita o lote inteiro — nada é marcado."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(ValueError, match="A9"):
        service.withdraw_operations(
            _user(*FULL_PERMS),
            branch="01",
            operations=[
                {
                    "work_center": "CT-01A",
                    "production_order": "A1",
                    "operation_code": "01",
                },
                {
                    "work_center": "CT-01A",
                    "production_order": "A9",
                    "operation_code": "01",
                },
            ],
            expected_keys=_source_keys_ct01a(),
        )
    row = snapshots.get(branch="01")
    assert "withdrawn_operations" not in row["payload_json"]
    assert snapshots.payload_updates == 0


def test_withdraw_operations_keeps_conjunto_siblings_visible() -> None:
    """Retirar uma OP não retira as irmãs do mesmo C2_NUM."""
    snapshots = FakeSnapshotRepo()
    ops = [
        {**_OPERATION, "work_center": "CT-01A", "production_order": "10840401", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "10840402", "operation_code": "01"},
    ]
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 8, 26),
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 2},
        },
        refreshed_by="seed",
    )
    service = _service(FakeGateway(), snapshots)
    service.withdraw_operations(
        _user(*FULL_PERMS),
        branch="01",
        operations=[
            {
                "work_center": "CT-01A",
                "production_order": "10840401",
                "operation_code": "01",
            }
        ],
        expected_keys=[
            {"production_order": "10840401", "operation_code": "01"},
            {"production_order": "10840402", "operation_code": "01"},
        ],
    )
    presented = service.build(
        _user(*FULL_PERMS), branch="01", work_center="CT-01A"
    )
    visible = [o["production_order"] for o in presented["selected"]["items"]]
    assert visible == ["10840402"]


def test_restore_operations_brings_back_only_marked() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)
    user = _user(*FULL_PERMS)
    refs = [
        {"work_center": "CT-01A", "production_order": "A1", "operation_code": "01"},
        {"work_center": "CT-01A", "production_order": "A3", "operation_code": "01"},
    ]
    service.withdraw_operations(
        user, branch="01", operations=refs, expected_keys=_source_keys_ct01a()
    )
    payload = service.restore_operations(
        user, branch="01", operations=[refs[0]], work_center="CT-01A"
    )
    presented = service.build(user, branch="01", work_center="CT-01A")
    visible = [o["production_order"] for o in presented["selected"]["items"]]
    assert visible == ["A1", "A2"]
    assert payload["withdrawal"]["action"] == "restored"


def test_restore_operations_rejects_not_withdrawn() -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)

    with pytest.raises(ValueError, match="não está retirada"):
        service.restore_operations(
            _user(*FULL_PERMS),
            branch="01",
            operations=[
                {
                    "work_center": "CT-01A",
                    "production_order": "A1",
                    "operation_code": "01",
                }
            ],
        )
    assert snapshots.payload_updates == 0


def test_operation_withdrawn_stays_hidden_when_conjunto_also_withdrawn() -> None:
    """Marcas se somam: restaurar a operação não revela o que o conjunto esconde."""
    snapshots = FakeSnapshotRepo()
    ops = [
        {**_OPERATION, "work_center": "CT-01A", "production_order": "10840401", "operation_code": "01"},
        {**_OPERATION, "work_center": "CT-01A", "production_order": "10840402", "operation_code": "01"},
    ]
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 8, 26),
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": ops,
            "summary": {"work_center_count": 2, "operation_count": 2},
        },
        refreshed_by="seed",
    )
    service = _service(FakeGateway(), snapshots)
    user = _user(*FULL_PERMS)
    ref = {
        "work_center": "CT-01A",
        "production_order": "10840401",
        "operation_code": "01",
    }
    service.withdraw_operations(
        user, branch="01", operations=[ref],
        expected_keys=[
            {"production_order": "10840401", "operation_code": "01"},
            {"production_order": "10840402", "operation_code": "01"},
        ],
    )
    service.withdraw_conjunto(user, branch="01", order_number="108404")
    service.restore_operations(user, branch="01", operations=[ref])
    presented = service.build(user, branch="01", work_center="CT-01A")
    assert presented["selected"]["items"] == []  # conjunto retirado ainda esconde


def test_withdraw_operations_survives_refresh() -> None:
    """Refresh do TOTVS reaplica withdrawn_operations sobre a fila nova."""
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    service = _service(FakeGateway(), snapshots)
    user = _user(*FULL_PERMS)
    ref = {
        "work_center": "CT-01A",
        "production_order": "A1",
        "operation_code": "01",
    }
    service.withdraw_operations(
        user, branch="01", operations=[ref], expected_keys=_source_keys_ct01a()
    )

    # Simula refresh: nova fila do TOTVS + replay das marcas.
    service2 = _service(FakeGateway(), snapshots)
    service2._fetch_frozen_payload = lambda **kwargs: {  # noqa: SLF001
        "work_centers": _WORK_CENTERS,
        "operations": [
            {**_OPERATION, "work_center": "CT-01A", "production_order": "A1", "operation_code": "01"},
            {**_OPERATION, "work_center": "CT-01A", "production_order": "A2", "operation_code": "01"},
            {**_OPERATION, "work_center": "CT-01A", "production_order": "A3", "operation_code": "01"},
            {**_OPERATION, "work_center": "CT-02", "production_order": "B1", "operation_code": "03"},
        ],
        "summary": {"work_center_count": 2, "operation_count": 4},
    }
    service2._pull_and_store(user, branch="01", start=None, end=date(2026, 8, 26))
    payload = snapshots.get(branch="01")["payload_json"]
    assert len(payload["withdrawn_operations"]) == 1
    presented = service2.build(user, branch="01", work_center="CT-01A")
    visible = [o["production_order"] for o in presented["selected"]["items"]]
    assert visible == ["A2", "A3"]


def test_withdraw_operations_http_409_and_422(machine_load_routes_module) -> None:
    snapshots = FakeSnapshotRepo()
    _seed_multi_center_snapshot(snapshots)
    client = _machine_load_client(_service(FakeGateway(), snapshots))

    stale = client.post(
        "/machine-load/withdraw-operations",
        params={"branch": "01"},
        json={
            "operations": [
                {
                    "work_center": "CT-01A",
                    "production_order": "A1",
                    "operation_code": "01",
                }
            ],
            "expected_keys": _ct01a_keys("A3", "A1", "A2"),
        },
    )
    assert stale.status_code == 409

    invalid = client.post(
        "/machine-load/withdraw-operations",
        params={"branch": "01"},
        json={"operations": [], "expected_keys": []},
    )
    assert invalid.status_code == 422
