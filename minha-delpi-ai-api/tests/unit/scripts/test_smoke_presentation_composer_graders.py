"""Graders do smoke de conversa do Presentation Composer."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SMOKE = (
    Path(__file__).resolve().parents[3]
    / "scripts/smoke_presentation_composer_conversation_live.py"
)


def _load_smoke():
    spec = importlib.util.spec_from_file_location("smoke_pc_conversation", _SMOKE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_t1_prompt_has_no_inspection_workaround():
    smoke = _load_smoke()
    turn = next(item for item in smoke._turns_for("10080001") if item["id"] == "T1.stock_table")
    message = str(turn["message"]).lower()
    assert "não inspeção" not in message
    assert "nao inspecao" not in message
    assert "consulte o estoque do produto 10080001" in message


def test_t1_grade_requires_stock_and_rejects_inspection():
    smoke = _load_smoke()
    snap = {
        "hasTable": True,
        "hasChart": False,
        "paths": ["/products/10080001/stock"],
        "answerExcerpt": "Estoque do produto 10080001",
        "selected": "table",
        "chartType": None,
        "paletteFamily": None,
        "unmetIntent": None,
        "unmetIntentNotice": None,
        "dimHints": [],
        "discriminantDims": [],
        "answerHasUnmetNotice": False,
        "answerLooksLikeClarification": False,
        "answerHasContextMissing": False,
        "canvasOpen": False,
        "canvasOpenPayload": None,
    }
    status, errors = smoke._grade("table_or_rows", snap, product="10080001")
    assert status == "PASS", errors

    fail_snap = {**snap, "paths": ["/products/10080001/inspection"]}
    status, errors = smoke._grade("table_or_rows", fail_snap, product="10080001")
    assert status == "FAIL"
    assert "missing_stock_path" in errors
    assert "inspection_path_in_plan" in errors


def test_t1_grade_sibling_saldo_path_still_stock_only():
    smoke = _load_smoke()
    snap = {
        "hasTable": True,
        "hasChart": False,
        "paths": ["/products/10080001/stock", "/products/10080001/inspection"],
        "answerExcerpt": "Saldo",
        "selected": "table",
        "chartType": None,
        "paletteFamily": None,
        "unmetIntent": None,
        "unmetIntentNotice": None,
        "dimHints": [],
        "discriminantDims": [],
        "answerHasUnmetNotice": False,
        "answerLooksLikeClarification": False,
        "answerHasContextMissing": False,
        "canvasOpen": False,
        "canvasOpenPayload": None,
    }
    status, errors = smoke._grade("table_or_rows", snap, product="10080001")
    assert status == "FAIL"
    assert "inspection_path_in_plan" in errors
