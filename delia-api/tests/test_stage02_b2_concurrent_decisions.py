"""B2 RW-01 — two simultaneous typed decisions claim one PendingWrite.

No live owner or business write: FakeProvider records governed ACT.
The barrier intentionally forces both requests to observe the SAME
pending proposal before either tries to consume it, reproducing the
interleaving from independent review §6.186.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.pending_proposals import (
    PendingWriteStore,
)
from test_stage02r2_execution_bound_diagnosis import (
    _apply,
    _direct_write_provider,
    _orchestrator,
    _stage_select,
)


def _prepared_race():
    provider = _direct_write_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select(
            {
                "goal_class": "create_or_modify",
                "execution_bound": "unrestricted",
            }
        ),
    )
    result = orch.attempt(
        "Crie o cadastro X.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert result.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    assert not any(name == "commit_record" for name, _ in provider.calls)
    return provider, orch, dict(result.confirmation_context or {})


def _align_initial_reads(orch):
    store = orch._pending_writes
    original_get = store.get
    barrier = Barrier(2, timeout=6)

    def both_read_first(digest):
        record = original_get(digest)
        if record is not None:
            barrier.wait()
        return record

    store.get = both_read_first


@pytest.mark.parametrize(
    "decisions",
    [
        ("CONFIRM", "CONFIRM"),
        ("CONFIRM", "REJECT"),
        ("REJECT", "CONFIRM"),
    ],
)
def test_two_simultaneous_decisions_have_only_one_winner(decisions):
    provider, orch, ctx = _prepared_race()
    _align_initial_reads(orch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_a = pool.submit(
            _apply, orch, ctx, "u1", "s1", decisions[0]
        )
        future_b = pool.submit(
            _apply, orch, ctx, "u1", "s1", decisions[1]
        )
        outcomes = [future_a.result(timeout=12), future_b.result(timeout=12)]

    owner_acts = sum(
        name == "commit_record" for name, _ in provider.calls
    )
    assert owner_acts <= 1
    assert sum(
        o.status is GovernedCapabilityStatus.SUCCESS for o in outcomes
    ) == owner_acts
    assert sum(
        o.error_code == "confirmation_unknown" for o in outcomes
    ) == 1
    # Replay is rejected after the winning confirmation/rejection.
    retry = _apply(orch, ctx)
    assert retry.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert retry.error_code == "confirmation_unknown"


def test_stale_record_cannot_claim_or_delete_replaced_pending():
    provider, orch, ctx = _prepared_race()
    store: PendingWriteStore = orch._pending_writes
    digest = ctx["proposal_digest"]
    stale = store.get(digest)
    assert stale is not None
    replacement = replace(stale, correlation_id="new-prepare")
    store.put(replacement)

    # CAS identity check prevents consuming a newer record with the
    # same digest, even if the older record passed binding earlier.
    assert store.take_if_current(digest, stale) is None
    assert store.get(digest) is replacement
    assert store.take_if_current(digest, replacement) is replacement
    assert store.take_if_current(digest, replacement) is None
    assert not any(name == "commit_record" for name, _ in provider.calls)
