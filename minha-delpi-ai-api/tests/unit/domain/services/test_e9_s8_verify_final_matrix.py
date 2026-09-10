"""E9.S8 — verify-final matrix: não declarar PASS global com INCONCLUSIVE."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_MATRIX = (
    _ROOT / "tests/fixtures/intelligence_baseline/e9_s8_verify_final_matrix.json"
)

_REQUIRED_IDS = {
    "unknown_api_no_code",
    "metamorphic_rename",
    "compound_long",
    "multi_turn_follow_up",
    "required_args",
    "safety",
    "presentation_schema",
    "recommendations_grounded",
    "send_stream_simulate_parity",
    "efficiency",
}


def _load() -> dict:
    return json.loads(_MATRIX.read_text(encoding="utf-8"))


def global_release_pass(data: dict) -> bool:
    blocking = set(data.get("blockingStatuses") or [])
    for row in data.get("matrix") or []:
        if str(row.get("status") or "") in blocking:
            return False
    return True


def test_e9_s8_matrix_covers_plan_objectives():
    data = _load()
    ids = {str(r.get("id") or "") for r in data.get("matrix") or []}
    assert _REQUIRED_IDS.issubset(ids)
    assert len(data["matrix"]) >= 10


def test_e9_s8_current_global_release_is_false():
    data = _load()
    assert data.get("globalReleasePass") is False
    assert global_release_pass(data) is False
    assert data.get("aggregate") == "PASS_OFFLINE_WITH_LIVE_EFFICIENCY"
    efficiency = next(r for r in data["matrix"] if r["id"] == "efficiency")
    assert efficiency["status"] == "PASS"


def test_e9_s8_each_row_has_evidence():
    data = _load()
    for row in data["matrix"]:
        evidence = str(row.get("evidence") or "")
        assert evidence, row.get("id")
        assert (_ROOT / evidence).is_file(), evidence
        assert str(row.get("status") or "").strip(), row.get("id")
        assert str(row.get("objective") or "").strip(), row.get("id")


def test_e9_s8_sibling_all_pass_would_release():
    data = _load()
    clone = json.loads(json.dumps(data))
    for row in clone["matrix"]:
        row["status"] = "PASS"
    assert global_release_pass(clone) is True


def test_e9_s8_negative_inconclusive_blocks_release():
    data = _load()
    clone = json.loads(json.dumps(data))
    for row in clone["matrix"]:
        row["status"] = "PASS"
    clone["matrix"][0]["status"] = "INCONCLUSIVE"
    assert global_release_pass(clone) is False
