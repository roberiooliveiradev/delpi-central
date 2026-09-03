"""Estrutura da bateria de interação humana — sem HTTP."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "human_interaction_battery_live.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("human_interaction_battery_live", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["human_interaction_battery_live"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_catalog_covers_core_families():
    mod = _load_module()
    cases = mod._cases_catalog()
    assert len(cases) >= 20
    families = {c.family for c in cases}
    for required in ("F01", "F03", "F04", "F14", "F19"):
        assert required in families, f"missing family {required}"


def test_typo_estrutra_case_present():
    mod = _load_module()
    ids = {c.case_id for c in mod._cases_catalog()}
    assert "F03.2-typo-estrutra" in ids


def test_judge_identity_fast_flags_slow():
    mod = _load_module()
    case = mod.BatteryCase("t", "F19", "x", "como vc se chama?", "identity_fast")
    msg = {"content": "Sou a Minha DELPI.", "toolCalls": []}
    mod._judge(case, msg, 12000)
    assert case.status == "FAIL"
    assert "lento" in case.detail


def test_judge_sql_authoring_pass():
    mod = _load_module()
    case = mod.BatteryCase("t", "F04", "x", "crie sql", "sql_authoring")
    msg = {
        "content": "```sql\nSELECT TOP 10 B1_COD FROM SB1010\n```",
        "toolCalls": [],
    }
    mod._judge(case, msg, 2000)
    assert case.status == "PASS"


def test_judge_sql_authoring_fails_on_data_sql_path():
    mod = _load_module()
    case = mod.BatteryCase("t", "F04", "x", "crie sql", "sql_authoring")
    msg = {
        "content": "```sql\nSELECT TOP 10 B1_COD FROM SB1010\n```",
        "toolCalls": [
            {
                "name": "execute_external_action",
                "metadata": {"path": "/data/sql", "ok": True},
            }
        ],
    }
    mod._judge(case, msg, 2000)
    assert case.status == "FAIL"
    assert "/data/sql" in case.detail
