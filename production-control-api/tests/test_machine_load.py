from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_machine_load_drawing_service import (
    PublicMachineLoadDrawingService,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DrawingNotFound,
    InvalidBranch,
    SnapshotNotFound,
)
from production_control_app.domain.product_drawing_pdf import DrawingFile
from production_control_app.domain.services.branch_access_service import BranchAccessService
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

    def fetch_machine_load_work_centers(
        self,
        *,
        branch: str,
        delivery_start: str | None,
        delivery_end: str,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "work_centers",
                {
                    "branch": branch,
                    "delivery_start": delivery_start,
                    "delivery_end": delivery_end,
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


class FakeSnapshotRepo:
    """Uma fila viva por filial — igual ao Postgres depois da V003."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.upserts = 0
        self.payload_updates = 0

    def get(self, *, branch: str) -> dict[str, Any] | None:
        return self.rows.get(branch)

    def upsert(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
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
            "payload_json": payload,
            "schema_version": schema_version,
            "source": source,
            "refreshed_at": datetime(2026, 8, 19, 22, 0, tzinfo=timezone.utc),
            "refreshed_by": refreshed_by,
        }
        self.rows[branch] = row
        return row

    def update_payload(self, *, branch: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.rows.get(branch)
        if existing is None:
            raise RuntimeError("Snapshot da carga máquina não encontrado para atualizar.")
        self.payload_updates += 1
        updated = {
            **existing,
            "payload_json": payload,
        }
        self.rows[branch] = updated
        return updated


def _user(*permissions: str):
    return SimpleNamespace(is_superadmin=False, permissions=list(permissions), id="user-1")


FULL_PERMS = (
    "production-control.access",
    "production-control.machine-load.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _service(gateway: FakeGateway, snapshots: FakeSnapshotRepo | None = None) -> MachineLoadService:
    return MachineLoadService(
        gateway,
        snapshots=snapshots or FakeSnapshotRepo(),
        branch_access=BranchAccessService(),
    )


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


def test_switching_work_center_reuses_live_status_cache() -> None:
    from production_control_app.application.services.machine_load_live_status_cache import (
        clear_live_status_cache,
    )

    clear_live_status_cache()
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01", work_center="CT-01A")
    first_status_calls = sum(1 for name, _ in gateway.calls if name == "appointment_status")
    assert first_status_calls == 1
    gateway.calls.clear()

    payload = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    assert payload["selected"]["work_center"] == "CT-02"
    assert "appointment_status" not in {name for name, _ in gateway.calls}


def test_refresh_invalidates_live_status_cache() -> None:
    from production_control_app.application.services.machine_load_live_status_cache import (
        clear_live_status_cache,
    )

    clear_live_status_cache()
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
    payload = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")

    operation = payload["selected"]["items"][0]
    assert operation["is_in_production"] is True
    assert operation["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"
    assert payload["summary"]["in_production_count"] >= 1
    assert payload["work_centers"][1]["in_production_count"] == 1


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
        )


def test_reorder_sequence_without_snapshot_is_not_found() -> None:
    service = _service(FakeGateway(), FakeSnapshotRepo())
    with pytest.raises(SnapshotNotFound):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            ordered_keys=[{"production_order": "A1", "operation_code": "01"}],
        )


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
) -> MachineLoadService:
    return MachineLoadService(
        gateway,
        snapshots=snapshots,
        branch_access=BranchAccessService(),
        change_notifier=notifier,
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


def test_reorder_sequence_notifies_connected_cockpits() -> None:
    snapshots = FakeSnapshotRepo()
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), snapshots, notifier)
    start, end = _seed_multi_center_snapshot(snapshots)

    service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        ordered_keys=[
            {"production_order": "A3", "operation_code": "01"},
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A2", "operation_code": "01"},
        ],
    )

    assert notifier.events == [
        {"branch": "01", "reason": "sequence", "work_center": "CT-01A"}
    ]


def test_refresh_notifies_connected_cockpits() -> None:
    notifier = RecordingNotifier()
    service = _service_with_notifier(FakeGateway(), FakeSnapshotRepo(), notifier)

    service.refresh(_user(*FULL_PERMS), branch="01")

    assert notifier.events == [{"branch": "01", "reason": "refresh", "work_center": None}]


def test_failed_notification_does_not_break_the_write() -> None:
    snapshots = FakeSnapshotRepo()

    def exploding_notifier(**_kwargs: Any) -> None:
        raise RuntimeError("hub fora do ar")

    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        branch_access=BranchAccessService(),
        change_notifier=exploding_notifier,
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


def test_prioritize_conjunto_keeps_started_operation_ahead() -> None:
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
        "99900001001:01",
        "10840401003:03",
        "88800001001:02",
    ]
    assert payload["prioritization"]["kept_ahead_count"] == 1


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


def test_public_cockpit_does_not_see_withdrawn_conjunto() -> None:
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
    assert "withdrawn" not in public_payload
    assert service.public_snapshot_contains_pa(branch="01", pa_code="90262910") is False
