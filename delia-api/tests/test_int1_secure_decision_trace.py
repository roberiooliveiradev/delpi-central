"""Deterministic dry-run for INT-1 secure decision-trace persistence."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.int1_secure_decision_trace import (
    check_security_gate,
    run_dry_run,
    verify_persistence_after_exit,
)


def test_dry_run_persists_sanitized_decision_trace(tmp_path: Path) -> None:
    result = run_dry_run(root=tmp_path)
    assert result["TRACE_SCHEMA"] == "PASS"
    assert result["TRACE_SANITIZATION"] == "PASS"
    assert result["TOOL_SURFACE_CAPTURE"] == "PASS"
    assert result["ARGUMENT_CAPTURE"] == "PASS"
    assert result["PROGRESS_CAPTURE"] == "PASS"

    persisted = verify_persistence_after_exit(
        result["evaluation_id"],
        result["content_fingerprint"],
        root=tmp_path,
    )
    assert persisted["TRACE_PERSISTENCE_AFTER_EXIT"] == "PASS"

    path = Path(result["jsonl_path"])
    raw = path.read_text(encoding="utf-8")
    assert "should-never-persist" not in raw
    assert "<redacted>" in raw
    events = [json.loads(line) for line in raw.splitlines()]
    assert {item["event_type"] for item in events} >= {
        "evaluation_meta",
        "model_visible_toolset",
        "tool_call",
        "finalization",
    }


def test_gate_reports_settings_egress_block_without_flag(monkeypatch) -> None:
    monkeypatch.setenv("DELIA_ENV", "development")
    monkeypatch.delenv("DELIA_EVAL_EGRESS_AUTHORIZED", raising=False)
    monkeypatch.setenv("DELIA_LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("DELIA_LLM_API_KEY", "dummy")
    monkeypatch.setenv("DELIA_RUNTIME_PROFILE", "openrouter_qwen")
    gate = check_security_gate()
    assert gate["SECURE_EVAL_GATE"] == "BLOCKED"
    assert gate["POLICY_BLOCKS_EXTERNAL_BASE_URL"] is True
    assert gate["SECURITY_OWNER_APPROVAL"] == "NOT_A_RUNTIME_CONFIG_REQUIREMENT"
    assert "existing Settings LLM egress policy blocks this endpoint" in gate["BLOCKERS"]


def test_security_gate_ready_for_openrouter_with_flag(monkeypatch) -> None:
    monkeypatch.setenv("DELIA_ENV", "development")
    monkeypatch.setenv("DELIA_EVAL_EGRESS_AUTHORIZED", "1")
    monkeypatch.setenv("DELIA_LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("DELIA_LLM_API_KEY", "dummy")
    monkeypatch.setenv("DELIA_RUNTIME_PROFILE", "openrouter_qwen")
    gate = check_security_gate()
    assert gate["SECURE_EVAL_GATE"] == "READY_FOR_ISOLATED_EVAL"
    assert gate["POLICY_BLOCKS_EXTERNAL_BASE_URL"] is False
    assert gate["SECURITY_OWNER_APPROVAL"] == "NOT_A_RUNTIME_CONFIG_REQUIREMENT"
    assert gate["MCP_READ_AUTHORIZED"] == "VERIFY_WITH_OWNER"
    assert not gate["BLOCKERS"]


def test_security_gate_blocks_localhost_proxy_even_with_flag(monkeypatch) -> None:
    monkeypatch.setenv("DELIA_ENV", "development")
    monkeypatch.setenv("DELIA_EVAL_EGRESS_AUTHORIZED", "1")
    monkeypatch.setenv("DELIA_LLM_BASE_URL", "http://127.0.0.1:18765/api/v1")
    monkeypatch.setenv("DELIA_LLM_API_KEY", "dummy")
    monkeypatch.setenv("DELIA_RUNTIME_PROFILE", "openrouter_qwen")
    gate = check_security_gate()
    assert gate["SECURE_EVAL_GATE"] == "BLOCKED"
    # Host must be openrouter.ai — localhost/proxy endpoints are refused
    # by the same endpoint-identity blocker (no duplicate approval gate).
    assert any(
        "openrouter.ai" in item or "localhost" in item or "127.0.0.1" in item
        for item in gate["BLOCKERS"]
    ) or any(
        "evaluation endpoint must be" in item for item in gate["BLOCKERS"]
    )
