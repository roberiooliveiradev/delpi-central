from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.product_3d_model_service import Product3DModelService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_machine_load_product_model_service import (
    PublicMachineLoadProductModelService,
)
from production_control_app.domain.errors import Product3DModelNotFound
from production_control_app.domain.product_3d_model import Product3DModel
from production_control_app.domain.services.branch_access_service import BranchAccessService

_OPERATION = {
    "work_center": "CT-02",
    "scheduled_date": "2026-08-20",
    "production_order": "24640401002",
    "operation_code": "03",
    "product_code": "50320064",
    "product_description": "PI",
    "pa_product_code": "90262957",
    "planned_qty": 7.1,
    "pending_qty": 7.1,
    "production_status": "not_started",
    "is_in_production": False,
}

_GLB = b"glTF" + b"\x02\x00\x00\x00" + b"x" * 20


class FakeSnapshotRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}

    def get(self, *, branch: str) -> dict[str, Any] | None:
        return self.rows.get(branch)

    def upsert(self, **kwargs: Any) -> dict[str, Any]:
        row = {
            "id": "snap-1",
            "branch": kwargs["branch"],
            "start_date": kwargs["start_date"],
            "end_date": kwargs["end_date"],
            "payload_json": kwargs["payload"],
            "schema_version": 1,
            "source": "api-delpi",
            "refreshed_at": datetime(2026, 8, 19, 22, 0, tzinfo=timezone.utc),
            "refreshed_by": kwargs.get("refreshed_by"),
        }
        self.rows[kwargs["branch"]] = row
        return row

    def update_payload(self, *, branch: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.rows[branch]
        updated = {**existing, "payload_json": payload}
        self.rows[branch] = updated
        return updated


class FakeGateway:
    def fetch_machine_load_work_centers(self, **kwargs: Any) -> dict[str, Any]:
        return {"success": True, "data": {"items": [], "summary": {}}}

    def fetch_machine_load_operations(self, **kwargs: Any) -> dict[str, Any]:
        return {"success": True, "data": {"items": [], "summary": {}}}

    def fetch_machine_load_appointment_status(self, **kwargs: Any) -> dict[str, Any]:
        return {"success": True, "data": {"items": [], "summary": {}}}


class FakeRepo:
    def __init__(self) -> None:
        self.rows: dict[str, Product3DModel] = {}
        self.lookups = 0

    def get(self, *, product_code: str) -> Product3DModel | None:
        self.lookups += 1
        return self.rows.get(product_code)

    def list(self, *, search: str | None = None) -> list[Product3DModel]:
        return list(self.rows.values())

    def existing_codes(self, codes: set[str]) -> set[str]:
        wanted = {code.upper() for code in codes}
        return {code for code in self.rows if code in wanted}

    def upsert(self, model: Product3DModel) -> Product3DModel:
        self.rows[model.product_code] = model
        return model

    def delete(self, *, product_code: str) -> Product3DModel | None:
        return self.rows.pop(product_code, None)


class FakeStorage:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.files: dict[str, bytes] = {}

    def write_glb(self, *, product_code: str, payload: bytes) -> str:
        name = f"{product_code}.glb"
        path = self.tmp_path / name
        path.write_bytes(payload)
        self.files[name] = payload
        return name

    def resolve_glb(self, *, stored_filename: str) -> str:
        path = self.tmp_path / stored_filename
        if not path.is_file():
            raise Product3DModelNotFound("missing")
        return str(path)

    def delete_glb(self, *, stored_filename: str) -> None:
        path = self.tmp_path / stored_filename
        if path.exists():
            path.unlink()


def _machine_load(snapshots: FakeSnapshotRepo) -> MachineLoadService:
    return MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        branch_access=BranchAccessService(),
    )


def _seed_queue(
    machine_load: MachineLoadService,
    snapshots: FakeSnapshotRepo,
    operations: list[dict[str, Any]],
) -> None:
    start, end = machine_load.resolve_delivery_window(start_date=None, end_date=None)
    snapshots.upsert(
        branch="01",
        start_date=start,
        end_date=end,
        payload={
            "work_centers": [{"work_center": "CT-02", "work_center_name": "CT", "operation_count": 1}],
            "operations": operations,
            "summary": {"work_center_count": 1, "operation_count": len(operations)},
        },
        refreshed_by="planner-1",
    )


def _public_service(
    snapshots: FakeSnapshotRepo,
    repo: FakeRepo,
    storage: FakeStorage,
) -> PublicMachineLoadProductModelService:
    models = Product3DModelService(models=repo, storage=storage, max_bytes=1024)
    return PublicMachineLoadProductModelService(
        access=PublicCockpitAccessService(),
        machine_load=_machine_load(snapshots),
        models=models,
    )


