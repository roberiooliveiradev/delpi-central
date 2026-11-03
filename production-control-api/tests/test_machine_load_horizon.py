"""Horizonte temporário por CT — prévia/aplicação WORKING-only (OPÇÃO A)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest

from production_control_app.domain.errors import MachineLoadSequenceConflict
from production_control_app.domain.services.machine_load_horizon import (
    HORIZON_EXCEPTIONS_KEY,
    HORIZON_EXPANDED_FLAG,
    additional_period_start,
    append_operations_after_center,
    filter_new_horizon_operations,
    validate_horizon_end,
)
from tests.test_machine_load import (
    FULL_PERMS,
    FakeGateway,
    FakeSnapshotRepo,
    _OPERATION,
    _service,
    _user,
)


def _op(**overrides: Any) -> dict[str, Any]:
    item = {**_OPERATION, "due_date": "2026-08-21"}
    item.update(overrides)
    return item


def test_validate_horizon_end_requires_beyond_base() -> None:
    today = date(2026, 8, 19)
    base = today + timedelta(days=14)
    with pytest.raises(ValueError, match="ultrapassar"):
        validate_horizon_end(requested_end=base, base_end=base, today=today)
    validate_horizon_end(
        requested_end=base + timedelta(days=1), base_end=base, today=today
    )


def test_append_operations_after_center_keeps_siblings() -> None:
    ops = [
        _op(work_center="CT-A", production_order="1"),
        _op(work_center="CT-B", production_order="2"),
        _op(work_center="CT-A", production_order="3"),
        _op(work_center="CT-B", production_order="4"),
    ]
    extra = [_op(work_center="CT-A", production_order="9")]
    merged = append_operations_after_center(
        ops, work_center="CT-A", new_operations=extra
    )
    assert [o["production_order"] for o in merged] == ["1", "2", "3", "9", "4"]


def test_filter_skips_existing_identity_even_on_other_ct() -> None:
    existing = {("24640401002", "03")}
    candidates = [
        _op(work_center="CT-A", production_order="24640401002", operation_code="03"),
        _op(
            work_center="CT-A",
            production_order="99940401002",
            operation_code="01",
            due_date="2026-09-10",
        ),
    ]
    added = filter_new_horizon_operations(
        candidates=candidates,
        work_center="CT-A",
        existing=existing,
        additional_start=date(2026, 9, 3),
        additional_end=date(2026, 9, 16),
    )
    assert len(added) == 1
    assert added[0]["production_order"] == "99940401002"
    assert added[0][HORIZON_EXPANDED_FLAG] is True


def test_preview_does_not_mutate_working_or_published() -> None:
    gateway = FakeGateway(
        work_centers=[
            {
                "work_center": "CT-A",
                "work_center_name": "CORTE",
                "operation_count": 1,
                "in_production_count": 0,
            },
            {
                "work_center": "CT-B",
                "work_center_name": "DECAPE",
                "operation_count": 1,
                "in_production_count": 0,
            },
        ],
        operations=[
            _op(work_center="CT-A", production_order="A1", due_date="2026-09-10"),
            _op(work_center="CT-B", production_order="B1", due_date="2026-09-10"),
        ],
    )
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    base_end = date(2026, 9, 2)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=base_end,
        generation_id="gen-draft",
        payload={
            "work_centers": gateway.work_centers,
            "operations": [
                _op(work_center="CT-A", production_order="A0", due_date="2026-08-25"),
                _op(work_center="CT-B", production_order="B0", due_date="2026-08-25"),
            ],
            "summary": {"operation_count": 2, "order_count": 2},
        },
        refreshed_by="pcp",
    )
    before = snapshots.get(branch="01")
    assert before is not None
    preview = service.preview_horizon_expansion(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-A",
        end_date=(base_end + timedelta(days=14)).isoformat(),
        expected_generation_id="gen-draft",
    )
    assert preview["new_operation_count"] == 1
    assert preview["work_center"] == "CT-A"
    assert snapshots.get(branch="01") == before
    assert snapshots.published == {}
    op_calls = [c for c in gateway.calls if c[0] == "operations"]
    assert op_calls
    assert op_calls[0][1]["work_center"] == "CT-A"
    assert op_calls[0][1]["delivery_start"] == additional_period_start(base_end).isoformat()


def test_apply_only_working_preserves_sibling_ct_and_order() -> None:
    gateway = FakeGateway(
        work_centers=[
            {
                "work_center": "CT-A",
                "work_center_name": "CORTE",
                "operation_count": 1,
                "in_production_count": 0,
            },
            {
                "work_center": "CT-B",
                "work_center_name": "DECAPE",
                "operation_count": 1,
                "in_production_count": 0,
            },
        ],
        operations=[
            _op(work_center="CT-A", production_order="A-NEW", due_date="2026-09-10"),
            _op(work_center="CT-B", production_order="B-NEW", due_date="2026-09-10"),
        ],
    )
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    base_end = date(2026, 9, 2)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=base_end,
        generation_id="gen-draft",
        payload={
            "work_centers": gateway.work_centers,
            "operations": [
                _op(work_center="CT-A", production_order="A0", due_date="2026-08-25"),
                _op(work_center="CT-B", production_order="B0", due_date="2026-08-25"),
            ],
            "summary": {"operation_count": 2, "order_count": 2},
        },
        refreshed_by="pcp",
    )
    end = (base_end + timedelta(days=14)).isoformat()
    result = service.apply_horizon_expansion(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-A",
        end_date=end,
        expected_generation_id="gen-draft",
        expected_new_operation_count=1,
    )
    assert result["horizon_expansion"]["added_count"] == 1
    assert result["publication"]["state"] == "unpublished"
    assert snapshots.published == {}
    ops = snapshots.rows["01"]["payload_json"]["operations"]
    orders = [o["production_order"] for o in ops]
    assert orders == ["A0", "A-NEW", "B0"]
    assert ops[1][HORIZON_EXPANDED_FLAG] is True
    assert HORIZON_EXCEPTIONS_KEY in snapshots.rows["01"]["payload_json"]
    assert "CT-A" in snapshots.rows["01"]["payload_json"][HORIZON_EXCEPTIONS_KEY]
    assert "CT-B" not in snapshots.rows["01"]["payload_json"][HORIZON_EXCEPTIONS_KEY]
    # CT-B não ganhou a OP futura do gateway.
    assert "B-NEW" not in orders


def test_apply_rejects_live_without_touching_published() -> None:
    gateway = FakeGateway(operations=[])
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 2),
        generation_id="gen-live",
        payload={"work_centers": [], "operations": []},
        refreshed_by="pcp",
    )
    snapshots.publish("01")
    with pytest.raises(MachineLoadSequenceConflict, match="Atualizar"):
        service.apply_horizon_expansion(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-A",
            end_date="2026-09-16",
            expected_generation_id="gen-live",
        )
    assert snapshots.payload_updates == 0


def test_apply_idempotent_and_multi_ct_exceptions() -> None:
    gateway = FakeGateway(
        work_centers=[
            {
                "work_center": "CT-A",
                "work_center_name": "A",
                "operation_count": 0,
                "in_production_count": 0,
            },
            {
                "work_center": "CT-B",
                "work_center_name": "B",
                "operation_count": 0,
                "in_production_count": 0,
            },
        ],
        operations=[
            _op(work_center="CT-A", production_order="A1", due_date="2026-09-10"),
            _op(work_center="CT-B", production_order="B1", due_date="2026-09-10"),
        ],
    )
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    base_end = date(2026, 9, 2)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=base_end,
        generation_id="gen-draft",
        payload={
            "work_centers": gateway.work_centers,
            "operations": [
                _op(work_center="CT-A", production_order="A0", due_date="2026-08-25"),
                _op(work_center="CT-B", production_order="B0", due_date="2026-08-25"),
            ],
        },
        refreshed_by="pcp",
    )
    end = (base_end + timedelta(days=14)).isoformat()
    first = service.apply_horizon_expansion(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-A",
        end_date=end,
        expected_generation_id="gen-draft",
    )
    assert first["horizon_expansion"]["added_count"] == 1
    second = service.apply_horizon_expansion(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-A",
        end_date=end,
        expected_generation_id="gen-draft",
    )
    assert second["horizon_expansion"]["added_count"] == 0
    assert second["horizon_expansion"]["idempotent"] is True
    service.apply_horizon_expansion(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-B",
        end_date=end,
        expected_generation_id="gen-draft",
    )
    exceptions = snapshots.rows["01"]["payload_json"][HORIZON_EXCEPTIONS_KEY]
    assert set(exceptions) == {"CT-A", "CT-B"}
    orders = [
        o["production_order"]
        for o in snapshots.rows["01"]["payload_json"]["operations"]
    ]
    assert orders.count("A1") == 1
    assert orders.count("B1") == 1


def test_refresh_discards_horizon_exceptions() -> None:
    gateway = FakeGateway(
        work_centers=[
            {
                "work_center": "CT-A",
                "work_center_name": "A",
                "operation_count": 1,
                "in_production_count": 0,
            }
        ],
        operations=[_op(work_center="CT-A", production_order="BASE", due_date="2026-08-25")],
    )
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 2),
        generation_id="gen-old",
        payload={
            "work_centers": gateway.work_centers,
            "operations": [
                _op(work_center="CT-A", production_order="OLD", due_date="2026-08-25"),
                _op(
                    work_center="CT-A",
                    production_order="EXP",
                    due_date="2026-09-10",
                    horizon_expanded=True,
                ),
            ],
            HORIZON_EXCEPTIONS_KEY: {
                "CT-A": {
                    "end_date": "2026-09-16",
                    "base_end_date": "2026-09-02",
                    "added_count": 1,
                }
            },
        },
        refreshed_by="pcp",
    )
    service.refresh(_user(*FULL_PERMS), branch="01")
    payload = snapshots.rows["01"]["payload_json"]
    assert HORIZON_EXCEPTIONS_KEY not in payload
    assert all(not item.get(HORIZON_EXPANDED_FLAG) for item in payload["operations"])
    assert snapshots.rows["01"]["generation_id"] != "gen-old"


def test_stale_preview_count_conflicts() -> None:
    gateway = FakeGateway(
        operations=[
            _op(work_center="CT-A", production_order="A1", due_date="2026-09-10"),
        ]
    )
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 2),
        generation_id="gen-draft",
        payload={
            "work_centers": [
                {
                    "work_center": "CT-A",
                    "work_center_name": "A",
                    "operation_count": 0,
                    "in_production_count": 0,
                }
            ],
            "operations": [],
        },
        refreshed_by="pcp",
    )
    with pytest.raises(MachineLoadSequenceConflict, match="obsoleta"):
        service.apply_horizon_expansion(
            _user(*FULL_PERMS),
            branch="01",
            work_center="CT-A",
            end_date="2026-09-16",
            expected_generation_id="gen-draft",
            expected_new_operation_count=99,
        )


def test_forbidden_without_permission() -> None:
    gateway = FakeGateway()
    snapshots = FakeSnapshotRepo()
    service = _service(gateway, snapshots)
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 2),
        generation_id="gen-draft",
        payload={"work_centers": [], "operations": []},
        refreshed_by="pcp",
    )
    with pytest.raises(PermissionError):
        service.preview_horizon_expansion(
            _user("production-control.access", "production-control.view.filial-01"),
            branch="01",
            work_center="CT-A",
            end_date="2026-09-16",
            expected_generation_id="gen-draft",
        )
