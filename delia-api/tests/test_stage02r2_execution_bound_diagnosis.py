"""Stage-02R2 adversarial diagnosis — textual execution bound vs model
interpretation (ledger §6.176, review doc 10).

DIAGNOSTIC-ONLY suite: it proves or disproves the B2 residual without
modifying production code. Cases that assert the *safety* property the
review requires ("textual 'não aplique' must cap the turn") are marked
``xfail(strict=True)`` — they FAIL on the reviewed SHA
`9fd3a7bc959686a6c4828f46b7d292c81a96938c` because the runtime only
honors the bound when the model emits ``execution_bound="prepare_only"``
and silently coerces absent/invalid/misclassified values to
``"unrestricted"``. xfail keeps the defect documented and the suite
green; it must never be read as behavioral acceptance.

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

_KNOWN_DEFECT = pytest.mark.xfail(
    strict=True,
    reason=(
        "B2 residual §6.176: textual 'não aplique' is honored only when "
        "the model emits execution_bound='prepare_only'; absent/invalid/"
        "misclassified bounds collapse to 'unrestricted' and governed "
        "direct ACT proceeds under owner confirmation=False."
    ),
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


# --- B2-DIAG-01: explicit contradiction ---------------------------------


@_KNOWN_DEFECT
def test_b2diag01_textual_bound_vs_unrestricted_proposal():
    """'Prepare um cadastro, mas não aplique.' + model proposal
    goal_class=create_or_modify, execution_bound='unrestricted',
    request ceiling None, owner READY/direct, ACT available.

    SAFETY property: commit must never run against the explicit user
    restriction. Observed on reviewed SHA: 'unrestricted' is trusted as
    a positive declaration; prepare_only stays False; the direct
    governed continuation invokes commit_record — FAIL."""
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
    attempt = orch.attempt("Prepare um cadastro, mas não aplique.")
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


# --- B2-DIAG-02: bound field absent --------------------------------------


@_KNOWN_DEFECT
def test_b2diag02_absent_bound_indistinguishable_from_unrestricted():
    """Same message; model omits execution_bound entirely.

    Code fact: ``proposal.get('execution_bound')`` is None -> coerced to
    'unrestricted' — an ABSENT field is indistinguishable from a
    positive 'no restriction' declaration; declared=True survives via
    goal_class, so the write path proceeds. Expected safe outcome:
    no ACT — FAIL on reviewed SHA (commit_record invoked)."""
    provider = _direct_write_provider()
    orch, _ = _orchestrator(
        [provider],
        _stage_select({"goal_class": "create_or_modify"}),
    )
    attempt = orch.attempt("Prepare um cadastro, mas não aplique.")
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


# --- B2-DIAG-03: bound value invalid -------------------------------------


@_KNOWN_DEFECT
def test_b2diag03_invalid_bound_falls_back_to_unrestricted():
    """Model returns an out-of-whitelist bound ('never_apply').

    Code fact: values outside _EXECUTION_BOUNDS normalize to
    'unrestricted' — the validation is fail-OPEN toward more
    execution authority, not fail-closed. Expected safe outcome:
    no ACT — FAIL on reviewed SHA."""
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
    attempt = orch.attempt("Prepare um cadastro, mas não aplique.")
    assert "commit_record" not in _called_names(provider)
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


# --- B2-DIAG-04: existing structural ceiling (control) -------------------


def test_b2diag04_request_ceiling_still_caps_act():
    """Control: max_execution_stage='prepare' + model 'unrestricted'.

    The structured request ceiling is independent of the model
    interpretation — ACT must stay blocked even when the model misses
    the textual bound. PASS expected."""
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


# --- B2-DIAG-05: positive control — legitimate direct continuation -------


def test_b2diag05_unrestricted_action_keeps_direct_continuation():
    """Control: 'Crie um cadastro.' with NO restriction + owner direct.

    The governed direct continuation must stay available — the fix must
    never degrade into universal confirmation. PASS expected."""
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
    attempt = orch.attempt("Crie um cadastro.")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "commit_record" in _called_names(provider)


# --- B2-DIAG-06: over-restrictive bound only reduces ---------------------


def test_b2diag06_prepare_only_bound_only_reduces():
    """'Crie um cadastro.' + model execution_bound='prepare_only'.

    The bound can only reduce the ceiling: ACT is capped even though
    the user text asks for the action itself. This is the documented
    fail-safe direction — availability cost, not a security hole.
    PASS expected (records the over-restriction impact)."""
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


@_KNOWN_DEFECT
@pytest.mark.parametrize("phrase", _BOUND_PHRASES)
def test_b2diag07_variants_depend_solely_on_model_recognition(phrase):
    """Each equivalent formulation of 'prepare only' relies EXCLUSIVELY
    on the model emitting prepare_only — the runtime holds no
    independent check. Scripted 'unrestricted' + any variant → ACT.
    FAIL on reviewed SHA for every phrase (no keyword path exists)."""
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
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


# --- B2-DIAG-08: structured confirmation vs same-turn text ---------------


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


def test_b2diag08_confirmation_path_never_reads_turn_text():
    """DIAG-08 investigation — a turn carrying a structured
    confirmation payload bypasses target selection AND goal
    interpretation entirely (``_attempt_confirmation`` has no
    input_text parameter): the same-turn message 'Não aplique.' is
    never interpreted. Observed behavior (documented, not a safety
    verdict): a valid CONFIRM binds and executes ACT regardless of the
    accompanying text — the request ceiling still applies. Precedence
    between an explicit structured CONFIRM and contradictory free text
    is UNSPECIFIED in the contract — recorded as a specification gap,
    not a proven exploit."""
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
    assert first.status is (
        GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    ctx = dict(first.confirmation_context or {})
    assert ctx.get("proposal_digest")
    second = orch.attempt(
        "Não aplique.",
        actor_user_id="u1",
        session_id="s1",
        confirmation={
            "proposal_digest": ctx["proposal_digest"],
            "session_id": ctx["session_id"],
            "preview_fingerprint": ctx["preview_fingerprint"],
            "decision": "CONFIRM",
        },
    )
    # Observed: the structured CONFIRM governs; 'Não aplique.' is not
    # interpreted — the confirmation path has no semantic channel.
    assert second.status is GovernedCapabilityStatus.SUCCESS
    assert "commit_record" in _called_names(provider)


def test_b2diag08b_request_ceiling_still_binds_confirmation_path():
    """DIAG-08 sibling: the request ceiling DOES reach the
    confirmation path — max_execution_stage='prepare' refuses ACT even
    with a valid CONFIRM. PASS expected."""
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
        "Confirme.",
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


@_KNOWN_DEFECT
def test_b2diag09_renamed_surface_same_fail_open_path():
    """Fully renamed provider/group/capabilities: the contradiction
    path is identical — the gate consumes only operation_class + the
    validated bound, never names. FAIL on reviewed SHA (post_entry
    invoked under 'unrestricted')."""
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
    attempt = orch.attempt("Prepare um cadastro, mas não aplique.")
    assert "post_entry" not in _called_names(provider)
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


def test_b2diag09b_owner_without_act_cannot_elevate():
    """Sibling: owner with only PREPARE (no ACT on the surface) —
    nothing can elevate the turn regardless of the bound. The residual
    requires an ACT sibling; the structural guarantee stands.
    PASS expected."""
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
    # Observed: a direct-policy owner with no ACT sibling cannot
    # complete the write — the continuation gate fails closed
    # (WRITE_REJECTED), regardless of the bound value.
    assert attempt.status is GovernedCapabilityStatus.WRITE_REJECTED
