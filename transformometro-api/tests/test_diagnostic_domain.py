"""Diagnostic V1 — Domain Kernel invariants (pure domain, no persistence)."""

import pytest

from tm_app.domain.diagnostic.diagnostic import (
    CausalLink,
    CausalRelation,
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    DiagnosticError,
    EffectiveValidation,
    EpistemicState,
    EvidenceLink,
    EvidenceRelation,
    Finding,
    FindingRole,
    Hypothesis,
    ProblemStatement,
    Provenance,
    ProvenanceOrigin,
    RootCauseDesignation,
)


def _diagnostic(**kwargs) -> Diagnostic:
    kwargs.setdefault(
        "problem_statement",
        ProblemStatement(text="Atraso no fechamento"),
    )
    return Diagnostic(
        diagnostic_id="d1",
        revision_id="rev-1",
        **kwargs,
    )


def _finding(fid: str = "f1", **kwargs) -> Finding:
    return Finding(finding_id=fid, statement="Pedido trava no ERP", **kwargs)


def _hypothesis(hid: str = "h1", **kwargs) -> Hypothesis:
    return Hypothesis(hypothesis_id=hid, statement="Falta conferência", **kwargs)


def _conclusion(cid: str = "c1", **kwargs) -> DiagnosticConclusion:
    return DiagnosticConclusion(
        conclusion_id=cid, statement="Causa raiz identificada", **kwargs
    )


# 01 — create valid Diagnostic
def test_create_valid_diagnostic():
    d = _diagnostic()
    assert d.diagnostic_id == "d1"
    assert d.revision_id == "rev-1"
    assert d.problem_statement.text == "Atraso no fechamento"
    assert d.version == 1


# 02 — invalid/empty ProblemStatement
def test_invalid_problem_statement():
    with pytest.raises(DiagnosticError, match="invalid_problem_statement"):
        ProblemStatement(text="")
    with pytest.raises(DiagnosticError, match="invalid_problem_statement"):
        ProblemStatement(text="   ")
    with pytest.raises(DiagnosticError, match="invalid_problem_statement"):
        Diagnostic(
            diagnostic_id="d1",
            revision_id="rev-1",
            problem_statement=None,
        )


# 03 — duplicate Finding id
def test_duplicate_finding_id_rejected():
    d = _diagnostic()
    d.add_finding(_finding("f1"))
    with pytest.raises(DiagnosticError, match="duplicate_internal_identity"):
        d.add_finding(_finding("f1"))
    with pytest.raises(DiagnosticError, match="duplicate_internal_identity"):
        _diagnostic(findings=[_finding("f9"), _finding("f9")])


# 04 — duplicate Hypothesis id
def test_duplicate_hypothesis_id_rejected():
    d = _diagnostic()
    d.add_hypothesis(_hypothesis("h1"))
    with pytest.raises(DiagnosticError, match="duplicate_internal_identity"):
        d.add_hypothesis(_hypothesis("h1"))


# 05 / 06 — Finding OBSERVED / CALCULATED
def test_finding_observed_and_calculated():
    f_obs = _finding("f1", epistemic_state=EpistemicState.OBSERVED)
    f_calc = _finding("f2", epistemic_state=EpistemicState.CALCULATED)
    assert f_obs.epistemic_state is EpistemicState.OBSERVED
    assert f_calc.epistemic_state is EpistemicState.CALCULATED


# 07 — Finding INFERRED rejected
def test_finding_inferred_rejected():
    with pytest.raises(DiagnosticError, match="invalid_epistemic_state"):
        _finding(epistemic_state=EpistemicState.INFERRED)


# 08 — Hypothesis always INFERRED
def test_hypothesis_inferred():
    h = _hypothesis()
    assert h.epistemic_state.value == "INFERRED"


# 09 — wrong Hypothesis epistemic rejected
def test_hypothesis_wrong_epistemic_rejected():
    with pytest.raises(DiagnosticError, match="invalid_epistemic_state"):
        _hypothesis(epistemic_state=EpistemicState.OBSERVED)


