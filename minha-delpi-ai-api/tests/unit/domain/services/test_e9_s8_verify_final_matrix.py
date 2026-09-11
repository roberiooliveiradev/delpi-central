"""E9.S8 — verify-final matrix: globalReleasePass só com células não-bloqueantes."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_MATRIX = (
    _ROOT / "tests/fixtures/intelligence_baseline/e9_s8_verify_final_matrix.json"
)
_GATES = _ROOT / "tests/fixtures/intelligence_baseline/e9_s6_cleanup_gates.json"
_S15_EVIDENCE = (
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/e9-s15-release-blockers-live.md"
)
_S15_JSON = (
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/e9-s15-release-blockers-live.json"
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


def test_e9_s8_global_release_pass_true_after_s15():
    """Positive: pós E9.S15 nenhuma célula blocking; release liberado."""
    data = _load()
    assert data.get("globalReleasePass") is True
    assert global_release_pass(data) is True
    assert data.get("aggregate") == "PASS_OFFLINE_AND_LIVE"
    assert data.get("blockingCells") == []
    efficiency = next(r for r in data["matrix"] if r["id"] == "efficiency")
    assert efficiency["status"] == "PASS"


def test_e9_s8_live_promoted_cells_after_s13_s15():
    """Sibling: gates com live E9.S13/S14/S15 não ficam PASS_OFFLINE."""
    data = _load()
    by_id = {r["id"]: r for r in data["matrix"]}
    for rid in (
        "unknown_api_no_code",
        "metamorphic_rename",
        "compound_long",
        "multi_turn_follow_up",
        "required_args",
        "safety",
        "presentation_schema",
        "recommendations_grounded",
        "send_stream_simulate_parity",
    ):
        assert by_id[rid]["status"] == "PASS_OFFLINE_AND_LIVE", rid


def test_e9_s8_aligned_with_delete_authorized_gates():
    """Gates E9.S6 já autorizam DELETE; verify-final release agora também passa."""
    gates = json.loads(_GATES.read_text(encoding="utf-8"))
    assert gates.get("deleteAuthorized") is True
    data = _load()
    assert data.get("deleteAuthorizedRef") is True
    assert data.get("globalReleasePass") is True


def test_e9_s8_each_row_has_evidence():
    data = _load()
    for row in data["matrix"]:
        evidence = str(row.get("evidence") or "")
        assert evidence, row.get("id")
        assert (_ROOT / evidence).is_file(), evidence
        assert str(row.get("status") or "").strip(), row.get("id")
        assert str(row.get("objective") or "").strip(), row.get("id")


def test_e9_s8_s15_evidence_artifact_pass():
    """Positive: artefato live E9.S15 reporta PASS nas duas células."""
    assert _S15_EVIDENCE.is_file()
    assert _S15_JSON.is_file()
    data = json.loads(_S15_JSON.read_text(encoding="utf-8"))
    assert data.get("pass") is True
    gates = data.get("gates") or {}
    assert gates.get("recommendations_grounded") == "PASS"
    assert gates.get("send_stream_simulate_parity") == "PASS"


def test_e9_s8_sibling_pass_offline_would_block_release():
    """Sibling: reintroduzir PASS_OFFLINE bloqueia release."""
    data = _load()
    clone = json.loads(json.dumps(data))
    clone["matrix"][0]["status"] = "PASS_OFFLINE"
    assert global_release_pass(clone) is False


def test_e9_s8_negative_inconclusive_blocks_release():
    data = _load()
    clone = json.loads(json.dumps(data))
    for row in clone["matrix"]:
        row["status"] = "PASS"
    clone["matrix"][0]["status"] = "INCONCLUSIVE"
    assert global_release_pass(clone) is False
