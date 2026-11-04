"""Doc 222 E4 — multi-evidence composition verifier (deterministic).

Model proposals are corroboration only; FACTS come from the bounded
deterministic diff with full coverage. Every claim must resolve to
an owner-backed record ref — fabricated refs rejected, omissions
still covered.
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    _flatten_evidence_records,
    _render_evidence_comparison,
    _verify_evidence_composition,
)

# Real BOM shapes captured via DAVI get_product_structure (M7/DIAG).
_LEFT = [
    {"code": "90260147", "quantity": 1, "unit": "MI", "type": "PA"},
    {"code": "50220013", "quantity": 2, "unit": "MI", "type": "PI"},
    {"code": "10030015", "quantity": 368, "unit": "MT", "type": "MP"},
    {"code": "10080031", "quantity": 1000, "unit": "PC", "type": "MP"},
    {"code": "50220014", "quantity": 2, "unit": "MI", "type": "PI"},
    {"code": "10030019", "quantity": 318, "unit": "MT", "type": "MP"},
    {"code": "10080031", "quantity": 1000, "unit": "PC", "type": "MP"},
]
_RIGHT = [
    {"code": "90260148", "quantity": 1, "unit": "MI", "type": "PA"},
    {"code": "50220013", "quantity": 2, "unit": "MI", "type": "PI"},
    {"code": "10030015", "quantity": 368, "unit": "MT", "type": "MP"},
    {"code": "10080031", "quantity": 1000, "unit": "PC", "type": "MP"},
    {"code": "50220015", "quantity": 2, "unit": "MI", "type": "PI"},
    {"code": "10030012", "quantity": 318, "unit": "MT", "type": "MP"},
    {"code": "10080031", "quantity": 1000, "unit": "PC", "type": "MP"},
]


def _sources():
    return {
        "90260147": _LEFT,
        "90260148": _RIGHT,
    }


def test_flatten_preserves_codes_qty_units_and_paths():
    rows = _flatten_evidence_records(_LEFT)
    codes = [r["code"] for r in rows]
    assert "10080031" in codes and codes.count("10080031") == 2
    paths = {r["code"]: r["path"] for r in rows}
    assert paths["90260147"] != paths["50220013"]


def test_flatten_nested_bom_components():
    nested = [
        {
            "code": "A1",
            "quantity": 1,
            "components": [
                {"code": "B1", "quantity": 3, "unit": "PC"},
                {"code": "B2", "quantity": 2, "unit": "PC"},
            ],
        }
    ]
    rows = _flatten_evidence_records(nested)
    assert {r["code"] for r in rows} == {"A1", "B1", "B2"}
    assert next(r for r in rows if r["code"] == "B1")["path"] != (0,)


def test_verify_real_pair_common_exclusive_and_quantities():
    result = _verify_evidence_composition(_sources(), None)
    claims = result["claims"]
    assert result["verdict"] == "differences_found"
    assert {e["code"] for e in claims["common"]} == {
        "50220013",
        "10030015",
        "10080031",
    }
    assert {e["code"] for e in claims["exclusive_left"]} == {
        "90260147",
        "50220014",
        "10030019",
    }
    assert {e["code"] for e in claims["exclusive_right"]} == {
        "90260148",
        "50220015",
        "10030012",
    }
    # quantities equal on all common items → no qty diff claimed
    assert claims["qty_differences"] == []


def test_verify_covers_records_the_model_omitted():
    # model proposal that forgot 10030015 — coverage must still
    # include it as common (omission risk is never model-bounded).
    proposal = {"proposed_pairs": [
        {"left_code": "50220013", "right_code": "50220013"},
    ]}
    result = _verify_evidence_composition(_sources(), proposal)
    assert "10030015" in {e["code"] for e in result["claims"]["common"]}


def test_verify_rejects_fabricated_proposal_refs():
    # the known Qwen3 error — claims 10030012 exists on the LEFT
    proposal = {"proposed_pairs": [
        {"left_code": "10030012", "right_code": "10030012"},
        {"left_code": "ghost999", "right_code": "10080031"},
    ]}
    result = _verify_evidence_composition(_sources(), proposal)
    assert any(
        lim.startswith("unsupported_proposal_refs")
        for lim in result["limitations"]
    )
    # 10030012 stays exclusive to the RIGHT side — never common.
    assert {e["code"] for e in result["claims"]["exclusive_right"]} >= {
        "10030012"
    }
    assert "10030012" not in {
        e["code"] for e in result["claims"]["common"]
    }


def test_verify_inconclusive_with_fewer_than_two_sources():
    result = _verify_evidence_composition(
        {"90260147": _LEFT, "empty": []}, None
    )
    assert result["verdict"] == "inconclusive"
    assert "evidence_partial" in result["limitations"]


def test_verify_detects_quantity_difference_on_shared_code():
    right = [dict(r) for r in _RIGHT]
    for r in right:
        if r["code"] == "10080031":
            r["quantity"] = 999
    result = _verify_evidence_composition(
        {"90260147": _LEFT, "90260148": right}, None
    )
    assert {e["code"] for e in result["claims"]["qty_differences"]} == {
        "10080031"
    }


def test_render_contains_ptbr_sections_and_verbatim_values():
    result = _verify_evidence_composition(_sources(), None)
    text = _render_evidence_comparison(result)
    assert "Componentes comuns" in text
    assert "Exclusivos de 90260147" in text
    assert "Exclusivos de 90260148" in text
    assert "50220014" in text and "50220015" in text


# --- Doc 228 §8: scoped entity-ref candidates — security/ambiguity ---
from app.domain.evidence.model import EntityRef as _ERef


class _RefTurn:
    def __init__(self, refs):
        self.entity_refs = refs


class _Goal:
    comparison_requested = True


def _orc():
    import app.application.capability_provision.orchestration as O
    o = object.__new__(O.OperationalCapabilityOrchestrator)
    return o


def test_session_refs_two_distinct_bind():
    refs = [
        _ERef("produto", "90260147", "delpi"),
        _ERef("produto", "90260148", "delpi"),
    ]
    out = _orc()._subobjectives_from_session_refs(
        (_RefTurn((refs[0],)), _RefTurn((refs[1],))), _Goal()
    )
    assert out is not None and len(out) == 2
    ids = {s.goal for s in out}
    assert ids == {"produto 90260147", "produto 90260148"}


def test_session_refs_ambiguous_three_returns_none():
    turns = (
        _RefTurn((_ERef("produto", "1", "delpi"),)),
        _RefTurn((_ERef("produto", "2", "delpi"),)),
        _RefTurn((_ERef("produto", "3", "delpi"),)),
    )
    assert _orc()._subobjectives_from_session_refs(turns, _Goal()) is None


def test_session_refs_forged_same_id_collapses():
    forged = (_RefTurn((_ERef("produto", "9", "delpi"),)),) * 3
    assert _orc()._subobjectives_from_session_refs(forged, _Goal()) is None


def test_session_refs_no_compare_goal_returns_none():
    class G:
        comparison_requested = False
    turns = (_RefTurn((_ERef("p", "1", "d"),)), _RefTurn((_ERef("p", "2", "d"),)))
    assert _orc()._subobjectives_from_session_refs(turns, G()) is None


def test_session_refs_empty_turns_returns_none():
    assert _orc()._subobjectives_from_session_refs((), _Goal()) is None