# 10 — DRAFT → VALIDATED
def test_hypothesis_draft_to_validated():
    d = _diagnostic()
    d.add_hypothesis(_hypothesis("h1"))
    d.validate_hypothesis("h1")
    assert d.hypotheses[0].lifecycle is ClaimLifecycle.VALIDATED


# 11 — DRAFT → REJECTED
def test_hypothesis_draft_to_rejected():
    d = _diagnostic()
    d.add_hypothesis(_hypothesis("h1"))
    d.reject_hypothesis("h1")
    assert d.hypotheses[0].lifecycle is ClaimLifecycle.REJECTED


# 12 — VALIDATED → SUPERSEDED
def test_hypothesis_validated_to_superseded():
    d = _diagnostic()
    d.add_hypothesis(_hypothesis("h1"))
    d.validate_hypothesis("h1")
    d.supersede_hypothesis("h1")
    assert d.hypotheses[0].lifecycle is ClaimLifecycle.SUPERSEDED


# 13 — invalid lifecycle transition
def test_invalid_lifecycle_transition():
    d = _diagnostic()
    d.add_hypothesis(_hypothesis("h1"))
    with pytest.raises(DiagnosticError, match="invalid_lifecycle_transition"):
        d.supersede_hypothesis("h1")
    d.reject_hypothesis("h1")
    with pytest.raises(DiagnosticError, match="invalid_lifecycle_transition"):
        d.validate_hypothesis("h1")


# 14 — CONTRIBUTES_TO Hypothesis → Finding
def test_causal_link_hypothesis_to_finding():
    d = _diagnostic(findings=[_finding("f1")], hypotheses=[_hypothesis("h1")])
    link = CausalLink(link_id="l1", source_hypothesis_id="h1", target_id="f1")
    d.add_causal_link(link)
    assert d.causal_links[0].relation is CausalRelation.CONTRIBUTES_TO


# 15 — CONTRIBUTES_TO Hypothesis → Hypothesis
def test_causal_link_hypothesis_to_hypothesis():
    d = _diagnostic(hypotheses=[_hypothesis("h1"), _hypothesis("h2")])
    d.add_causal_link(
        CausalLink(link_id="l1", source_hypothesis_id="h1", target_id="h2")
    )
    assert len(d.causal_links) == 1


# 16 — invalid causal source
def test_causal_link_invalid_source():
    d = _diagnostic(findings=[_finding("f1")])
    with pytest.raises(DiagnosticError, match="invalid_causal_link"):
        d.add_causal_link(
            CausalLink(
                link_id="l1", source_hypothesis_id="h?", target_id="f1"
            )
        )


# 17 — invalid causal target / self-reference
def test_causal_link_invalid_target_and_self_reference():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    with pytest.raises(DiagnosticError, match="invalid_causal_link"):
        d.add_causal_link(
            CausalLink(
                link_id="l1", source_hypothesis_id="h1", target_id="f?"
            )
        )
    with pytest.raises(DiagnosticError, match="invalid_causal_link"):
        d.add_causal_link(
            CausalLink(
                link_id="l2", source_hypothesis_id="h1", target_id="h1"
            )
        )


# 18 — unsupported causal relation rejected
def test_causal_link_unsupported_relation():
    with pytest.raises(DiagnosticError, match="invalid_causal_link"):
        CausalLink(
            link_id="l1",
            source_hypothesis_id="h1",
            target_id="f1",
            relation="CAUSES",
        )


# 19/20/21 — Evidence relations
def test_evidence_relations():
    for relation in (
        EvidenceRelation.SUPPORTS,
        EvidenceRelation.CONTRADICTS,
        EvidenceRelation.CONTEXTUALIZES,
    ):
        link = EvidenceLink(link_id="e1", evidence_id="ev-1", relation=relation)
        assert link.relation is relation


