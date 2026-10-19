"""Unit tests for migration planner — no live DB required."""

from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "migrate_protheus_identities_from_purchase_requests.py"
)


@pytest.fixture(scope="module")
def mig():
    import sys

    spec = importlib.util.spec_from_file_location("mig_protheus", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # dataclasses require the module to be present in sys.modules during decoration.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_orphan_blocks_before_any_plan_insert(mig):
    uid = str(uuid.uuid4())
    rows = [
        {
            "user_id": uid,
            "protheus_user_id": "000234",
            "protheus_user_code": "X",
            "mapping_status": "mapped",
            "mapping_source": "email_match",
            "verified": True,
        }
    ]
    plan, conflicts = mig.build_transfer_plan(rows, core_users={}, destination={})
    assert any(c.code == "orphan_user" for c in conflicts)
    assert all(item.action == "blocked" for item in plan)
    assert mig.blocking_conflicts(conflicts)


def test_identical_destination_is_noop(mig):
    uid = uuid.uuid4()
    row = {
        "user_id": str(uid),
        "protheus_user_id": "000234",
        "protheus_user_code": "X",
        "mapping_status": "mapped",
        "mapping_source": "email_match",
        "verified": True,
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    dest = {str(uid): dict(row, user_id=uid)}
    plan, conflicts = mig.build_transfer_plan(
        [row],
        core_users={uid: True},
        destination=dest,
    )
    assert not mig.blocking_conflicts(conflicts)
    assert plan[0].action == "identical"


def test_destination_divergence_blocks(mig):
    uid = uuid.uuid4()
    source = {
        "user_id": str(uid),
        "protheus_user_id": "000234",
        "protheus_user_code": "X",
        "mapping_status": "mapped",
        "mapping_source": "email_match",
        "verified": True,
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    dest_row = {
        **source,
        "user_id": uid,
        "protheus_user_id": "000999",
        "updated_at": datetime(2026, 2, 1, tzinfo=timezone.utc),
    }
    plan, conflicts = mig.build_transfer_plan(
        [source],
        core_users={uid: True},
        destination={str(uid): dest_row},
    )
    assert any(c.code == "destination_newer_divergence" for c in conflicts)
    assert plan[0].action == "blocked"


def test_duplicate_protheus_id_in_source_blocks(mig):
    u1 = uuid.uuid4()
    u2 = uuid.uuid4()
    rows = [
        {
            "user_id": str(u1),
            "protheus_user_id": "000234",
            "protheus_user_code": "A",
            "mapping_status": "mapped",
            "mapping_source": "manual",
            "verified": True,
        },
        {
            "user_id": str(u2),
            "protheus_user_id": "000234",
            "protheus_user_code": "B",
            "mapping_status": "mapped",
            "mapping_source": "manual",
            "verified": True,
        },
    ]
    _plan, conflicts = mig.build_transfer_plan(
        rows,
        core_users={u1: True, u2: True},
        destination={},
    )
    assert any(c.code == "duplicate_protheus_user_id" for c in conflicts)


def test_leading_zeros_preserved_in_semantic_snapshot(mig):
    snap = mig.semantic_snapshot(
        {
            "protheus_user_id": "000234",
            "protheus_user_code": "YAGO",
            "mapping_status": "mapped",
            "mapping_source": "email_match",
            "verified": True,
        }
    )
    assert snap["protheus_user_id"] == "000234"


def test_allow_conflicts_flag_removed(mig):
    import argparse

    parser = argparse.ArgumentParser()
    # Recreate CLI flags from main without executing DB.
    parser.add_argument("--plugins-dsn", required=True)
    parser.add_argument("--core-dsn", required=True)
    parser.add_argument("--apply", action="store_true")
    with pytest.raises(SystemExit):
        parser.parse_args(["--plugins-dsn", "x", "--core-dsn", "y", "--allow-conflicts"])
