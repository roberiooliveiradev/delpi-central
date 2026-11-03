"""S2–S6 cross proof (doc 214 §4): ONE compound investigation that
exercises the full chain end-to-end — semantic decomposition (S3),
dependency-aware parallel fan-out (S4), durable checkpoint +
fresh-instance resume (S5) and coverage-aware grounded synthesis
(S6) — through the real governed path, never isolated mocks."""

from __future__ import annotations

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.specialist_interop.errors import MCP_UNAVAILABLE
from app.infrastructure.orchestration.langgraph_engine import (
    LangGraphCapabilityOrchestrator,
)
from tests.test_generic_multistep_orchestration import (
    FakeProvider,
    _group,
)
from tests.test_subobjective_fanout import _cap_s, _engine_a
from tests.test_subobjective_fanout import (
    _ErrorProvider as _FanErrorProvider,
)
from tests.test_subobjective_investigation import _decompose, _select
from tests.test_subobjective_resume import _KillThenOk


def _engine(providers, proposal, saver):
    return LangGraphCapabilityOrchestrator(
        _engine_a(providers, proposal),
        subobjective_fanout_enabled=True,
        checkpointer=saver,
    )


def _saver(db_path):
    return SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))


def _state(db_path, thread_id):
    ck = _saver(db_path).get_tuple(
        {"configurable": {"thread_id": thread_id}}
    )
    return ck.checkpoint.get("channel_values", {}) if ck else {}


def test_full_chain_compound_investigation_resume_and_coverage(
    tmp_path,
):
    """Three subobjectives: so_1+so_2 independent (same wave), so_3
    dependent. Provider for so_3 crashes mid-run — a fresh engine
    instance resumes, committed so_1/so_2 are never re-executed,
    so_3 completes, and synthesis reports per-subobjective
    coverage including the so_2 unavailability gap."""
    db = str(tmp_path / "ck.sqlite")
    caps1 = [_cap_s("g1", "p1", "r1")]
    caps2 = [_cap_s("g2", "p2", "r2")]
    caps3 = [_cap_s("g3", "p3", "r3")]
    # p2 unavailable the whole investigation; p3 killed once so the
    # crash lands after the independent wave committed.
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2 = _FanErrorProvider(
        "p2",
        [_group("p2", "g2", caps2)],
        CapabilityProviderError(MCP_UNAVAILABLE, "owner 503"),
    )
    p3 = _KillThenOk("p3", [_group("p3", "g3", caps3)])
    providers = {"p1": p1, "p2": p2, "p3": p3}
    proposal = [
        _select("g1", "r1", extra=_decompose(
            ("ler g1", (), ("a",)),
            ("ler g2", (), ("b",)),
            ("ler g3", (0, 1), ("c",)),
        )),
        _select("g2", "r2"),
        _select("g3", "r3"),
    ]
    eng1 = _engine(providers, proposal, _saver(db))
    crashed = False
    try:
        att = eng1.attempt(
            "investigue g1, g2 e g3", thread_id="t-integ",
        )
    except RuntimeError:
        crashed = True
    assert crashed  # the so_3 kill must interrupt the investigation
    # phase-2 fresh instance resumes the same thread
    eng2 = _engine(
        providers,
        [_select("g3", "r3")],
        _saver(db),
    )
    att = eng2.attempt(
        "investigue g1, g2 e g3", thread_id="t-integ",
    )

    # so_1 evidence preserved; so_3 eventually completed; so_1's
    # provider was never re-invoked after its durable commit.
    assert att.status is GovernedCapabilityStatus.SUCCESS
    assert att.content
    assert len(p1.calls) == 1
    finals = {
        r["subobjective_id"]: r["state"]
        for r in _state(db, "t-integ")["sub_results"]
    }
    assert finals.get("so_1") == "COMPLETED"
    assert finals.get("so_3") == "COMPLETED"
    assert finals.get("so_2") != "COMPLETED"
    # S6 coverage: so_2's owner outage is an explicit declared gap,
    # never a fabricated completion.
    assert any("so_2" in lim for lim in att.limitations)
    coverage = _state(db, "t-integ").get("evidence_coverage") or {}
    assert coverage.get("so_1") == "sufficient"
    assert coverage.get("so_3") == "sufficient"
    assert coverage.get("so_2") != "sufficient"