# 22 — invalid Evidence relation
def test_invalid_evidence_relation():
    with pytest.raises(DiagnosticError, match="invalid_evidence_relation"):
        EvidenceLink(link_id="e1", evidence_id="ev-1", relation="PROVES")


# 23 — create draft conclusion
def test_create_draft_conclusion():
    d = _diagnostic()
    d.add_conclusion(_conclusion("c1"))
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.DRAFT
    assert d.diagnostic_conclusions[0].epistemic_state.value == "INFERRED"


# 24 — validate conclusion
def test_validate_conclusion():
    d = _diagnostic()
    d.add_conclusion(_conclusion("c1"))
    d.validate_conclusion("c1")
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.VALIDATED


# 25 — reject conclusion
def test_reject_conclusion():
    d = _diagnostic()
    d.add_conclusion(_conclusion("c1"))
    d.reject_conclusion("c1")
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.REJECTED


# 26 — supersede conclusion
def test_supersede_conclusion():
    d = _diagnostic()
    d.add_conclusion(_conclusion("c1"))
    d.validate_conclusion("c1")
    d.supersede_conclusion("c1")
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.SUPERSEDED


# 27 — second effective VALIDATED conclusion blocked
def test_second_validated_conclusion_blocked():
    d = _diagnostic()
    d.add_conclusion(_conclusion("c1"))
    d.add_conclusion(_conclusion("c2"))
    d.validate_conclusion("c1")
    with pytest.raises(DiagnosticError, match="effective_conclusion_conflict"):
        d.validate_conclusion("c2")
    d.supersede_conclusion("c1")
    d.validate_conclusion("c2")  # SUPERSEDED frees the slot


# 28 — valid RootCauseDesignation
def test_valid_root_cause_designation():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    d.validate_hypothesis("h1")
    d.add_conclusion(
        _conclusion(
            "c1",
            hypothesis_ids=("h1",),
            root_cause=RootCauseDesignation(hypothesis_id="h1"),
        )
    )
    d.validate_conclusion("c1")
    assert d.diagnostic_conclusions[0].root_cause.hypothesis_id == "h1"


# 29 — Root Cause → non-VALIDATED Hypothesis blocked at validation
def test_root_cause_non_validated_hypothesis_blocked():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    # A DRAFT conclusion may carry a proposed designation; the
    # VALIDATED+CURRENT rule is enforced when the conclusion is validated.
    d.add_conclusion(
        _conclusion(
            "c1",
            hypothesis_ids=("h1",),
            root_cause=RootCauseDesignation(hypothesis_id="h1"),
        )
    )
    with pytest.raises(
        DiagnosticError, match="invalid_root_cause_designation"
    ):
        d.validate_conclusion("c1")
    d.validate_hypothesis("h1")
    d.validate_conclusion("c1")


# 30 — Root Cause → STALE Hypothesis blocked
def test_root_cause_stale_hypothesis_blocked():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    d.validate_hypothesis("h1")
    d.mark_hypothesis_stale_evidence("h1")
    d.add_conclusion(
        _conclusion(
            "c1",
            hypothesis_ids=("h1",),
            root_cause=RootCauseDesignation(hypothesis_id="h1"),
        )
    )
    with pytest.raises(
        DiagnosticError, match="invalid_root_cause_designation"
    ):
        d.validate_conclusion("c1")


# 31 — historical VALIDATED lifecycle preserved when freshness goes stale
def test_historical_validated_preserved_when_stale():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    d.validate_hypothesis("h1")
    d.mark_hypothesis_stale_evidence("h1")
    h = d.hypotheses[0]
    assert h.lifecycle is ClaimLifecycle.VALIDATED
    assert h.effective_validation is EffectiveValidation.STALE_EVIDENCE
    assert h.epistemic_state.value == "INFERRED"
    assert h.validation_history[-1].to_lifecycle is ClaimLifecycle.VALIDATED