def test_open_glb_when_pi_is_in_queue(tmp_path: Path) -> None:
    snapshots = FakeSnapshotRepo()
    repo = FakeRepo()
    storage = FakeStorage(tmp_path)
    machine_load = _machine_load(snapshots)
    _seed_queue(machine_load, snapshots, [{**_OPERATION}])
    models = Product3DModelService(models=repo, storage=storage, max_bytes=1024)
    models.upsert(
        SimpleNamespace(is_superadmin=True, permissions=[], email="pcp@delpi.local"),
        product_code="50320064",
        original_filename="pi.glb",
        payload=_GLB,
    )
    service = _public_service(snapshots, repo, storage)

    opened = service.open_glb(token="aberto", branch="01", product_code="50320064")

    assert opened.filename == "50320064.glb"
    assert opened.path.read_bytes() == _GLB


def test_open_glb_when_pa_is_the_operation_product(tmp_path: Path) -> None:
    snapshots = FakeSnapshotRepo()
    repo = FakeRepo()
    storage = FakeStorage(tmp_path)
    machine_load = _machine_load(snapshots)
    _seed_queue(
        machine_load,
        snapshots,
        [{**_OPERATION, "product_code": "90262957", "pa_product_code": "90262957"}],
    )
    models = Product3DModelService(models=repo, storage=storage, max_bytes=1024)
    models.upsert(
        SimpleNamespace(is_superadmin=True, permissions=[], email="pcp@delpi.local"),
        product_code="90262957",
        original_filename="pa.glb",
        payload=_GLB,
    )
    service = _public_service(snapshots, repo, storage)

    opened = service.open_glb(token="aberto", branch="01", product_code="90262957")
    assert opened.filename == "90262957.glb"


def test_open_glb_rejects_code_that_is_only_pa_not_op_product(tmp_path: Path) -> None:
    snapshots = FakeSnapshotRepo()
    repo = FakeRepo()
    storage = FakeStorage(tmp_path)
    machine_load = _machine_load(snapshots)
    _seed_queue(machine_load, snapshots, [{**_OPERATION}])
    models = Product3DModelService(models=repo, storage=storage, max_bytes=1024)
    models.upsert(
        SimpleNamespace(is_superadmin=True, permissions=[], email="pcp@delpi.local"),
        product_code="90262957",
        original_filename="pa.glb",
        payload=_GLB,
    )
    service = _public_service(snapshots, repo, storage)
    lookups_before = repo.lookups

    with pytest.raises(Product3DModelNotFound, match="não está na fila publicada"):
        service.open_glb(token="aberto", branch="01", product_code="90262957")

    assert repo.lookups == lookups_before


def test_open_glb_rejects_product_outside_queue_without_reading_storage(tmp_path: Path) -> None:
    snapshots = FakeSnapshotRepo()
    repo = FakeRepo()
    storage = FakeStorage(tmp_path)
    machine_load = _machine_load(snapshots)
    _seed_queue(machine_load, snapshots, [{**_OPERATION}])
    models = Product3DModelService(models=repo, storage=storage, max_bytes=1024)
    models.upsert(
        SimpleNamespace(is_superadmin=True, permissions=[], email="pcp@delpi.local"),
        product_code="11111111",
        original_filename="other.glb",
        payload=_GLB,
    )
    service = _public_service(snapshots, repo, storage)
    lookups_before = repo.lookups

    with pytest.raises(Product3DModelNotFound, match="não está na fila publicada"):
        service.open_glb(token="aberto", branch="01", product_code="11111111")

    assert repo.lookups == lookups_before


def test_annotate_public_queue_flags_items(tmp_path: Path) -> None:
    snapshots = FakeSnapshotRepo()
    repo = FakeRepo()
    storage = FakeStorage(tmp_path)
    models = Product3DModelService(models=repo, storage=storage, max_bytes=1024)
    models.upsert(
        SimpleNamespace(is_superadmin=True, permissions=[], email="pcp@delpi.local"),
        product_code="50320064",
        original_filename="pi.glb",
        payload=_GLB,
    )
    service = _public_service(snapshots, repo, storage)
    payload = {
        "selected": {
            "items": [
                {"product_code": "50320064"},
                {"product_code": "90262957"},
            ]
        }
    }

    annotated = service.annotate_public_queue(payload)

    assert annotated["selected"]["items"][0]["has_3d_model"] is True
    assert annotated["selected"]["items"][1]["has_3d_model"] is False
