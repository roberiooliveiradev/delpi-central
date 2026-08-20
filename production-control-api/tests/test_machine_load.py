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
from production_control_app.domain.services.current_month_period import forward_window_bounds

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
        scheduled_start: str,
        scheduled_end: str,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "work_centers",
                {
                    "branch": branch,
                    "scheduled_start": scheduled_start,
                    "scheduled_end": scheduled_end,
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
        scheduled_start: str,
        scheduled_end: str,
        work_center: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "operations",
                {
                    "branch": branch,
                    "scheduled_start": scheduled_start,
                    "scheduled_end": scheduled_end,
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
    def __init__(self) -> None:
        self.rows: dict[tuple[str, date, date], dict[str, Any]] = {}
        self.upserts = 0
        self.payload_updates = 0

    def get(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any] | None:
        return self.rows.get((branch, start_date, end_date))

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
        self.rows[(branch, start_date, end_date)] = row
        return row

    def update_payload(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        key = (branch, start_date, end_date)
        existing = self.rows.get(key)
        if existing is None:
            raise RuntimeError("Snapshot da carga máquina não encontrado para atualizar.")
        self.payload_updates += 1
        updated = {
            **existing,
            "payload_json": payload,
        }
        self.rows[key] = updated
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


def test_forward_window_defaults_to_seven_days_ahead() -> None:
    start, end = forward_window_bounds(
        timezone="America/Sao_Paulo", days=7, today=date(2026, 8, 19)
    )
    assert start.isoformat() == "2026-08-19"
    assert end.isoformat() == "2026-08-26"


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
    assert "appointment_status" in {name for name, _ in gateway.calls}


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


def test_explicit_period_is_forwarded_to_the_gateway() -> None:
    gateway = FakeGateway()
    _service(gateway).build(
        _user(*FULL_PERMS),
        branch="01",
        start_date="2026-08-24",
        end_date="2026-08-28",
    )
    call = next(params for name, params in gateway.calls if name == "work_centers")
    assert call["scheduled_start"] == "2026-08-24"
    assert call["scheduled_end"] == "2026-08-28"


def test_inverted_period_is_rejected() -> None:
    with pytest.raises(ValueError):
        _service(FakeGateway()).build(
            _user(*FULL_PERMS),
            branch="01",
            start_date="2026-08-28",
            end_date="2026-08-24",
        )


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
    refreshed_before = snapshots.get(branch="01", start_date=start, end_date=end)["refreshed_at"]
    service = _service(FakeGateway(), snapshots)

    payload = service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        ordered_keys=[
            {"production_order": "A3", "operation_code": "01"},
            {"production_order": "A1", "operation_code": "01"},
            {"production_order": "A2", "operation_code": "01"},
        ],
    )

    assert snapshots.payload_updates == 1
    assert snapshots.upserts == 1
    row = snapshots.get(branch="01", start_date=start, end_date=end)
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
            start_date=start.isoformat(),
            end_date=end.isoformat(),
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
            start_date=start.isoformat(),
            end_date=end.isoformat(),
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
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            ordered_keys=[{"production_order": "A1", "operation_code": "01"}],
        )


def test_reorder_sequence_without_snapshot_is_not_found() -> None:
    service = _service(FakeGateway(), FakeSnapshotRepo())
    with pytest.raises(SnapshotNotFound):
        service.reorder_sequence(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-01A",
            start_date="2026-08-19",
            end_date="2026-08-26",
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
    start, end = service.resolve_window(start_date=None, end_date=None)
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
        start_date=start.isoformat(),
        end_date=end.isoformat(),
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
        start_date=start.isoformat(),
        end_date=end.isoformat(),
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
    start, end = service.resolve_window(start_date=None, end_date=None)
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
