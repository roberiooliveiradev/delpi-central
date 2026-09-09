"""Harness E8 graders — empty tokens must never silent PASS."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SMOKE = Path(__file__).resolve().parents[3] / "scripts/smoke_conversation_context_quality_live.py"


def _load_smoke():
    spec = importlib.util.spec_from_file_location("smoke_e8", _SMOKE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_family_ok_empty_tokens_inconclusive():
    smoke = _load_smoke()
    assert smoke._family_ok("forbidden", [], []) == "INCONCLUSIVE"
    assert smoke._family_ok("capabilities", [], []) == "INCONCLUSIVE"


def test_family_ok_stock_pass_and_fail():
    smoke = _load_smoke()
    assert smoke._family_ok("stock", ["/products/1/stock"], []) == "PASS"
    assert smoke._family_ok("stock", ["/commercial/rol"], []) == "FAIL"


def test_provider_ok_requires_evidence():
    smoke = _load_smoke()
    assert smoke._provider_ok("nebula-factory", {}, {}) == "FAIL"
    assert (
        smoke._provider_ok(
            "nebula-factory",
            {},
            {
                "toolCalls": [
                    {
                        "metadata": {"providerKey": "nebula-factory", "path": "/x"},
                        "arguments": {"actionId": "nebula.export"},
                    }
                ]
            },
        )
        == "PASS"
    )
