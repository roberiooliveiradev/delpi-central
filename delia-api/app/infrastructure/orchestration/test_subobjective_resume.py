"""S5 — durable checkpoint/resume (doc 214 §8.3): real SqliteSaver
backed interruption → restart → resume on a fresh engine instance.
Proves committed subobjectives are not re-executed, threads are
isolated, authorization is revalidated on resume, expired budgets
close with honest gaps, and corrupted checkpoints fail closed."""

from __future__ import annotations

import sqlite3

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver

from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
)
from app.infrastructure.orchestration.langgraph_engine import (
    LangGraphCapabilityOrchestrator,
)
from tests.test_generic_multistep_orchestration import (
    FakeProvider,
    _cap,
    _group,
)
from tests.test_subobjective_fanout import (
    _cap_s,
    _engine_a,
)
from tests.test_subobjective_fanout import (
    _ErrorProvider as _FanErrorProvider,
)
from tests.test_subobjective_investigation import _decompose, _select


class _KillThenOk(FakeProvider):
    """First invoke raises a typed 'crash'; later calls succeed."""

    def __init__(self, provider_id, groups, kill_calls=1):
        super().__init__(provider_id, groups)
        self._kill_calls = kill_calls

    def invoke(
        self, capability, arguments, *, correlation_id, timeout_seconds=None
    ):
        self.calls.append((capability.remote_name, dict(arguments)))
        if len(self.calls) <= self._kill_calls:
            raise RuntimeError("simulated process kill")
        return super().invoke(
            capability,
            arguments,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )


def _engine(providers, proposal, saver):
    return LangGraphCapabilityOrchestrator(
        _engine_a(providers, proposal),
        subobjective_fanout_enabled=True,
        checkpointer=saver,
    )


def _saver(db_path):
    return SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))


def _thread_state(db_path, thread_id):
    ck = _saver(db_path).get_tuple(
        {"configurable": {"thread_id": thread_id}}
    )
    return ck.checkpoint.get("channel_values", {}) if ck else {}


def _two_sub_setup():
    caps1 = [_cap_s("g1", "p1", "r1")]
    caps2 = [_cap_s("g2", "p2", "r2")]
    proposal = [
        _select("g1", "r1", extra=_decompose(
            ("ler g1", (), ("a",)),
            ("ler g2", (0,), ("b",)),
        )),
        _select("g2", "r2"),
    ]
    return caps1, caps2, proposal


# ---------------- restart-resume: no duplicate committed work -----


