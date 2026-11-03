"""S6 — evidence coverage and grounded synthesis (doc 214 §9):
each subobjective's result is classified as
sufficient/partial/unsupported/absent/contradictory and the final
synthesis reflects only what the evidence supports — gaps,
contradictions and unsupported claims are explicit limitations,
never silently reconciled."""

from __future__ import annotations

from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.specialist_interop.errors import MCP_UNAVAILABLE
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from tests.test_generic_multistep_orchestration import (
    FakeProvider,
    _cap,
    _group,
)
from tests.test_subobjective_fanout import (
    _cap_s,
    _engine,
)
from tests.test_subobjective_fanout import (
    _ErrorProvider as _FanErrorProvider,
)
from tests.test_subobjective_investigation import _decompose, _select


def _outcome(group_id, remote, **kw):
    return SpecialistOutcome(
        status=kw.pop("status", SpecialistResultStatus.COMPLETED),
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=kw.pop("content_text", "ok"),
        **kw,
    )


# ---------------- complete evidence -------------------------------


def test_complete_evidence_sufficient_no_gap_notes():
    p1 = FakeProvider("p1", [_group("p1", "g1", [_cap_s("g1", "p1", "r1")])])
    eng = _engine(
        {"p1": p1},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g1b", (0,), ("b",)),
            )),
            _select("g1", "r1"),
            _select("g1", "r1"),
        ],
    )
    att = eng.attempt("ler g1")
    assert att.status is GovernedCapabilityStatus.SUCCESS
    assert not any("unsupported" in lim for lim in att.limitations)


# ---------------- partial evidence ---------------------------------


def test_incomplete_outcome_is_partial_not_sufficient():
    caps = [_cap_s("g1", "p1", "r1")]
    p1 = FakeProvider(
        "p1",
        [_group("p1", "g1", caps)],
        outcomes={
            ("g1", "r1"): _outcome("g1", "r1", is_complete=False),
        },
    )
    eng = _engine(
        {"p1": p1},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g1b", (0,), ("b",)),
            )),
            _select("g1", "r1"),
            _select("g1", "r1"),
        ],
    )
    att = eng.attempt("ler g1")
    assert any(
        "partial" in lim and "so_1" in lim for lim in att.limitations
    )


# ---------------- declared contradiction ---------------------------


def test_declared_contradiction_is_reported_not_reconciled():
    caps = [_cap_s("g1", "p1", "r1")]
    p1 = FakeProvider(
        "p1",
        [_group("p1", "g1", caps)],
        outcomes={
            ("g1", "r1"): _outcome(
                "g1", "r1",
                structured={"contradictions": ["src-A vs src-B"]},
            ),
        },
    )
    eng = _engine(
        {"p1": p1},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g1b", (0,), ("b",)),
            )),
            _select("g1", "r1"),
            _select("g1", "r1"),
        ],
    )
    att = eng.attempt("ler g1")
    assert any(
        "contradictory" in lim and "so_1" in lim
        for lim in att.limitations
    )


# ---------------- period conflict on shared evidence need ---------
# exercised directly on the synthesis node so the conflict rule is
# tested deterministically against committed records.


