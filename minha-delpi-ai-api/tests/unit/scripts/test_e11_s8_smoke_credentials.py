"""E11.S8 — smoke credentials require env (no versioned defaults)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_CRED_PATH = _SCRIPTS / "smoke_credentials.py"


def _load_smoke_credentials():
    spec = importlib.util.spec_from_file_location("smoke_credentials", _CRED_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_require_smoke_credentials_fails_without_env(monkeypatch):
    mod = _load_smoke_credentials()
    monkeypatch.delenv("SMOKE_USER", raising=False)
    monkeypatch.delenv("SMOKE_PASSWORD", raising=False)
    with pytest.raises(SystemExit) as exc:
        mod.require_smoke_credentials()
    assert exc.value.code == 2


def test_require_smoke_credentials_ok(monkeypatch):
    mod = _load_smoke_credentials()
    monkeypatch.setenv("SMOKE_USER", "alice")
    monkeypatch.setenv("SMOKE_PASSWORD", "secret")
    assert mod.require_smoke_credentials() == ("alice", "secret")


def test_semantic_smoke_credential_debt_is_zero():
    root = Path(__file__).resolve().parents[3].parent
    sys.path.insert(0, str(root))
    from scripts.ci import audit_architecture_phase3 as phase3

    findings = [
        item
        for item in phase3.scan_semantic_debt_workspace()
        if item.rule == "SEMANTIC_SMOKE_CREDENTIAL_DEFAULT"
    ]
    assert findings == []
