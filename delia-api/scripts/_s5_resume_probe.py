#!/usr/bin/env python3
"""S5 probe — durable checkpoint/resume for the fan-out engine.

Simulates interrupt -> process restart -> resume:
  phase 1: graph with SqliteSaver runs; provider raises a typed kill
           mid-investigation (after so_1 completes).
  phase 2: fresh engine instance over the SAME sqlite file resumes
           the same thread_id; asserts completed branches were NOT
           re-invoked (provider call counts).
"""
import os
import sys
import tempfile

sys.path.insert(0, "/app")

from tests.test_subobjective_fanout import _engine_a
from tests.test_generic_multistep_orchestration import (
    FakeProvider,
    _cap,
    _group,
)
from tests.test_subobjective_investigation import _decompose, _select
from app.domain.specialist_interop.model import SpecialistOperationClass
from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.specialist_interop.errors import MCP_UNAVAILABLE
from app.infrastructure.orchestration.langgraph_engine import (
    LangGraphCapabilityOrchestrator,
)


class _KillThenOk(FakeProvider):
    """First call raises a typed 'crash'; later calls succeed."""

    def __init__(self, provider_id, groups, kill_calls=1):
        super().__init__(provider_id, groups)
        self._kill_calls = kill_calls

    def invoke(self, capability, arguments, *, correlation_id, timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        if len(self.calls) <= self._kill_calls:
            raise RuntimeError("simulated process kill")
        return super().invoke(
            capability, arguments, correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )


def build(db_path, providers, proposal, shared_providers):
    from langgraph.checkpoint.sqlite import SqliteSaver
    import sqlite3

    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    engine = LangGraphCapabilityOrchestrator(
        _engine_a(providers, proposal),
        subobjective_fanout_enabled=True,
        checkpointer=saver,
    )
    return engine


def main():
    db = tempfile.mktemp(suffix=".sqlite")
    caps1 = [_cap("g1", "p1", "r1", SpecialistOperationClass.READ)]
    caps2 = [_cap("g2", "p2", "r2", SpecialistOperationClass.READ)]
    proposal = [
        _select("g1", "r1", extra=_decompose(
            ("ler g1", (), ("a",)),
            ("ler g2", (0,), ("b",)),
        )),
        _select("g2", "r2"),
    ]
    # phase 1 — crash mid-run
    p1 = FakeProvider("p1", [_group("p1", "g1", caps1)])
    p2 = _KillThenOk("p2", [_group("p2", "g2", caps2)], kill_calls=1)
    eng1 = build(db, {"p1": p1, "p2": p2}, proposal, None)
    thread = "probe-investigation-1"
    try:
        eng1.attempt("ler g1 e g2", correlation_id="c1", turn_deadline=None,
                     thread_id=thread)
        print("PHASE1: completed without crash")
    except Exception as e:
        print("PHASE1 crash:", type(e).__name__, str(e)[:120])
    # phase 2 — resume on fresh instance
    from langgraph.checkpoint.sqlite import SqliteSaver
    import sqlite3
    conn = sqlite3.connect(db, check_same_thread=False)
    ck = SqliteSaver(conn).get_tuple(
        {"configurable": {"thread_id": thread}})
    if ck is not None:
        cv = ck.checkpoint.get("channel_values", {})
        print("CK deadline_data:", cv.get("deadline_data"))
        print("CK sub_results:", cv.get("sub_results"))
        print("CK subobjectives:", cv.get("subobjectives"))
    eng2 = build(db, {"p1": p1, "p2": p2},
                 [_select("g2", "r2")], None)
    try:
        att = eng2.attempt("ler g1 e g2", correlation_id="c1", turn_deadline=None,
                           thread_id=thread)
        print("PHASE2 status:", att.status, "content?", bool(att.content))
        print("PHASE2 trace:", eng2.last_node_trace)
        ck2 = SqliteSaver(sqlite3.connect(db, check_same_thread=False)
                          ).get_tuple({"configurable": {"thread_id": thread}})
        if ck2 is not None:
            cv2 = ck2.checkpoint.get("channel_values", {})
            for r in cv2.get("sub_results") or []:
                print("FINAL sub_result:", r["subobjective_id"], r["state"],
                      r.get("attempt_status"), "gaps=", r.get("gaps"))
    except Exception as e:
        print("PHASE2 raise:", type(e).__name__, str(e)[:200])
    print("p1.calls", len(p1.calls), "p2.calls", len(p2.calls))
    # Contract: durably-completed so_1 must NOT be re-invoked
    # (p1.calls stays 1); so_2 was never committed, so governed
    # re-execution (incl. retry of the killed call) is legitimate.
    ok = len(p1.calls) == 1 and len(p2.calls) >= 2
    print("RESUME_NO_DUPLICATE:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