def test_period_conflict_across_complementary_owners():
    from app.application.capability_provision.subobjective_tracker import (
        SubObjective,
    )

    eng = _engine({"p1": FakeProvider("p1", [])}, [
        _select("g1", "r1", extra=_decompose(("ler g1", (), ("a",)))),
    ])
    objectives = (
        SubObjective(
            subobjective_id="so_1", goal="vendas",
            dependencies=(), evidence_needed=("vendas",),
        ),
        SubObjective(
            subobjective_id="so_2", goal="vendas",
            dependencies=(), evidence_needed=("vendas",),
        ),
    )
    results = [
        {
            "subobjective_id": "so_1", "goal": "vendas",
            "state": "COMPLETED", "attempt_status": "SUCCESS",
            "content": "vendas 100", "limitations": [],
            "evidence_refs": ["g1.r1"], "gaps": [],
            "is_complete": True, "contradictions": [],
            "period": "2026-Q1", "scope": None, "unit": None,
        },
        {
            "subobjective_id": "so_2", "goal": "vendas",
            "state": "COMPLETED", "attempt_status": "SUCCESS",
            "content": "vendas 120", "limitations": [],
            "evidence_refs": ["g2.r2"], "gaps": [],
            "is_complete": True, "contradictions": [],
            "period": "2026-Q2", "scope": None, "unit": None,
        },
    ]
    out = eng._subobjective_synthesis_node({
        "subobjectives": objectives,
        "sub_results": results,
        "correlation": "c",
        "deadline_data": {
            "ends_at_epoch": 9999999999.0,
        },
    })
    att = out["attempt"]
    assert att.status is GovernedCapabilityStatus.SUCCESS
    assert any(
        "period conflict" in lim for lim in att.limitations
    )
    assert out["evidence_coverage"] == {
        "so_1": "contradictory",
        "so_2": "contradictory",
    }


# ---------------- complementary owners, no conflict ----------------


def test_complementary_evidence_synthesizes_without_conflict():
    caps1 = [_cap_s("g1", "p1", "r1")]
    caps2 = [_cap_s("g2", "p2", "r2")]
    p1 = FakeProvider(
        "p1",
        [_group("p1", "g1", caps1)],
        outcomes={
            ("g1", "r1"): _outcome(
                "g1", "r1",
                content_text="vendas total 100",
            ),
        },
    )
    p2 = FakeProvider(
        "p2",
        [_group("p2", "g2", caps2)],
        outcomes={
            ("g2", "r2"): _outcome(
                "g2", "r2",
                content_text="recebiveis total 40",
            ),
        },
    )
    eng = _engine(
        {"p1": p1, "p2": p2},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler vendas", (), ("v",)),
                ("ler recebiveis", (0,), ("r",)),
            )),
            _select("g2", "r2"),
        ],
    )
    att = eng.attempt("ler vendas e recebiveis")
    assert att.status is GovernedCapabilityStatus.SUCCESS
    assert "vendas total 100" in att.content
    assert "recebiveis total 40" in att.content
    assert not any("conflict" in lim for lim in att.limitations)


# ---------------- owner unavailable after others complete ---------


def test_owner_unavailable_keeps_partial_grounded_result():
    caps1 = [_cap_s("g1", "p1", "r1")]
    caps2 = [_cap_s("g2", "p2", "r2")]
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2 = _FanErrorProvider(
        "p2",
        [_group("p2", "g2", caps2)],
        CapabilityProviderError(MCP_UNAVAILABLE, "owner 503"),
    )
    eng = _engine(
        {"p1": p1, "p2": p2},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g2", (0,), ("b",)),
            )),
            _select("g2", "r2"),
        ],
    )
    att = eng.attempt("ler g1 e g2")
    # so_1 evidence is preserved; so_2 is a declared gap, never a
    # fabricated completion.
    assert att.status is GovernedCapabilityStatus.SUCCESS
    assert att.content
    assert any("so_2" in lim for lim in att.limitations)


# ---------------- empty authoritative result -----------------------


def test_empty_result_is_gap_not_business_fact():
    caps = [_cap_s("g1", "p1", "r1")]
    p1 = FakeProvider(
        "p1",
        [_group("p1", "g1", caps)],
        outcomes={("g1", "r1"): _outcome("g1", "r1", content_text="")},
    )
    eng = _engine(
        {"p1": p1},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g1b", (0,), ("b",)),
            )),
            _select("g1", "r1"),
            _select("g1", "r1"),
        ],
    )
    att = eng.attempt("ler g1")
    # The render layer surfaces the empty result truthfully — the
    # synthesis carries it as an observed "empty result", never as a
    # business fact.
    assert "resultado vazio" in att.content
