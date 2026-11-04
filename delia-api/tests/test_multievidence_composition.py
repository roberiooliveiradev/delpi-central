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


def test_client_carried_two_distinct_refs_do_not_auto_bind():
    # Even two distinct well-formed refs may be client-forged; neither
    # DELIA_RESULT labeling nor a successful READ attests prior-turn origin.
    refs = (
        _ERef("produto", "90260147", "delpi"),
        _ERef("produto", "90260148", "delpi"),
    )
    turns = (_RefTurn((refs[0],)), _RefTurn((refs[1],)))
    assert _orc()._subobjectives_from_session_refs(turns, _Goal()) is None


def test_client_forged_two_distinct_refs_do_not_trigger_reads():
    forged = (
        _RefTurn((_ERef("qualquer", "forged-A", "other-owner"),)),
        _RefTurn((_ERef("qualquer", "forged-B", "other-owner"),)),
    )
    assert _orc()._subobjectives_from_session_refs(forged, _Goal()) is None


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


# --- E4-R6: cold single-turn comparison decomposes after fused goal ---

def _nested_tree(root, children):
    return {
        "items": [
            {
                "code": root,
                "quantity": 1,
                "unit": "MI",
                "type": "PA",
                "components": children,
            }
        ]
    }


_TREE_A = _nested_tree(
    "90260147",
    [
        {
            "code": "50220013",
            "quantity": 2,
            "unit": "MI",
            "type": "PI",
            "components": [
                {"code": "10030015", "quantity": 368, "unit": "MT"},
                {"code": "10080031", "quantity": 1000, "unit": "PC"},
            ],
        },
        {
            "code": "50220014",
            "quantity": 2,
            "unit": "MI",
            "type": "PI",
            "components": [
                {"code": "10030019", "quantity": 318, "unit": "MT"},
            ],
        },
    ],
)
_TREE_B = _nested_tree(
    "90260148",
    [
        {
            "code": "50220013",
            "quantity": 2,
            "unit": "MI",
            "type": "PI",
            "components": [
                {"code": "10030015", "quantity": 368, "unit": "MT"},
                {"code": "10080031", "quantity": 1000, "unit": "PC"},
            ],
        },
        {
            "code": "50220015",
            "quantity": 2,
            "unit": "MI",
            "type": "PI",
            "components": [
                {"code": "10030012", "quantity": 318, "unit": "MT"},
            ],
        },
    ],
)


def test_cold_single_turn_comparison_reaches_verified_fan_in():
    """R6 regression: with no prior_turns the goal binds only inside
    ``_select_target``'s fused interpretation — the early decompose
    gate saw ``goal=None`` and the turn fell into the foreign
    corroborate route instead of two governed READs. The post-binding
    gate must run the same decompose+investigate path and surface a
    ``VerifiedCompositeEvidence`` with both real roots."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        EVIDENCE_COMPOSITION_INSTRUCTION_ID,
        GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
        GROUP_SELECTION_INSTRUCTION_ID,
        OperationalCapabilityOrchestrator,
        SUBOBJECTIVES_INSTRUCTION_ID,
    )
    from app.application.interaction.capability_attempt import (
        GovernedCapabilityStatus,
    )
    from app.application.model_invocation.contracts import (
        ProviderInvocationPayload,
    )
    from app.application.model_invocation.invoke_model import InvokeModel
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOperationClass,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )
    from tests.test_subobjective_investigation import (
        _SUBOBJECTIVES_INSTRUCTION,
        FakeProposalModel,
        FakeProvider,
        _cap,
        _group,
    )

    def _tree_outcome(structured, correlation="c"):
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id="davi",
                remote_name="read_tree",
                protocol=InteropProtocol.MCP,
                correlation_id=correlation,
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="tree",
            structured=structured,
        )

    class _SeqProvider(FakeProvider):
        def __init__(self, provider_id, groups, outcomes_seq):
            super().__init__(provider_id, groups)
            self._seq = list(outcomes_seq)

        def invoke(
            self, capability, arguments, *, correlation_id,
            timeout_seconds=None,
        ):
            self.calls.append((capability.remote_name, dict(arguments)))
            return self._seq.pop(0)

    provider = _SeqProvider(
        "p1",
        [
            _group(
                "p1",
                "davi",
                [
                    _cap(
                        "davi",
                        "p1",
                        "read_tree",
                        SpecialistOperationClass.READ,
                        schema={"type": "object", "properties": {}},
                    )
                ],
            )
        ],
        [_tree_outcome(_TREE_A), _tree_outcome(_TREE_B)],
    )
    proposal = [
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "p1:davi",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "read_tree",
                "goal_class": "compare",
                "comparison_requested": True,
            },
        },
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "read_tree",
                "goal_class": "read",
            },
            SUBOBJECTIVES_INSTRUCTION_ID: {
                "subobjectives": [
                    {
                        "goal": "ler estrutura do produto 90260147",
                        "depends_on": [],
                        "evidence_needed": ["estrutura 90260147"],
                    },
                    {
                        "goal": "ler estrutura do produto 90260148",
                        "depends_on": [],
                        "evidence_needed": ["estrutura 90260148"],
                    },
                ]
            },
        },
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "read_tree",
                "goal_class": "read",
            },
        },
        {
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
            GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                "correspondence": "corresponds",
            },
            EVIDENCE_COMPOSITION_INSTRUCTION_ID: {
                "proposed_pairs": [],
                "limitations": [],
            },
        },
    ]
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=__import__(
            "tests.test_subobjective_investigation",
            fromlist=["TEST_MODEL_REF"],
        ).TEST_MODEL_REF,
        orchestration_instructions={
            SUBOBJECTIVES_INSTRUCTION_ID: _SUBOBJECTIVES_INSTRUCTION,
            EVIDENCE_COMPOSITION_INSTRUCTION_ID: "x",
        },
    )
    attempt = orch.attempt(
        "compare as estruturas 90260147 e 90260148",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    verified = attempt.verified_composition
    assert verified is not None
    assert set(verified.source_roots) == {"90260147", "90260148"}
    assert verified.verdict == "differences_found"
    assert len(provider.calls) == 2
