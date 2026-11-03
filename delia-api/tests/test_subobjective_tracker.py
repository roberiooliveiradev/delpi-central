"""S3 subobjective tracker — deterministic state machine tests."""

import pytest

from app.application.capability_provision.subobjective_tracker import (
    MAX_ATTEMPTS_PER_SUBOBJECTIVE,
    MAX_SUBOBJECTIVES_PER_INVESTIGATION,
    SubObjective,
    SubObjectiveTracker,
)


def _obj(oid, deps=(), **kw):
    return SubObjective(
        subobjective_id=oid,
        goal=f"goal-{oid}",
        dependencies=deps,
        **kw,
    )


def test_dependency_order_enforced():
    tracker = SubObjectiveTracker(
        (_obj("a"), _obj("b", deps=("a",)), _obj("c", deps=("b",)))
    )
    assert tracker.ready_ids() == ("a",)
    tracker.begin_attempt("a")
    tracker.complete("a", evidence_refs=("ref-1",))
    assert tracker.ready_ids() == ("b",)
    with pytest.raises(ValueError):
        tracker.begin_attempt("c")  # b not satisfied yet


def test_completed_requires_evidence():
    tracker = SubObjectiveTracker((_obj("a"),))
    tracker.begin_attempt("a")
    with pytest.raises(ValueError):
        tracker.complete("a", evidence_refs=())  # no evidence → no completion


def test_partial_records_gap_unblocks_dependent():
    tracker = SubObjectiveTracker((_obj("a"), _obj("b", deps=("a",))))
    tracker.begin_attempt("a")
    tracker.conclude_partial("a", gaps=("nonconformity source unavailable",))
    assert tracker.ready_ids() == ("b",)
    tracker.begin_attempt("b")
    tracker.complete("b", evidence_refs=("ref-b",))
    assert tracker.is_finished()
    assert tracker.coverage()["PARTIAL"] == 1
    assert tracker.coverage()["COMPLETED"] == 1


def test_attempt_cap_and_blocked_terminal():
    tracker = SubObjectiveTracker((_obj("a"),))
    for i in range(MAX_ATTEMPTS_PER_SUBOBJECTIVE):
        tracker.begin_attempt("a")
        tracker.fail("a", recoverable=True)
    # budget exhausted under failure → BLOCKED terminal
    assert tracker.get("a").state == "BLOCKED"
    with pytest.raises(ValueError):
        tracker.begin_attempt("a")


def test_nonrecoverable_fail_closes():
    tracker = SubObjectiveTracker((_obj("a"),))
    tracker.begin_attempt("a")
    tracker.fail("a", recoverable=False)
    assert tracker.get("a").state == "BLOCKED"
    assert tracker.is_finished()


def test_recoverable_fail_retries():
    tracker = SubObjectiveTracker((_obj("a"),))
    tracker.begin_attempt("a")
    tracker.fail("a", recoverable=True)
    assert tracker.get("a").state == "FAILED"
    assert tracker.retry_ready("a")
    tracker.begin_attempt("a")
    tracker.complete("a", evidence_refs=("ref",))


def test_progress_records_refs_and_gaps():
    tracker = SubObjectiveTracker((_obj("a"),))
    tracker.begin_attempt("a")
    obj = tracker.record_progress(
        "a", evidence_refs=("ref-1",), gaps=("missing denominator",)
    )
    assert obj.evidence_refs == ("ref-1",)
    assert obj.gaps == ("missing denominator",)


def test_invalid_construction():
    with pytest.raises(ValueError):
        SubObjectiveTracker((_obj("a"), _obj("a")))  # dup id
    with pytest.raises(ValueError):
        SubObjectiveTracker((_obj("a", deps=("missing",)),))  # unknown dep
    with pytest.raises(ValueError):
        SubObjectiveTracker((_obj("a", deps=("b",)), _obj("b")))  # fwd dep
    with pytest.raises(ValueError):
        SubObjectiveTracker(
            tuple(_obj(f"s{i}") for i in range(MAX_SUBOBJECTIVES_PER_INVESTIGATION + 1))
        )
    with pytest.raises(ValueError):
        SubObjective(subobjective_id="x", goal="g", state="COMPLETED")  # no evidence
    with pytest.raises(ValueError):
        SubObjective(subobjective_id="x", goal="g", state="INVENTED")


def test_investigation_attempt_cap():
    tracker = SubObjectiveTracker((_obj("a"), _obj("b")), investigation_attempt_cap=1)
    tracker.begin_attempt("a")
    tracker.fail("a", recoverable=True)
    with pytest.raises(ValueError):
        tracker.begin_attempt("b")  # investigation cap spent


def test_terminal_states_is_finished():
    tracker = SubObjectiveTracker((_obj("a"), _obj("b")))
    tracker.begin_attempt("a")
    tracker.complete("a", evidence_refs=("r",))
    tracker.begin_attempt("b")
    tracker.fail("b", recoverable=False)
    assert tracker.is_finished()
    cov = tracker.coverage()
    assert cov["COMPLETED"] == 1 and cov["BLOCKED"] == 1
