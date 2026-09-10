"""E9.S10 — send/stream completion parity offline (+ artefato residual stream/simulate)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_RESIDUAL = (
    _ROOT / "docs/testing/evidence/residual_path_display_stream_simulate.json"
)
_PARITY_MODULE = (
    _ROOT
    / "tests/unit/application/services/test_chat_turn_completion_parity.py"
)


def test_e9_s10_completion_parity_harness_exists():
    assert _PARITY_MODULE.is_file()
    text = _PARITY_MODULE.read_text(encoding="utf-8")
    assert "test_send_and_stream_share_core_metadata_keys" in text


def test_e9_s10_residual_stream_simulate_artifact_pass():
    """Positive: artefato D4 stream/simulate reporta PASS (evidência histórica)."""
    data = json.loads(_RESIDUAL.read_text(encoding="utf-8"))
    surfaces = data.get("SURFACES") or {}
    assert surfaces.get("STREAM") == "PASS"
    assert surfaces.get("SIMULATE") == "PASS"
    assert data.get("pass") is True


def test_e9_s10_negative_artifact_is_not_live_latency_gate():
    """Negative: artefato de superfície ≠ medição P50/P95 (latency permanece aberta)."""
    data = json.loads(_RESIDUAL.read_text(encoding="utf-8"))
    blob = json.dumps(data)
    assert "p50" not in blob.lower()
    assert "p95" not in blob.lower()