def test_restart_resume_skips_committed_subobjective(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps1, caps2, proposal = _two_sub_setup()
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2 = _KillThenOk("p2", [_group("p2", "g2", caps2)])
    eng1 = _engine({"p1": p1, "p2": p2}, proposal, _saver(db))
    with pytest.raises(RuntimeError):
        eng1.attempt(
            "ler g1 e g2", correlation_id="c1",
            turn_deadline=None, thread_id="t-resume",
        )
    # committed durably before the crash
    cv = _thread_state(db, "t-resume")
    assert cv["sub_results"][0]["state"] == "COMPLETED"

    eng2 = _engine({"p1": p1, "p2": p2}, [_select("g2", "r2")],
                   _saver(db))
    att = eng2.attempt(
        "ler g1 e g2", correlation_id="c1",
        turn_deadline=None, thread_id="t-resume",
    )
    assert att.status is GovernedCapabilityStatus.SUCCESS
    assert len(p1.calls) == 1  # completed work never re-executed
    finals = _thread_state(db, "t-resume")["sub_results"]
    assert {r["subobjective_id"]: r["state"] for r in finals} == {
        "so_1": "COMPLETED",
        "so_2": "COMPLETED",
    }


# ---------------- isolation between threads -----------------------


def test_thread_isolation(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps = [_cap_s("g1", "p1", "r1")]
    proposal = [
        _select("g1", "r1", extra=_decompose(("ler g1", (), ("a",)))),
        _select("g1", "r1"),
    ]
    pa = FakeProvider("p1", [_group("p1", "g1", caps)])
    pb = FakeProvider("p1", [_group("p1", "g1", caps)])
    _engine({"p1": pa}, proposal, _saver(db)).attempt(
        "ler g1", correlation_id="cA", thread_id="thread-A",
    )
    _engine({"p1": pb}, proposal, _saver(db)).attempt(
        "ler g1", correlation_id="cB", thread_id="thread-B",
    )
    a = _thread_state(db, "thread-A")
    b = _thread_state(db, "thread-B")
    assert a["correlation"] == "cA"
    assert b["correlation"] == "cB"
    assert len(pa.calls) == len(pb.calls)


# ---------------- revoked authorization on resume -----------------


def test_revoked_authz_on_resume_blocks_branch(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps1, caps2, proposal = _two_sub_setup()
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2_kill = _KillThenOk("p2", [_group("p2", "g2", caps2)])
    eng1 = _engine({"p1": p1, "p2": p2_kill}, proposal, _saver(db))
    with pytest.raises(RuntimeError):
        eng1.attempt("ler g1 e g2", thread_id="t-authz")

    # Authorization revoked between crash and resume — the resumed
    # branch must be denied, never silently fall back.
    p2_denied = _FanErrorProvider(
        "p2",
        [_group("p2", "g2", caps2)],
        CapabilityProviderError(MCP_AUTHORIZATION_DENIED, "revoked"),
    )
    eng2 = _engine({"p1": p1, "p2": p2_denied},
                   [_select("g2", "r2")], _saver(db))
    att = eng2.attempt("ler g1 e g2", thread_id="t-authz")
    assert len(p1.calls) == 1
    denied = [
        r for r in _thread_state(db, "t-authz")["sub_results"]
        if r["subobjective_id"] == "so_2"
    ]
    assert denied and denied[-1]["state"] != "COMPLETED"


# ---------------- expired budget on resume ------------------------


def test_expired_budget_on_resume_closes_with_gap(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps1, caps2, proposal = _two_sub_setup()
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2 = _KillThenOk("p2", [_group("p2", "g2", caps2)])
    eng1 = _engine({"p1": p1, "p2": p2}, proposal, _saver(db))
    with pytest.raises(RuntimeError):
        eng1.attempt("ler g1 e g2", thread_id="t-expired")

    eng2 = _engine({"p1": p1, "p2": p2}, [_select("g2", "r2")],
                   _saver(db))
    att = eng2.attempt(
        "ler g1 e g2",
        turn_deadline=TurnDeadline.start(0.0),
        thread_id="t-expired",
    )
    # so_2 never ran a second provider call — the expired deadline
    # terminates the turn as PROCESSING_TIMEOUT; pending work is
    # never fabricated as completed.
    assert len(p2.calls) == 1
    assert att.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert not att.content


# ---------------- corrupted checkpoint → fail closed --------------


def test_corrupted_checkpoint_fails_closed(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps = [_cap_s("g1", "p1", "r1")]
    proposal = [
        _select("g1", "r1", extra=_decompose(("ler g1", (), ("a",)))),
        _select("g1", "r1"),
    ]
    p1 = FakeProvider("p1", [_group("p1", "g1", caps)])
    _engine({"p1": p1}, proposal, _saver(db)).attempt(
        "ler g1", thread_id="t-corrupt",
    )
    conn = sqlite3.connect(db)
    conn.execute(
        "UPDATE checkpoints SET checkpoint = ? WHERE thread_id = ?",
        (sqlite3.Binary(b"\x00" * 32), "t-corrupt"),
    )
    conn.commit()
    conn.close()

    calls_before = len(p1.calls)
    with pytest.raises(Exception):
        _engine({"p1": p1}, proposal, _saver(db)).attempt(
            "ler g1", thread_id="t-corrupt",
        )
    assert len(p1.calls) == calls_before  # fail closed pre-invoke


# ---------------- incompatible persisted version ------------------


def test_incompatible_checkpoint_version_fails_closed(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps = [_cap_s("g1", "p1", "r1")]
    proposal = [
        _select("g1", "r1", extra=_decompose(("ler g1", (), ("a",)))),
        _select("g1", "r1"),
    ]
    p1 = FakeProvider("p1", [_group("p1", "g1", caps)])
    _engine({"p1": p1}, proposal, _saver(db)).attempt(
        "ler g1", thread_id="t-ver",
    )
    saver = _saver(db)
    latest = saver.get_tuple({"configurable": {"thread_id": "t-ver"}})
    cfg = latest.config
    forged = dict(latest.checkpoint)
    forged["channel_values"] = dict(forged["channel_values"])
    forged["channel_values"]["state_version"] = "s5.v0"
    saver.put(cfg, forged, latest.metadata, {})

    calls_before = len(p1.calls)
    with pytest.raises(Exception):
        _engine({"p1": p1}, proposal, _saver(db)).attempt(
            "ler g1", thread_id="t-ver",
        )
    assert len(p1.calls) == calls_before  # fail closed pre-invoke


# ---------------- rollback to an earlier checkpoint ---------------


def test_rollback_restores_earlier_checkpoint(tmp_path):
    db = str(tmp_path / "ck.sqlite")
    caps1, caps2, proposal = _two_sub_setup()
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2 = _KillThenOk("p2", [_group("p2", "g2", caps2)])
    eng1 = _engine({"p1": p1, "p2": p2}, proposal, _saver(db))
    with pytest.raises(RuntimeError):
        eng1.attempt("ler g1 e g2", thread_id="t-rb")

    # Complete the investigation on a fresh engine.
    eng2 = _engine({"p1": p1, "p2": p2}, [_select("g2", "r2")],
                   _saver(db))
    att = eng2.attempt("ler g1 e g2", thread_id="t-rb")
    assert att.status is GovernedCapabilityStatus.SUCCESS
    history = list(
        _saver(db).list({"configurable": {"thread_id": "t-rb"}})
    )
    # Roll back to the earliest checkpoint that already carries the
    # plan but no committed results — the resumed run must then
    # re-execute from that point (so_1's provider runs again).
    earlier = next(
        t for t in reversed(history)
        if t.checkpoint["channel_values"].get("subobjectives")
        and not t.checkpoint["channel_values"].get("sub_results")
    )
    rolled = dict(earlier.checkpoint)
    # SqliteSaver picks the newest row by checkpoint_id DESC — a
    # lexically-later hex id lands the rollback at the head.
    rolled["id"] = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    cfg = earlier.config
    _saver(db).put(cfg, rolled, earlier.metadata, {})

    p1_before = len(p1.calls)
    eng3 = _engine(
        {"p1": p1, "p2": p2},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g2", (0,), ("b",)),
            )),
            _select("g1", "r1"),
            _select("g2", "r2"),
        ],
        _saver(db),
    )
    att3 = eng3.attempt("ler g1 e g2", thread_id="t-rb")
    assert att3.status is GovernedCapabilityStatus.SUCCESS
    assert len(p1.calls) > p1_before  # rolled-back work re-executed
