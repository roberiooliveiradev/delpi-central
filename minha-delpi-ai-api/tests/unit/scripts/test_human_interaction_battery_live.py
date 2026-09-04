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
    for required in ("F01", "F03", "F04", "F06", "F07", "F14", "F19"):
        assert required in families, f"missing family {required}"


def test_f07_rag_cases_present():
    mod = _load_module()
    by_id = {c.case_id: c for c in mod._cases_catalog()}
    assert "F07.policy" in by_id
    assert "F07.glossary" in by_id
    assert "F07.stock-policy" in by_id
    assert "F07.follow-terminais" in by_id
    assert "F07.normas" in by_id
    normas = by_id["F07.normas"]
    assert normas.require_rag_hits is True
    assert normas.forbid_empty_rag_prose is True
    follow = by_id["F07.follow-terminais"]
    assert follow.judge_seed is True
    assert follow.prose_markers


def test_f11_technical_description_cases_present():
    mod = _load_module()
    by_id = {c.case_id: c for c in mod._cases_catalog()}
    assert "F11.terminal" in by_id
    assert "F11.vdar" in by_id
    assert "F11.cabo" in by_id
    assert "F11.intermediario" in by_id
    assert "F11.produto-cadastro" in by_id
    assert by_id["F11.terminal"].expect == "rag_internal"
    assert by_id["F11.produto-cadastro"].expect == "product_path"
    assert "F11.compliance-mp" in by_id
    assert "F11.compliance-intermediario" in by_id
    assert "F11.compliance-pa" in by_id
    assert by_id["F11.compliance-mp"].expect == "normas_compliance_eval"
    assert by_id["F11.compliance-pa"].expect == "normas_compliance_missing"
    assert by_id["F11.compliance-mp"].seed
    assert by_id["F11.compliance-mp"].require_rag_hits is True
    assert by_id["F11.compliance-intermediario"].require_rag_hits is True
    assert by_id["F11.compliance-intermediario"].forbid_empty_rag_prose is False


def test_empty_rag_prose_ignores_field_level_hedge():
    """«não consigo confirmar [campo]» ≠ admitir retrieve vazio."""
    mod = _load_module()
    assert not mod.EMPTY_RAG_PROSE_RE.search(
        "majoritariamente conforme, com ressalva que não consigo confirmar o ROHS no trecho."
    )
    assert mod.EMPTY_RAG_PROSE_RE.search("não tenho a norma do grupo 1008")
    assert mod.EMPTY_RAG_PROSE_RE.search("não consigo encontrar na base")


def test_judge_rag_fails_on_empty_admission_when_grounded_required():
    mod = _load_module()
    case = mod.BatteryCase(
        "t",
        "F07",
        "x",
        "o que dizem as normas técnicas DELPI sobre matéria-prima?",
        "rag_internal",
        require_rag_hits=True,
        forbid_empty_rag_prose=True,
        prose_markers=("1001", "norma"),
    )
    msg = {
        "content": "Não tenho o conteúdo detalhado disponível na base de conhecimento neste momento.",
        "toolCalls": [],
        "adminDebug": {
            "intentRoute": {"decision": "rag_internal", "intent": "rag_question"},
            "pipeline": {"skipRag": False},
            "rag": {"retrievedChunkCount": 0, "sources": []},
        },
    }
    mod._judge(case, msg, 2000)
    assert case.status == "FAIL"
    assert "retrieve vazio" in case.detail or "RAG sem hits" in case.detail


def test_judge_rag_passes_with_hits_and_markers():
    mod = _load_module()
    case = mod.BatteryCase(
        "t",
        "F07",
        "x",
        "o que dizem as normas técnicas DELPI sobre matéria-prima?",
        "rag_internal",
        require_rag_hits=True,
        forbid_empty_rag_prose=True,
        prose_markers=("1001", "norma"),
    )
    msg = {
        "content": "As Normas Técnicas DELPI cobrem grupos 1001 a 1025 para matéria-prima.",
        "toolCalls": [],
        "metadata": {"interactivity": {"suggestions": [{"label": "O que você pode fazer?"}]}},
        "adminDebug": {
            "intentRoute": {"decision": "rag_internal", "intent": "rag_question"},
            "pipeline": {"skipRag": False},
            "rag": {"retrievedChunkCount": 2, "ragContextText": "x" * 100},
        },
    }
    mod._judge(case, msg, 2000)
    assert case.status == "PASS"

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


def test_judge_capabilities_flags_slow():
    mod = _load_module()
    case = mod.BatteryCase("t", "F02", "x", "o q vc pode fazer?", "capabilities")
    msg = {
        "content": "Posso ajudar com consultas autorizadas e documentação da plataforma.",
        "toolCalls": [],
    }
    mod._judge(case, msg, 15000)
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
