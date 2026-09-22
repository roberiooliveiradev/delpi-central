"""F4 — eval protocol authority residual (R1–R11 + write safety linkage)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_DOCS = _ROOT / "docs/testing/chat-ai-flow-families.md"
_INVENTORY = (
    _ROOT
    / "tests/fixtures/intelligence_baseline/f4_eval_protocol_authority_inventory.json"
)
_TESTS = _ROOT / "tests/unit"


def test_f4_inventory_core_canonical():
    payload = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in payload["items"]}
    assert by_id["r1_r11_protocol_doc"]["postStatus"] == "CANONICAL"
    assert by_id["r10_write_confirmation_coverage"]["postStatus"] == "COVERED"


def test_f4_r1_r11_dimensions_documented():
    text = _DOCS.read_text(encoding="utf-8")
    for dim in (f"**R{i}**" for i in range(1, 12)):
        assert dim in text, dim


def test_f4_r10_mentions_confirmation_safety():
    text = _DOCS.read_text(encoding="utf-8")
    section = re.search(r"\*\*R10\*\*.+", text)
    assert section, "R10 row missing"
    assert "confirmation" in section.group(0).lower() or "RBAC" in section.group(0)


def test_f4_residual_gates_exist_for_prior_epics():
    expected = [
        "application/services/test_f1_residual_selection_authority.py",
        "domain/services/test_f2_residual_presentation_authority.py",
        "domain/services/test_f3_residual_write_confirmation_authority.py",
        "application/use_cases/test_execute_external_action_write_confirmation.py",
    ]
    for rel in expected:
        assert (_TESTS / rel).is_file(), rel


def test_f4_negative_inconclusive_forbidden_in_verdict_rules():
    text = _DOCS.read_text(encoding="utf-8")
    assert "INCONCLUSIVE" in text
    assert "requiredDimension sem evidência" in text or "sem grader" in text