# 32/33 — provenance USER / TEO
def test_provenance_user_and_teo():
    p_user = Provenance(origin=ProvenanceOrigin.USER)
    p_teo = Provenance(origin=ProvenanceOrigin.TEO)
    assert p_user.origin is ProvenanceOrigin.USER
    assert p_teo.origin is ProvenanceOrigin.TEO
    f = _finding(provenance=p_teo)
    assert f.provenance.origin is ProvenanceOrigin.TEO


# 34 — TEO provenance does not imply authorization
def test_teo_provenance_not_authorization():
    p = Provenance(origin=ProvenanceOrigin.TEO)
    assert not hasattr(p, "permission")
    assert not hasattr(p, "authorized")
    assert not hasattr(p, "scope")
    assert not hasattr(p, "token")


# 35 — aggregate version valid
def test_aggregate_version_valid():
    d = _diagnostic(version=3)
    assert d.version == 3


# 36 — invalid version rejected
def test_invalid_version_rejected():
    for bad in (0, -1, "1", 1.5, True):
        with pytest.raises(DiagnosticError, match="invalid_version"):
            _diagnostic(version=bad)


# 37 — no hard-delete for validated material
def test_no_hard_delete_for_validated_material():
    d = _diagnostic(findings=[_finding("f1")], hypotheses=[_hypothesis("h1")])
    d.validate_hypothesis("h1")
    d.add_conclusion(_conclusion("c1"))
    d.validate_conclusion("c1")
    mutating = [
        name
        for name in dir(d)
        if name.startswith(("delete", "remove", "destroy"))
    ]
    assert mutating == []
    assert d.findings[0].finding_id == "f1"
    assert d.hypotheses[0].lifecycle is ClaimLifecycle.VALIDATED
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.VALIDATED


# extras — direct invariant proofs
def test_finding_symptom_role():
    f = _finding(role=FindingRole.SYMPTOM)
    assert f.role is FindingRole.SYMPTOM


def test_evidence_link_target_must_exist():
    d = _diagnostic(findings=[_finding("f1")])
    d.add_evidence_link(
        EvidenceLink(
            link_id="e1",
            evidence_id="ev-1",
            relation=EvidenceRelation.SUPPORTS,
            target_id="f1",
        )
    )
    with pytest.raises(DiagnosticError, match="invalid_evidence_relation"):
        d.add_evidence_link(
            EvidenceLink(
                link_id="e2",
                evidence_id="ev-2",
                relation=EvidenceRelation.CONTRADICTS,
                target_id="h?",
            )
        )


def test_conclusion_references_must_exist():
    d = _diagnostic()
    with pytest.raises(DiagnosticError):
        d.add_conclusion(_conclusion("c1", hypothesis_ids=["h?"]))
    with pytest.raises(DiagnosticError):
        d.add_conclusion(_conclusion("c2", finding_ids=["f?"]))


# ---------------------------------------------------------------------------
# Correction pass — aggregate encapsulation
# ---------------------------------------------------------------------------


def test_consumer_cannot_append_findings_directly():
    d = _diagnostic(findings=[_finding("f1")])
    with pytest.raises(AttributeError):
        d.findings.append(_finding("f2"))


def test_consumer_cannot_clear_or_pop_hypotheses():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    with pytest.raises(AttributeError):
        d.hypotheses.clear()
    with pytest.raises(AttributeError):
        d.hypotheses.pop()


def test_consumer_cannot_replace_collection_or_remove_validated_material():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    d.validate_hypothesis("h1")
    d.add_conclusion(_conclusion("c1"))
    d.validate_conclusion("c1")
    with pytest.raises(AttributeError):
        d.findings = []
    with pytest.raises(AttributeError):
        d.diagnostic_conclusions = []
    with pytest.raises(AttributeError):
        d.version = 9
    with pytest.raises(AttributeError):
        d.diagnostic_id = "other"
    # Read-only views still expose the material.
    assert d.hypotheses[0].lifecycle is ClaimLifecycle.VALIDATED
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.VALIDATED


