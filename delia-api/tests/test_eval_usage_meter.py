"""Offline regression test for the eval harness LLM usage meter.

pydantic_ai 2.50 exposes ``AgentRunResult.usage`` as a **property**
(RunUsage), not a method — the meter previously called ``result.usage()``,
raised TypeError, and silently zeroed token counts in every eval run.
No live LLM/Keycloak/MCP required.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from pydantic_ai.usage import RunUsage

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_eval():
    path = _SCRIPTS / "native_mcptoolset_direct_eval.py"
    spec = importlib.util.spec_from_file_location(
        "native_mcptoolset_direct_eval_meter", path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeRunResult:
    @property
    def usage(self) -> RunUsage:
        return RunUsage(input_tokens=17, output_tokens=5, requests=2)


def test_meter_reads_usage_property_not_call(monkeypatch):
    import pydantic_ai

    eval_mod = _load_eval()
    recorded = []
    monkeypatch.setattr(
        pydantic_ai.Agent,
        "run_sync",
        lambda self, *a, **k: _FakeRunResult(),
    )
    eval_mod._LLM_USAGE.clear()
    eval_mod._install_usage_meter()
    try:
        pydantic_ai.Agent.run_sync(object())
    finally:
        monkeypatch.undo()
    assert len(eval_mod._LLM_USAGE) == 1
    usage = eval_mod._LLM_USAGE[0]["usage"]
    assert usage is not None
    assert usage["input_tokens"] == 17
    assert usage["output_tokens"] == 5
    assert usage["requests"] == 2
