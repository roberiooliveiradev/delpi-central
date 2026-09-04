"""Estrutura do harness de baseline — sem assertar PASS do gap atual."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests" / "fixtures" / "intelligence_baseline" / "routing_cases.json"
SCRIPT = ROOT / "scripts" / "chat_intelligence_baseline_harness.py"


def test_baseline_fixture_schema():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert raw.get("version") == 1
    cases = raw.get("cases") or []
    assert len(cases) >= 5
    for case in cases:
        assert case.get("id")
        assert case.get("message")
        assert isinstance(case.get("expect"), dict)


def test_baseline_harness_script_exists_and_runs(tmp_path, monkeypatch):
    assert SCRIPT.is_file()
    # Import smoke: harness main writes evidence
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("baseline_harness", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["baseline_harness"] = mod
    spec.loader.exec_module(mod)
    code = mod.main()
    assert code == 0
    out = ROOT / "docs" / "testing" / "evidence" / "chat-intelligence-baseline.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["total"] >= 5
    assert "metrics" in payload["summary"]
