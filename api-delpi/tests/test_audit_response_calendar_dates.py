"""Regressão do gate anti-YYYYMMDD em fixtures de resposta."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_audit_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_response_calendar_dates.py"
    )
    spec = importlib.util.spec_from_file_location("audit_response_calendar_dates", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_walk_flags_ymd_on_calendar_keys() -> None:
    audit = _load_audit_module()
    hits: list[dict[str, str]] = []
    audit._walk(
        {"reference_date": "20260611", "ok": "2026-06-11", "nested": {"start": "20260301"}},
        path="",
        hits=hits,
    )
    values = {h["value"] for h in hits}
    assert "20260611" in values
    assert "20260301" in values
    assert "2026-06-11" not in values


def test_audit_check_passes_on_clean_tree() -> None:
    audit = _load_audit_module()
    assert audit.check() == 0