def test_mutating_returned_tuple_does_not_touch_aggregate():
    d = _diagnostic(findings=[_finding("f1")])
    leaked = d.findings
    assert isinstance(leaked, tuple)
    leaked += (_finding("evil"),)
    assert len(d.findings) == 1


def test_stable_ids_cannot_be_reassigned():
    f = _finding("f1")
    h = _hypothesis("h1")
    c = _conclusion("c1")
    for entity, attr in (
        (f, "finding_id"),
        (h, "hypothesis_id"),
        (c, "conclusion_id"),
    ):
        with pytest.raises(AttributeError):
            setattr(entity, attr, "novo")


def test_epistemic_and_lifecycle_cannot_be_bypassed():
    h = _hypothesis("h1")
    c = _conclusion("c1")
    with pytest.raises(AttributeError):
        h.epistemic_state = EpistemicState.OBSERVED
    with pytest.raises(AttributeError):
        h.lifecycle = ClaimLifecycle.VALIDATED
    with pytest.raises(AttributeError):
        c.lifecycle = ClaimLifecycle.VALIDATED
    with pytest.raises(AttributeError):
        h.effective_validation = EffectiveValidation.STALE_EVIDENCE


def test_aggregate_can_still_mark_effective_validation():
    d = _diagnostic(hypotheses=[_hypothesis("h1")])
    d.mark_hypothesis_stale_evidence("h1")
    assert d.hypotheses[0].effective_validation is (
        EffectiveValidation.STALE_EVIDENCE
    )
    d.mark_hypothesis_revalidation_required("h1")
    assert d.hypotheses[0].effective_validation is (
        EffectiveValidation.REVALIDATION_REQUIRED
    )


# ---------------------------------------------------------------------------
# Correction pass — rehydration
# ---------------------------------------------------------------------------


def test_rehydrate_with_exactly_one_validated_conclusion():
    d = _diagnostic()
    d.add_conclusion(_conclusion("c1"))
    d.validate_conclusion("c1")
    rehydrated = _diagnostic(diagnostic_conclusions=list(d.diagnostic_conclusions))
    assert rehydrated.diagnostic_conclusions[0].lifecycle is (
        ClaimLifecycle.VALIDATED
    )


def test_rehydrate_with_two_validated_conclusions_fails():
    with pytest.raises(DiagnosticError, match="effective_conclusion_conflict"):
        _diagnostic(
            diagnostic_conclusions=[
                _conclusion("c1", lifecycle=ClaimLifecycle.VALIDATED),
                _conclusion("c2", lifecycle=ClaimLifecycle.VALIDATED),
            ]
        )


def test_superseded_then_validated_rehydrates():
    d = _diagnostic(
        diagnostic_conclusions=[
            _conclusion("c1", lifecycle=ClaimLifecycle.SUPERSEDED),
            _conclusion("c2", lifecycle=ClaimLifecycle.VALIDATED),
        ]
    )
    assert d.diagnostic_conclusions[1].lifecycle is ClaimLifecycle.VALIDATED


# ---------------------------------------------------------------------------
# Correction pass — problem statement canonical rule
# ---------------------------------------------------------------------------


def test_short_non_empty_problem_statement_accepted():
    ps = ProblemStatement(text="NC")
    assert ps.text == "NC"
    d = _diagnostic(problem_statement=ProblemStatement(text="NC"))
    assert d.problem_statement.text == "NC"


# ---------------------------------------------------------------------------
# Correction pass — root cause subset invariant
# ---------------------------------------------------------------------------


def test_root_cause_must_be_subset_of_conclusion_hypotheses():
    d = _diagnostic(hypotheses=[_hypothesis("h1"), _hypothesis("h2")])
    d.validate_hypothesis("h2")
    with pytest.raises(
        DiagnosticError, match="invalid_root_cause_designation"
    ):
        d.add_conclusion(
            _conclusion(
                "c1",
                hypothesis_ids=("h1",),
                root_cause=RootCauseDesignation(hypothesis_id="h2"),
            )
        )


