"""E9.S6 — cleanup gates: DELETE só com todas as dimensões required em PASS pleno."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_GATES = _ROOT / "tests/fixtures/intelligence_baseline/e9_s6_cleanup_gates.json"

_REQUIRED_GATE_IDS = {
    "candidate_task_success",
    "unknown_api",
    "metamorphic",
    "safety",
    "required_args",
    "multi_turn",
    "compound",
    "latency_cost",
    "legacy_fallback_hit_rate",
}

_BLOCKING = frozenset({"INCONCLUSIVE", "PENDING", "FAIL", "PENDING_RUNTIME"})


def _load() -> dict:
    return json.loads(_GATES.read_text(encoding="utf-8"))


def delete_authorized(data: dict) -> bool:
    """Autoriza DELETE somente se nenhum gate required estiver bloqueando."""
    allow = set(data.get("passStatusesForDelete") or ["PASS"])
    for gate in data.get("gates") or []:
        if not gate.get("required", True):
            continue
        status = str(gate.get("status") or "")
        if status not in allow:
            return False
    return True


def test_e9_s6_required_gates_present():
    data = _load()
    ids = {str(g.get("id") or "") for g in data.get("gates") or []}
    assert _REQUIRED_GATE_IDS.issubset(ids)


def test_e9_s6_current_evaluation_blocks_delete():
    """Positive (estado atual): deleteAuthorized=false enquanto há PASS_OFFLINE."""
    data = _load()
    assert data.get("deleteAuthorized") is False
    assert delete_authorized(data) is False
    offline_only = [
        g["id"]
        for g in data["gates"]
        if g.get("required") and str(g.get("status")) == "PASS_OFFLINE"
    ]
    # E9.S11: latency_cost=PASS; demais dims offline ainda bloqueiam DELETE.
    assert offline_only
    latency = next(g for g in data["gates"] if g["id"] == "latency_cost")
    assert latency["status"] == "PASS"


def test_e9_s6_delete_candidates_are_blocked():
    data = _load()
    candidates = data.get("deleteCandidates") or []
    assert len(candidates) >= 3
    for item in candidates:
        assert item.get("status") == "BLOCKED", item.get("id")
        assert str(item.get("blockReason") or "").strip(), item.get("id")
        assert str(item.get("owner") or "").strip(), item.get("id")
        assert item.get("fields"), item.get("id")


def test_e9_s6_evidence_paths_exist():
    data = _load()
    for gate in data["gates"]:
        evidence = str(gate.get("evidence") or "")
        assert evidence, gate.get("id")
        assert (_ROOT / evidence).is_file(), evidence


def test_e9_s6_sibling_all_pass_would_authorize():
    """Sibling: se todos required forem PASS pleno, authorize=true."""
    data = _load()
    clone = json.loads(json.dumps(data))
    for gate in clone["gates"]:
        if gate.get("required"):
            gate["status"] = "PASS"
    assert delete_authorized(clone) is True


def test_e9_s6_negative_pass_offline_alone_does_not_authorize():
    """Negative: PASS_OFFLINE não está em passStatusesForDelete → sem DELETE."""
    data = _load()
    clone = json.loads(json.dumps(data))
    for gate in clone["gates"]:
        if gate.get("required"):
            gate["status"] = "PASS_OFFLINE"
    assert "PASS_OFFLINE" not in set(clone.get("passStatusesForDelete") or [])
    assert delete_authorized(clone) is False
