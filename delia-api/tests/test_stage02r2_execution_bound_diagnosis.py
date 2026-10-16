"""Stage-02R2/B2 execution-scope contract verification (§§6.176-6.184).

Originally a diagnostic suite proving the B2 residual: the runtime
honored textual "não aplique" only when the model emitted
``execution_bound="prepare_only"``, and a misclassified/absent/invalid
bound silently reached governed direct ACT. After the architecture
closure (doc 18 / §6.184) this file verifies the CONTRACT, not the
defect:

- A free-text MESSAGE can never reach material ACT — the governed chain
  caps at PREPARE + a backend pending write, whatever the model
  proposes (``unrestricted``, absent, invalid — all carry no
  permissive value).
- ACT requires a separate typed decision command bound to the exact
  pending proposal (digest/fingerprint/session/actor), reusing the
  structured confirmation machinery — ``APPLY_PREPARED`` for CONFIRM,
  ``REJECT_PREPARED`` for REJECT. The owner confirmation policy keeps
  its own meaning: ``explicit_user_confirmation=false`` still needs the
  user execution-scope choice; ``true`` makes the same bound choice
  satisfy the owner confirmation too.
- ACT-only capabilities without a verifiable owner PREPARE proposal
  are refused truthfully — the runtime must not fabricate a preview.

Harness: scripted FakeProposalModel/FakeProvider — no real LLM, no real
write, provider-neutral fictitious owners only.
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.orchestration import (
    GOAL_INSTRUCTION_ID,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
)

from test_conversational_intelligence_baseline import (
    _cap,
    _group,
    _outcome,
    _orchestrator,
    _process_provider,
    _select,
    FakeProvider,
)

_STAGE_ARGS = {
    "entity": "process",
    "operation": "create",
    "changes": {"nome_processo": "x", "status_processo": "ativo"},
}


def _direct_write_provider():
    """Owner with DISCOVERY + PREPARE(READY, confirmation=False) + ACT."""
    return _process_provider(
        commit_outcome=_outcome(
            "registry",
            "commit_record",
            "created",
            structured={"data": {"record_id": "R-1"}},
        )
    )


def _stage_select(goal_payload=None):
    extra = (
        {GOAL_INSTRUCTION_ID: goal_payload} if goal_payload else None
    )
    return _select(
        "registry", "stage_record", arguments=_STAGE_ARGS, extra=extra
    )


def _called_names(provider):
    return [name for name, _ in provider.calls]


def _apply(orch, pending_ctx, actor="u1", session="s1", decision="CONFIRM"):
    """Typed decision turn bound to the pending proposal (APPLY/REJECT).

    The wire layer maps ``confirmation.decision=CONFIRM`` to
    APPLY_PREPARED and ``REJECT`` to REJECT_PREPARED; at the orchestration
    boundary the bound digests alone carry the decision.
    """
    return orch.attempt(
        "",
        actor_user_id=actor,
        session_id=session,
        confirmation={
            "proposal_digest": pending_ctx["proposal_digest"],
            "session_id": pending_ctx["session_id"],
            "preview_fingerprint": pending_ctx["preview_fingerprint"],
            "decision": decision,
        },
    )


# --- B2-DIAG-01: explicit contradiction ---------------------------------


def test_b2diag01_textual_bound_vs_unrestricted_proposal():
    """'Prepare um cadastro, mas não aplique.' + model proposal
    goal_class=create_or_modify, execution_bound='unrestricted',
    request ceiling None, owner READY/direct, ACT available.

    CONTRACT (§6.184 D1/D3): a free-text MESSAGE is never ACT-eligible —
    the model bound carries no permissive value. Expected: PREPARE +
    pending execution-scope choice, zero ACT."""
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
    attempt = orch.attempt(
        "Prepare um cadastro, mas não aplique.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    ctx = dict(attempt.confirmation_context or {})
    assert ctx.get("pending_purpose") == "execution_scope_choice"


# --- B2-DIAG-02: bound field absent --------------------------------------


def test_b2diag02_absent_bound_never_grants_act():
    """Same message; model omits execution_bound entirely.

    CONTRACT: an absent model bound is NOT evidence of unrestricted
    scope — the MESSAGE still caps at PREPARE + pending choice."""
    provider = _direct_write_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select({"goal_class": "create_or_modify"}),
    )
    attempt = orch.attempt(
        "Prepare um cadastro, mas não aplique.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED


# --- B2-DIAG-03: bound value invalid -------------------------------------


def test_b2diag03_invalid_bound_never_grants_act():
    """Model returns an out-of-whitelist bound ('never_apply').

    CONTRACT: invalid model output has no permissive value — MESSAGE
    caps at PREPARE + pending choice, zero ACT."""
    provider = _direct_write_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select(
            {
                "goal_class": "create_or_modify",
                "execution_bound": "never_apply",
            }
        ),
    )
    attempt = orch.attempt(
        "Prepare um cadastro, mas não aplique.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED


# --- B2-DIAG-04: existing structural ceiling (control) -------------------


def test_b2diag04_request_ceiling_still_caps_act():
    """Control: max_execution_stage='prepare' + model 'unrestricted'.

    The structured request ceiling is independent of the model
    interpretation — ACT stays blocked even when the model misses the
    textual bound."""
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
    attempt = orch.attempt(
        "Prepare um cadastro, mas não aplique.",
        max_execution_stage="prepare",
    )
    assert "commit_record" not in _called_names(provider)
    assert attempt.status in (
        GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
        GovernedCapabilityStatus.WRITE_REJECTED,
    )


# --- B2-DIAG-05: legitimate governed ACT via bound typed choice ----------


def test_b2diag05_apply_prepared_executes_governed_act():
    """Positive control: 'Crie um cadastro.' MESSAGE -> PREPARE +
    pending scope choice (zero ACT in the same turn), then a typed
    APPLY_PREPARED decision bound to the pending proposal reaches the
    governed ACT — direct continuation is preserved WITHOUT trusting
    the model interpretation."""
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
    first = orch.attempt(
        "Crie um cadastro.",
        actor_user_id="u1",
        session_id="s1",
    )
    # MESSAGE never executes a material ACT in the same turn.
    assert "commit_record" not in _called_names(provider)
    assert first.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    ctx = dict(first.confirmation_context or {})
    assert ctx.get("pending_purpose") == "execution_scope_choice"

    second = _apply(orch, ctx)
    assert second.status is GovernedCapabilityStatus.SUCCESS
    assert "commit_record" in _called_names(provider)
    # Scope choice is not an owner confirmation: the owner capability
    # receives no fabricated `confirmation=True`.
    commit_args = dict(provider.calls[-1][1])
    assert commit_args.get("confirmation") is False


# --- B2-DIAG-06: over-restrictive bound only reduces ---------------------


def test_b2diag06_prepare_only_bound_only_reduces():
    """'Crie um cadastro.' + model execution_bound='prepare_only'.

    The bound can only reduce the ceiling — a fail-safe availability
    cost, never a security hole."""
    provider = _direct_write_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select(
            {
                "goal_class": "create_or_modify",
                "execution_bound": "prepare_only",
            }
        ),
    )
    attempt = orch.attempt("Crie um cadastro.")
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED


# --- B2-DIAG-07: semantic variants scripted 'unrestricted' ---------------


_BOUND_PHRASES = (
    "Apenas prepare uma prévia.",
    "Monte a proposta, sem executar.",
    "Pode deixar pronto, mas não salve.",
    "Não faça a alteração ainda.",
    "Quero revisar antes de aplicar.",
    "Prepare agora; executamos depois.",
)


@pytest.mark.parametrize("phrase", _BOUND_PHRASES)
def test_b2diag07_variants_never_reach_act_on_message(phrase):
    """Each 'prepare only' formulation + scripted 'unrestricted' bound
    must still cap at PREPARE — the contract does not depend on the
    model recognizing the restriction."""
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
    attempt = orch.attempt(phrase)
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED


# --- B2-DIAG-08: structured decision vs same-turn text --------------------


def _confirm_required_provider():
    return _process_provider(
        prepare_outcome=_outcome(
            "registry",
            "stage_record",
            "Prévia pronta.",
            structured={
                "data": {
                    "capability": "stage_record",
                    "proposal_handle": "prop-handle-1",
                    "exact_change": {
                        "entity": "process",
                        "operation": "create",
                    },
                    "ready": True,
                    "validation_result": {"ready": True},
                    "confirmation_requirement": {
                        "explicit_user_confirmation": True
                    },
                }
            },
        ),
        commit_outcome=_outcome(
            "registry",
            "commit_record",
            "created",
            structured={"data": {"record_id": "R-1"}},
        ),
    )


def test_b2diag08_apply_prepared_owner_true_executes_governed_act():
    """Owner ``explicit_user_confirmation=true``: the same typed
    APPLY_PREPARED decision satisfies BOTH the execution-scope choice
    and the owner-required confirmation — one bound decision, no
    artificial double click. The pending purpose must say so
    truthfully."""
    provider = _confirm_required_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select(
            {
                "goal_class": "create_or_modify",
                "execution_bound": "unrestricted",
            }
        ),
    )
    first = orch.attempt(
        "Prepare um cadastro.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert first.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    ctx = dict(first.confirmation_context or {})
    assert ctx.get("proposal_digest")
    assert (
        ctx.get("pending_purpose")
        == "execution_scope_plus_owner_confirmation"
    )
    second = _apply(orch, ctx)
    assert second.status is GovernedCapabilityStatus.SUCCESS
    assert "commit_record" in _called_names(provider)
    commit_args = dict(provider.calls[-1][1])
    assert commit_args.get("confirmation") is True


def test_b2diag08b_request_ceiling_still_binds_confirmation_path():
    """Sibling: the request ceiling DOES reach the decision path —
    max_execution_stage='prepare' refuses ACT even with a valid
    CONFIRM decision."""
    provider = _confirm_required_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select({"goal_class": "create_or_modify"}),
    )
    first = orch.attempt(
        "Prepare um cadastro.",
        actor_user_id="u1",
        session_id="s1",
    )
    ctx = dict(first.confirmation_context or {})
    second = orch.attempt(
        "",
        actor_user_id="u1",
        session_id="s1",
        max_execution_stage="prepare",
        confirmation={
            "proposal_digest": ctx["proposal_digest"],
            "session_id": ctx["session_id"],
            "preview_fingerprint": ctx["preview_fingerprint"],
            "decision": "CONFIRM",
        },
    )
    assert second.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert second.error_code == "execution_ceiling"
    assert "commit_record" not in _called_names(provider)


def test_b2diag08c_reject_prepared_consumes_pending_zero_act():
    """REJECT_PREPARED invalidates the pending proposal and never
    executes — a later CONFIRM replay on the same digest fails."""
    provider = _confirm_required_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select({"goal_class": "create_or_modify"}),
    )
    first = orch.attempt(
        "Prepare um cadastro.", actor_user_id="u1", session_id="s1"
    )
    ctx = dict(first.confirmation_context or {})
    rejected = _apply(orch, ctx, decision="REJECT")
    assert rejected.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert "commit_record" not in _called_names(provider)
    replay = _apply(orch, ctx)
    assert replay.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert replay.error_code == "confirmation_unknown"
    assert "commit_record" not in _called_names(provider)


def test_b2diag08d_apply_replay_fails_closed():
    """A consumed decision cannot be replayed: double CONFIRM on the
    same digest executes at most once."""
    provider = _direct_write_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select({"goal_class": "create_or_modify"}),
    )
    first = orch.attempt(
        "Crie um cadastro.", actor_user_id="u1", session_id="s1"
    )
    ctx = dict(first.confirmation_context or {})
    applied = _apply(orch, ctx)
    assert applied.status is GovernedCapabilityStatus.SUCCESS
    assert _called_names(provider).count("commit_record") == 1
    replay = _apply(orch, ctx)
    assert replay.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert _called_names(provider).count("commit_record") == 1


# --- B2-DIAG-09: provider neutrality -------------------------------------


def _renamed_direct_provider():
    caps = [
        _cap(
            "ledger",
            "zz-records",
            "list_fields",
            SpecialistOperationClass.DISCOVERY,
            desc="list entity fields",
        ),
        _cap(
            "ledger",
            "zz-records",
            "draft_entry",
            SpecialistOperationClass.PREPARE,
            schema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "operation": {"type": "string"},
                    "changes": {"type": "object"},
                },
                "required": ["entity", "operation", "changes"],
            },
            desc="draft an entry change",
        ),
        _cap(
            "ledger",
            "zz-records",
            "post_entry",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {
                    "proposal_handle": {"type": "string"},
                    "confirmation": {"type": "boolean"},
                },
                "required": ["proposal_handle", "confirmation"],
            },
            desc="post a drafted entry",
        ),
    ]
    return FakeProvider(
        "zz-records",
        [_group("zz-records", "ledger", caps)],
        outcomes={
            ("ledger", "draft_entry"): _outcome(
                "ledger",
                "draft_entry",
                "Prévia pronta.",
                structured={
                    "data": {
                        "capability": "draft_entry",
                        "proposal_handle": "h-1",
                        "exact_change": {
                            "entity": "process",
                            "operation": "create",
                        },
                        "ready": True,
                        "validation_result": {"ready": True},
                        "confirmation_requirement": {
                            "explicit_user_confirmation": False
                        },
                    }
                },
            ),
            ("ledger", "post_entry"): _outcome(
                "ledger",
                "post_entry",
                "posted",
                structured={"data": {"entry_id": "E-1"}},
            ),
        },
    )


def test_b2diag09_renamed_surface_same_fail_closed_contract():
    """Fully renamed provider/group/capabilities: MESSAGE caps at
    PREPARE + pending choice exactly as before — the gate consumes
    operation_class + bound structure, never names. A typed APPLY on
    the exact pending reaches the governed ACT."""
    provider = _renamed_direct_provider()
    orch, _ = _orchestrator(
        [provider],
        _select(
            "zz-records:ledger",
            "draft_entry",
            arguments=_STAGE_ARGS,
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                    "execution_bound": "unrestricted",
                }
            },
        ),
    )
    first = orch.attempt(
        "Prepare um cadastro, mas não aplique.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert "post_entry" not in _called_names(provider)
    assert first.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    ctx = dict(first.confirmation_context or {})
    applied = _apply(orch, ctx)
    assert applied.status is GovernedCapabilityStatus.SUCCESS
    assert "post_entry" in _called_names(provider)


def test_b2diag09b_owner_without_act_cannot_elevate():
    """Sibling: owner with only PREPARE (no ACT on the surface) —
    nothing can elevate the turn regardless of the bound."""
    caps = [
        _cap(
            "registry",
            "acme-flow",
            "stage_record",
            SpecialistOperationClass.PREPARE,
            schema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "operation": {"type": "string"},
                    "changes": {"type": "object"},
                },
                "required": ["entity", "operation", "changes"],
            },
            desc="draft a record change",
        ),
    ]
    provider = FakeProvider(
        "acme-flow",
        [_group("acme-flow", "registry", caps)],
        outcomes={
            ("registry", "stage_record"): _outcome(
                "registry",
                "stage_record",
                "Prévia pronta.",
                structured={
                    "data": {
                        "capability": "stage_record",
                        "proposal_handle": "h-2",
                        "exact_change": {
                            "entity": "process",
                            "operation": "create",
                        },
                        "ready": True,
                        "validation_result": {"ready": True},
                        "confirmation_requirement": {
                            "explicit_user_confirmation": False
                        },
                    }
                },
            ),
        },
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "acme-flow:registry",
            "stage_record",
            arguments=_STAGE_ARGS,
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                    "execution_bound": "unrestricted",
                }
            },
        ),
    )
    attempt = orch.attempt("Prepare um cadastro, mas não aplique.")
    assert _called_names(provider) == ["stage_record"]
    # No ACT sibling announced by the owner — fail closed.
    assert attempt.status is GovernedCapabilityStatus.WRITE_REJECTED


# --- ACT-only / no verifiable PREPARE (§6.184 §5) -------------------------


def _act_only_provider():
    """Owner exposing a single ACT capability (no PREPARE sibling)."""
    caps = [
        _cap(
            "registry",
            "acme-flow",
            "wipe_record",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {"record_id": {"type": "string"}},
            },
            desc="destructively wipe a record",
        ),
    ]
    return FakeProvider(
        "acme-flow",
        [_group("acme-flow", "registry", caps)],
        outcomes={
            ("registry", "wipe_record"): _outcome(
                "registry", "wipe_record", "wiped",
                structured={"data": {"done": True}},
            ),
        },
    )


def test_b2diag10_act_only_capability_never_executes_from_message():
    """A cold ACT selection on a free-text MESSAGE has no verified
    PREPARE/preview binding — the contract refuses it truthfully
    (precondition), never executes, never fabricates a pending intent
    preview."""
    provider = _act_only_provider()
    orch, _ = _orchestrator(
        [provider],
        _select(
            "acme-flow:registry",
            "wipe_record",
            arguments={"record_id": "R-9"},
            extra={
                GOAL_INSTRUCTION_ID: {"goal_class": "create_or_modify"}
            },
        ),
    )
    attempt = orch.attempt("Apague o registro R-9.")
    assert "wipe_record" not in _called_names(provider)
    assert attempt.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert attempt.confirmation_context is None