# ---------------------------------------------------------------------------
# Final hardening — lifecycle injection via add_*
# ---------------------------------------------------------------------------


def test_add_hypothesis_blocks_lifecycle_injection():
    d = _diagnostic()
    for state in (
        ClaimLifecycle.VALIDATED,
        ClaimLifecycle.REJECTED,
        ClaimLifecycle.SUPERSEDED,
    ):
        with pytest.raises(
            DiagnosticError, match="invalid_lifecycle_transition"
        ):
            d.add_hypothesis(_hypothesis("h1", lifecycle=state))


def test_add_conclusion_blocks_lifecycle_injection():
    d = _diagnostic()
    for state in (
        ClaimLifecycle.VALIDATED,
        ClaimLifecycle.REJECTED,
        ClaimLifecycle.SUPERSEDED,
    ):
        with pytest.raises(
            DiagnosticError, match="invalid_lifecycle_transition"
        ):
            d.add_conclusion(_conclusion("c1", lifecycle=state))


def test_rehydrate_validated_hypothesis_remains_valid():
    d = _diagnostic(
        hypotheses=[_hypothesis("h1", lifecycle=ClaimLifecycle.VALIDATED)]
    )
    assert d.hypotheses[0].lifecycle is ClaimLifecycle.VALIDATED


def test_rehydrate_validated_conclusion_without_root_cause():
    d = _diagnostic(
        diagnostic_conclusions=[
            _conclusion("c1", lifecycle=ClaimLifecycle.VALIDATED)
        ]
    )
    assert d.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.VALIDATED


def test_rehydrate_validated_conclusion_with_draft_root_cause_fails():
    with pytest.raises(
        DiagnosticError, match="invalid_root_cause_designation"
    ):
        _diagnostic(
            hypotheses=[_hypothesis("h1", lifecycle=ClaimLifecycle.DRAFT)],
            diagnostic_conclusions=[
                _conclusion(
                    "c1",
                    lifecycle=ClaimLifecycle.VALIDATED,
                    hypothesis_ids=("h1",),
                    root_cause=RootCauseDesignation(hypothesis_id="h1"),
                )
            ],
        )


def test_rehydrate_validated_conclusion_with_stale_root_cause_fails():
    with pytest.raises(
        DiagnosticError, match="invalid_root_cause_designation"
    ):
        _diagnostic(
            hypotheses=[
                _hypothesis(
                    "h1",
                    lifecycle=ClaimLifecycle.VALIDATED,
                    effective_validation=EffectiveValidation.STALE_EVIDENCE,
                )
            ],
            diagnostic_conclusions=[
                _conclusion(
                    "c1",
                    lifecycle=ClaimLifecycle.VALIDATED,
                    hypothesis_ids=("h1",),
                    root_cause=RootCauseDesignation(hypothesis_id="h1"),
                )
            ],
        )


def test_rehydrate_validated_conclusion_with_valid_root_cause():
    d = _diagnostic(
        hypotheses=[
            _hypothesis(
                "h1",
                lifecycle=ClaimLifecycle.VALIDATED,
                effective_validation=EffectiveValidation.CURRENT,
            )
        ],
        diagnostic_conclusions=[
            _conclusion(
                "c1",
                lifecycle=ClaimLifecycle.VALIDATED,
                hypothesis_ids=("h1",),
                root_cause=RootCauseDesignation(hypothesis_id="h1"),
            )
        ],
    )
    assert d.diagnostic_conclusions[0].root_cause.hypothesis_id == "h1"


def test_problem_statement_trim_normalization():
    assert ProblemStatement(text="  NC  ").text == "NC"


def test_problem_statement_blank_remains_invalid():
    with pytest.raises(DiagnosticError, match="invalid_problem_statement"):
        ProblemStatement(text="   ")
