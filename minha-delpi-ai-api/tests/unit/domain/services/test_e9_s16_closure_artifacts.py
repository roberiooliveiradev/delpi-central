"""E9.S16 / tokens / archive — artefatos de fechamento dos débitos opcionais."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_F5 = _ROOT / "docs/roadmap/llm-json-decoupling/evidence/e9-s16-f5-session-reload-live.json"
_EFF = _ROOT / "docs/roadmap/llm-json-decoupling/evidence/e9-s11-efficiency-live-v1/results.json"
_ARCHIVED = _ROOT / "docs/roadmap/llm-json-decoupling/ARCHIVED.md"
_CHANGELOG = _ROOT / "docs/changelog/2026-09-llm-json-decoupling.md"


def test_e9_s16_f5_session_reload_artifact_pass():
    data = json.loads(_F5.read_text(encoding="utf-8"))
    assert data.get("pass") is True
    cases = data.get("cases") or {}
    assert cases.get("SEED_stock", {}).get("ok") is True
    assert cases.get("GET_messages_reload", {}).get("ok") is True
    assert cases.get("FOLLOWUP_same_product_after_reload", {}).get("ok") is True


def test_e9_s11_tokens_metadata_pass():
    data = json.loads(_EFF.read_text(encoding="utf-8"))
    assert data.get("decision") == "PASS"
    tokens = data.get("tokens") or {}
    assert tokens.get("status") == "PASS"
    assert tokens.get("trialsWithTokens", 0) >= 1
    assert tokens.get("totals")


def test_program_archived_and_changelog_exist():
    assert _ARCHIVED.is_file()
    assert "ARQUIVADO" in _ARCHIVED.read_text(encoding="utf-8")
    assert _CHANGELOG.is_file()
    assert "globalReleasePass" in _CHANGELOG.read_text(encoding="utf-8")
