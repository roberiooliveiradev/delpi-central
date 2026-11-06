"""Governed capability orchestration — the Application-owned
stage-gate implementation bound by ``SupportsGovernedStageGates``.

Extracted from the retired monolithic ``orchestration`` module:
provider-neutral catalog/listing, governed invocation,
semantic finalize composition and write-lifecycle stages live
here; evidence/plan/finalize helpers live in
``semantic_capability_support``.
"""
from __future__ import annotations

import contextvars
import dataclasses
import hashlib
import json
import logging
import re
import time
import unicodedata
import uuid
from typing import (
    Any,
    Callable,
    Mapping,
    MutableMapping,
    Sequence,
)

from app.application.interaction.activity import (
    ActivityEventSink,
    ActivityOutcomeStatus,
    ActivityPhase,
    ActivityState,
    capability_ref as _activity_capability_ref,
    outcome_ref as _activity_outcome_ref,
    owner_ref as _activity_owner_ref,
    source_ref as _activity_source_ref,
)
from app.application.interaction.argument_validation import (
    MAX_ARGUMENT_KEYS,
    ORCHESTRATED_FIELDS,
    validate_arguments as _validate_instance,
    validate_untyped_arguments,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityBinding,
    GovernedCapabilityStatus,
    OWNER_PATH_UNBOUND,
    SURFACE_INQUIRY_ADMISSION,
    _error_attempt,
    _success_attempt,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    LIMITATION_CAPABILITY_SURFACE_LISTING,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    LIMITATION_RESULT_TRUNCATED,
    VerifiedCompositeEvidence,
)
from app.application.interaction.pending_proposals import (
    DEFAULT_PENDING_TTL_SECONDS,
    PENDING_PURPOSE_SCOPE_CHOICE,
    PENDING_PURPOSE_SCOPE_PLUS_CONFIRMATION,
    PendingWrite,
    PendingWriteStore,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ModelInvocationRequest,
    TurnKind,
)
from app.application.interaction.turn_budget import (
    DEFAULT_TURN_BUDGET_SECONDS,
    TurnBudgetExhausted,
    TurnDeadline,
)
from app.application.interaction.turn_observability import (
    current_call_ledger,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.governed_retries import (
    LLM_CALL_MAX_ATTEMPTS,
    call_retry_eligible,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    InvestigationAnswer,
    InvestigationAnswerStatus,
    ProviderCapability,
)
from app.application.capability_provision.conversational_response import (
    EMPTY_RESULT_TEXT,
    FieldLabels,
    MAX_RENDER_CONTENT_CHARS,
    _business_lines,
    _format_structured,
    _md_business_lines,
    _md_format_structured,
    _md_leaf,
    field_display_label,
)
from app.application.capability_provision.generic_evidence_renderer import (
    MAX_DESCRIPTION_CHARS,
    MAX_OWNER_EVIDENCE_ENTRY_CHARS,
    MAX_RENDER_LIST_ITEMS,
    MAX_SURFACE_ENTRIES,
    _CAPABILITY_VOCABULARY_KEYS,
    _CONTROL_PLANE_KEYS,
    _RESOLVER_ENVELOPE_KEYS,
    _canonical_key,
    _comparison_records,
    _contract_fact_rows,
    _is_generic_status,
    _mapping_items_excluding_control,
    _redact_text,
    _resolver_entities,
    _sanitize_renderable,
    _unwrap_owner_payload,
    extract_pagination_envelope,
    parse_temporal_value,
)
from app.application.capability_provision.ports import (
    CapabilityProviderPort,
)
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
from app.domain.governed_write.model import (
    ConfirmationDecision,
    ConfirmationRecord,
    ConfirmationState,
    ProposalReadiness,
    StructuredConfirmation,
    WriteOutcomeStatus,
    WriteProposalPreview,
)
from app.domain.governed_write.rules import (
    bind_confirmation,
    evaluate_write_continuation,
    preview_fingerprint,
    project_proposal_preview,
    project_write_outcome,
    proposal_digest,
)
from app.application.interaction.workspace_context import (
    WorkspaceContext,
)
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultStatus,
)
from app.domain.specialist_interop.rules import (
    invocable_in_interactive_phase,
)

_logger = logging.getLogger(__name__)

# Candidate-flow and proposal-flow detection are structural,
# owner-defined: a capability whose input schema requires
# ``candidate_token`` is the second step of an owner
# discover->candidate->execute pattern (DAVI); a capability whose input
# schema requires ``proposal_handle`` is the ACT step of an owner
# prepare->proposal->commit pattern (TÉO/VISTA). DÉLIA never names the
# pairs — the owner schema carries them.
CANDIDATE_TOKEN_FIELD = "candidate_token"
PROPOSAL_HANDLE_FIELD = "proposal_handle"
# Orchestration-resolved schema fields live in
# argument_validation.ORCHESTRATED_FIELDS (re-exported above): never
# accepted from a model proposal — DÉLIA fills them from owner-issued
# state (candidate_token, proposal_handle) or from the governed-write
# decision itself (confirmation, idempotency_key); commit_now is
# generic orchestration-control semantics (collapses PREPARE+ACT,
# bypassing the DÉLIA confirmation gate).

from app.application.capability_provision import semantic_capability_support as _support
from app.application.capability_provision.semantic_capability_support import (
    CANDIDATE_TOKEN_FIELD,
    CONFIRMATION_POLICY_CONFIRM,
    CONFIRMATION_POLICY_DIRECT,
    CONFIRMATION_POLICY_INVALID,
    CONVERSATIONAL_FALLBACK_RESERVE_SECONDS,
    DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS,
    EVIDENCE_COMPOSITION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    MAX_ARGUMENTS_BLOCK_CHARS,
    MAX_DISCOVERY_CONTEXT_EXCERPT_CHARS,
    MAX_DISCOVERY_CONTEXT_TURNS,
    MAX_DISCOVERY_QUERY_CHARS,
    MAX_GOVERNED_ATTEMPTS,
    MAX_PRIOR_EXCERPTS,
    MAX_STRUCTURED_RENDER_CHARS,
    MAX_SURFACE_CHARS,
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    MODEL_STAGE_TIMEOUT_SECONDS,
    OBLIGATION_INCONCLUSIVE,
    OBLIGATION_REQUIRED,
    OBLIGATION_SATISFIED,
    OBLIGATION_UNAVAILABLE,
    OBLIGATION_UNSATISFIED,
    ORCHESTRATION_INSTRUCTION_KEYS,
    PROPOSAL_HANDLE_FIELD,
    RenderedSpecialistOutcome,
    SELECTION_INSTRUCTION_VERSION,
    SemanticInvestigationPlan,
    _ACTIVITY_SINK,
    _ATTEMPT_INDEX,
    _AttemptCheckpoint,
    _BOND_STOP_TOKENS,
    _CANCEL_CHECK,
    _CONCRETE_VALUE_TOKENS,
    _EVIDENCE_CHILD_KEYS,
    _EVIDENCE_CODE_KEYS,
    _EVIDENCE_DESC_KEYS,
    _EVIDENCE_QTY_KEYS,
    _EVIDENCE_TYPE_KEYS,
    _EVIDENCE_UNIT_KEYS,
    _GUIDANCE_FAMILY_ORDER,
    _GUIDANCE_INDEX_KEYS,
    _GUIDANCE_INDEX_PREVIEW_CHARS,
    _GUIDANCE_META_KEYS,
    _GUIDANCE_NESTED_KEYS,
    _GUIDANCE_RENDER_SKIP_KEYS,
    _GUIDANCE_SECTION_FAMILIES,
    _IDENTIFIER_ARG_KEY_RE,
    _IDENTIFIER_LITERAL_RE,
    _LAST_CATALOG_FAILURES,
    _MAX_DISCOVERY_SURFACE_LINES,
    _MAX_SURFACE_INQUIRY_GROUPS,
    _NULL_LITERAL_ARG_VALUES,
    _OBLIGATION_STATES,
    _ORCHESTRATION_BLOCK_ARG_KEYS,
    _OUTCOME_NOTE,
    _READINESS_NOTE,
    _RESUMABLE_OPERATION_CLASSES,
    _RESUME_STATE,
    _StageDeadlineExceeded,
    _TEMPORAL_ARG_KEY_RE,
    _TurnCancelled,
    _WRITE_OPERATION_CLASSES,
    _act_arguments,
    _activity_outcome_summary,
    _apply_declared_answer,
    _attempt_satisfies_obligation,
    _authoritative_structure_root,
    _bind_attempt_to_target,
    _bind_identifier_args_from_utterance,
    _bind_missing_required_query,
    _cancel_observed,
    _candidate_needs_missing_identifier,
    _clarification_content,
    _context_folded_discovery_query,
    _deterministic_guidance_content,
    _discovery_empty_result_class,
    _effective_confirmation_policy,
    _emit_activity,
    _evaluate_material_obligations,
    _evidence_rows_by_code,
    _finalize_agent_collected_attempts,
    _find_act_capability,
    _fit_json_block,
    _flatten_evidence_records,
    _group_activity_refs,
    _guidance_family_for_key,
    _guidance_hit_count,
    _guidance_section_records,
    _identifier_arg_keys,
    _is_business_evidence_attempt,
    _is_candidate_bound,
    _is_unconstrained_string,
    _iter_guidance_doc_items,
    _json_block,
    _lineage,
    _listing_failure_is_transient,
    _live_interop_surface_lines,
    _logger,
    _md_guidance_content,
    _normalize_identity_tuple,
    _omitted_sections_line,
    _owner_eligible_action_count,
    _pack_guidance_sections,
    _preview_render,
    _prior_observation_context,
    _property_node,
    _render_evidence_comparison,
    _render_guidance_value,
    _render_zero_candidate_discovery,
    _requires_field,
    _resolvable_identifier_literals,
    _resume_invoke_key,
    _resume_stage_key,
    _schema_declared_literals,
    _schema_keys,
    _select_guidance_records,
    _sole_unconstrained_string_field,
    _surface_inquiry_content,
    _synthesis_records,
    _uncovered_named_identifiers,
    _verify_evidence_composition,
    _workspace_identifier_literals,
    render_specialist_outcome,
    render_specialist_outcome_rich,
)


# Compatibility delegation: any support-contract name not listed
# above resolves from its canonical owner module — consumers
# migrating off the retired orchestration import surface find
# every helper here exactly once.
def __getattr__(name: str):
    return getattr(_support, name)


class OperationalCapabilityOrchestrator:
    """Provider-neutral governed capability orchestration — no local
    catalog authority.

    Attempts at most one bounded operational plan per turn
    (``MAX_OPERATIONAL_PLAN_STEPS``): capability groups are fetched
    live from every provider, selection is a bounded model proposal
    revalidated against the fresh projection, and when the selected
    capability's schema carries owner-defined vocabulary (opaque
    envelope fields) a required DISCOVERY step runs first so argument
    projection consumes the owner's own declared vocabulary — never an
    invented one. Every invocation still passes the provider's own
    enforcement boundaries plus owner/domain AuthZ. Write-class
    selections route through the generic governed-write chain:
    preview -> pending orchestration state -> structured confirmation
    -> fresh live revalidation -> ACT -> owner-authoritative outcome
    projection.
    """

    def __init__(
        self,
        providers: Sequence[CapabilityProviderPort],
        *,
        invoke_model: InvokeModel | None = None,
        model_ref=None,
        pending_writes: PendingWriteStore | None = None,
        turn_budget_seconds: float = DEFAULT_TURN_BUDGET_SECONDS,
        model_stage_timeout_seconds: float = MODEL_STAGE_TIMEOUT_SECONDS,
        interaction_total_budget_seconds: float = (
            DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS
        ),
        max_governed_attempts: int = 1,
        llm_call_max_attempts: int = 1,
        field_labels: FieldLabels | None = None,
        orchestration_instructions: Mapping[str, str] | None = None,
    ) -> None:
        self._providers = {p.provider_id: p for p in providers}
        # R1/M01: declarative instruction text is composition-injected
        # from the governed resource; absent in tests -> empty map.
        self._instructions = dict(orchestration_instructions or {})
        self._invoke_model = invoke_model
        self._model_ref = model_ref
        self._pending_writes = pending_writes or PendingWriteStore()
        self._turn_budget_seconds = float(turn_budget_seconds)
        self._model_stage_timeout_seconds = float(
            model_stage_timeout_seconds
        )
        # CP4 (docs 88 §10.2 / 90): ephemeral governed resume — OFF by
        # default (single attempt, legacy behavior). The approved
        # ceiling is two attempts under one monotonic interaction
        # budget; a configured value above the ceiling is clamped,
        # never honored.
        self._interaction_total_budget_seconds = max(
            0.0, float(interaction_total_budget_seconds)
        )
        self._max_governed_attempts = max(
            1, min(int(max_governed_attempts), MAX_GOVERNED_ATTEMPTS)
        )
        # Doc 103 GATE 1: governed per-LOGICAL-CALL retry limit — a
        # mechanism distinct from turn resume above. Defaults to 1
        # (OFF); clamped to the PO-approved ceiling, never raised.
        self._llm_call_max_attempts = max(
            1, min(int(llm_call_max_attempts), LLM_CALL_MAX_ATTEMPTS)
        )
        # Governed presentation labels resolve field names in every
        # path (detail, list, comparison) — absent the fallback stays
        # neutral.
        self._field_labels = dict(field_labels or {})

    def _instruction(self, key: str) -> str:
        """Declarative instruction text by resource key — injected,
        never authored here; empty only in tests without the resource."""
        return self._instructions.get(key, "")


    def _run_governed_attempts(
        self,
        attempt_once: Callable[
            [str, TurnDeadline], GovernedCapabilityAttempt
        ],
        *,
        correlation_id: str | None,
        confirmation: Mapping[str, Any] | None,
        activity_sink: ActivityEventSink | None,
        cancel_check: Callable[[], bool] | None,
        turn_deadline: TurnDeadline | None,
    ) -> GovernedCapabilityAttempt:
        """Shared governed attempt runner: binds request-scoped
        context (activity sink, resume checkpoint, cancellation,
        relevance flag), anchors the monotonic interaction budget
        and drives the bounded attempt/resume loop around a caller-
        supplied single-attempt callable. Engine A passes
        self._attempt; alternative engines pass one graph
        invocation — the retry/budget/cancel controls stay shared
        and never re-implemented per engine (doc 194)."""
        correlation = correlation_id or str(uuid.uuid4())
        first_deadline = turn_deadline or TurnDeadline.start(
            self._turn_budget_seconds
        )
        # The checkpoint exists only when recovery is enabled for this
        # interaction — confirmation turns and legacy single-attempt
        # mode never checkpoint, never resume.
        checkpoint = (
            _AttemptCheckpoint()
            if self._max_governed_attempts > 1 and confirmation is None
            else None
        )
        # Bind the request-scoped activity sink, resume checkpoint and
        # cancellation probe for this call's context only — the
        # instance is shared across concurrent turns.
        sink_token = _ACTIVITY_SINK.set(activity_sink)
        resume_token = _RESUME_STATE.set(checkpoint)
        cancel_token = _CANCEL_CHECK.set(cancel_check)
        try:
            # Monotonic interaction end: anchored at the REAL start of
            # the interaction's clock (TurnDeadline.start), never at
            # this boundary — time already consumed before the
            # orchestrator counts against the approved total. Each
            # further attempt receives the remaining global budget —
            # no artificial per-attempt wall (doc 103).
            interaction_start = (
                first_deadline.started_at
                if first_deadline.started_at is not None
                else first_deadline.clock()
            )
            interaction_end = (
                interaction_start + self._interaction_total_budget_seconds
            )
            deadline = first_deadline
            attempts = 0
            while True:
                try:
                    _ATTEMPT_INDEX.set(attempts + 1)
                    completed = attempt_once(correlation, deadline)
                    # Presentation-only accounting: how many governed
                    # attempts this turn actually needed. Never
                    # authority — resume stays deterministic.
                    return dataclasses.replace(
                        completed, governed_attempts=attempts + 1
                    )
                except _StageDeadlineExceeded as exc:
                    reason = exc.reason
                except TurnBudgetExhausted:
                    reason = "turn_budget_exhausted"
                except _TurnCancelled:
                    reason = "cancelled"
                attempts += 1
                _logger.info(
                    "orchestration stage=turn_budget decision=%s "
                    "attempt=%d correlation_id=%s",
                    reason,
                    attempts,
                    correlation,
                )
                remaining = interaction_end - deadline.clock()
                # Doc 103: no artificial per-attempt wall — an attempt
                # receives the remaining global budget; the 60s per-call
                # ceiling and 3-call retry bound model work inside it.
                per_attempt = max(0.0, remaining)
                if (
                    checkpoint is None
                    or attempts >= self._max_governed_attempts
                    or checkpoint.mutating_invoke_started
                    or (cancel_check is not None and cancel_check())
                    or per_attempt < MIN_VIABLE_MODEL_STAGE_SECONDS
                    # A model_timeout reaching this boundary already
                    # consumed the governed per-call retry budget —
                    # resuming the turn would re-invoke the same
                    # logical call a forbidden fourth time. Only
                    # budget exhaustion resumes the turn (checkpoint
                    # replays provably completed work).
                    or reason == "model_timeout"
                ):
                    # Stage 6 attribution: which responsibility ended
                    # the turn — model stage timeout, shared budget
                    # exhaustion or client cancellation — recorded in
                    # coarse terms for the observability projection.
                    term_ledger = current_call_ledger()
                    if term_ledger is not None:
                        term_ledger.record_terminal_timeout(
                            {
                                "model_timeout": "model",
                                "turn_budget_exhausted": "budget",
                                "cancelled": "cancelled",
                            }.get(reason, "budget")
                        )
                    return GovernedCapabilityAttempt(
                        status=GovernedCapabilityStatus.PROCESSING_TIMEOUT,
                        correlation_id=correlation,
                        error_code=reason,
                        governed_attempts=attempts,
                    )
                # A new bounded attempt on the SAME interaction: fresh
                # deadline inside the monotonic budget; the checkpoint
                # replays only what provably completed.
                deadline = TurnDeadline(
                    ends_at=deadline.clock() + per_attempt,
                    clock=deadline.clock,
                )
                _emit_activity(
                    phase=ActivityPhase.CONTINUING,
                    correlation=correlation,
                )
                _logger.info(
                    "orchestration stage=governed_resume "
                    "decision=continue attempt=%d remaining_ms=%d "
                    "correlation_id=%s",
                    attempts + 1,
                    int(remaining * 1000),
                    correlation,
                )
        finally:
            _ACTIVITY_SINK.reset(sink_token)
            _RESUME_STATE.reset(resume_token)
            _CANCEL_CHECK.reset(cancel_token)



    def _compose_multi_evidence(
        self,
        sources: dict[str, tuple[Mapping[str, Any], ...]],
        input_text: str,
        *,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline | None,
    ) -> tuple[str, tuple[str, ...], str] | None:
        """Doc 222 E4 — governed multi-evidence composition.

        The model only proposes candidate correspondences between
        records of different authorized sources; the deterministic
        verifier computes every fact over the full projected
        coverage and rejects fabricated/out-of-range refs. Output
        is rendered verbatim from verified evidence — no model
        factual prose (ADR 58 / §6.145)."""
        instruction = self._instruction(EVIDENCE_COMPOSITION_INSTRUCTION_ID)
        if not instruction or len(sources) != 2:
            return None
        block = {
            sid: _flatten_evidence_records(records)
            for sid, records in sources.items()
        }
        proposal = self._propose(
            input_text,
            block_tag="evidence_sources",
            block_payload=_fit_json_block(block, MAX_SURFACE_CHARS),
            instruction_id=EVIDENCE_COMPOSITION_INSTRUCTION_ID,
            instruction=instruction,
            instruction_version=SELECTION_INSTRUCTION_VERSION,
            expected_fields=("proposed_pairs",),
            input_kind="evidence_composition",
            allowed_keys=frozenset({"proposed_pairs", "limitations"}),
            workspace_context=workspace_context,
            correlation=correlation,
            deadline=deadline,
        )
        result = _verify_evidence_composition(sources, proposal)
        _logger.info(
            "orchestration stage=evidence_composition decision=%s "
            "sources=%d correlation_id=%s",
            result["verdict"],
            len(sources),
            correlation,
        )
        return (_render_evidence_comparison(result),
                tuple(result["limitations"]), result["verdict"])






    _GOAL_CLASSES = frozenset(
        {"read", "analyze", "compare", "create_or_modify", "clarify"}
    )

    @dataclasses.dataclass(frozen=True, slots=True)
    class _TurnGoal:
        """Bounded semantic interpretation of the user turn (LOOP-03R1).

        A proposal, never authority: it classifies intent, carries the
        business subject and user-stated scope constraints. Downstream
        stages consume it as untrusted-but-validated structure — a
        comparison goal can never silently collapse to single-source
        native success.
        """

        goal_class: str = "read"
        comparison_requested: bool = False
        output_mode: str = "unspecified"
        business_subject: str | None = None
        scope_constraints: tuple[tuple[str, str], ...] = ()
        # True only when a validated model proposal declared the class
        # — the neutral default is never treated as declared intent,
        # so an absent interpretation is unproven intent and cannot
        # carry a write-class selection (C3-CI-02R1 §6.174).
        declared: bool = False
        # User-stated execution restriction (C3-CI-02R1): "prepare_only"
        # when the user explicitly forbids applying the change; the
        # bound can only reduce the effective execution ceiling.
        execution_bound: str = "unrestricted"
        # True only when a validated proposal declares that prior
        # DELIA_RESULT content already answers without a new owner call.
        prior_evidence_sufficient: bool = False
        # D5 evidence-intent correspondence (doc 124): True only when a
        # validated proposal declares the user asked about the published
        # contract/schema itself. Owner contract metadata composes an
        # answer only for declared contract subjects — absent means
        # unproven intent, never schema-dump-by-default.
        contract_subject: bool = False












    @dataclasses.dataclass(frozen=True, slots=True)
    class _ForeignResult:
        """Outcome of the bounded foreign non-mutating step."""

        outcome: SpecialistOutcome | None = None
        evidence: str | None = None
        missing_inputs: tuple[str, ...] = ()
        failed: bool = False




    # ---------------- write orchestration ----------------

    def _attempt_prepare(
        self,
        group_key: str,
        remote_name: str,
        arguments: Mapping[str, Any],
        group: CapabilityGroup,
        actor_user_id: str | None,
        session_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Invoke an owner PREPARE capability and project the proposal.

        A READY proposal is held as backend-only pending orchestration
        state and surfaced as CONFIRMATION_REQUIRED — the raw
        proposal_ref never leaves this boundary. Anything else is
        rendered truthfully (NOT_READY/INVALID/EXPIRED/denials are
        owner answers, not DÉLIA failures).
        """
        capability_ref = f"{group_key}.{remote_name}"
        _logger.info(
            "orchestration stage=prepare_invoke decision=call "
            "capability=%s arg_keys=%s correlation_id=%s",
            capability_ref,
            ",".join(sorted(str(k) for k in arguments))[:200],
            correlation,
        )
        try:
            outcome = self._invoke(
                group, remote_name, dict(arguments), correlation,
                deadline,
            )
        except CapabilityProviderError as exc:
            _logger.info(
                "orchestration stage=prepare_invoke decision=error "
                "error_code=%s detail=%s correlation_id=%s",
                exc.code,
                exc.message[:240],
                correlation,
            )
            return _error_attempt(correlation, exc)

        payload = outcome.structured or {}
        preview = project_proposal_preview(
            capability_ref=capability_ref,
            remote_capability=remote_name,
            owner_payload=payload,
            specialist_id=group_key,
            correlation_id=correlation,
            observed_at=outcome.provenance.observed_at,
            now_epoch=time.time(),
            limitations=outcome.limitations,
        )
        self._audit(
            stage="PREPARE_PROJECTED",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=preview.readiness.value,
            proposal_digest=(
                proposal_digest(preview.proposal_ref)
                if preview.proposal_ref
                else None
            ),
            preview_fingerprint=(
                preview_fingerprint(preview) if preview.proposal_ref else None
            ),
        )

        if preview.readiness is not ProposalReadiness.READY:
            # Truthful owner projection — the specialist answered the
            # prepare call but produced no confirmable proposal
            # (denial/invalid/expired/not-ready). Render what the owner
            # actually returned; never fabricate a preview.
            rendered = render_specialist_outcome_rich(
                outcome, field_labels=self._field_labels
            )
            note = _READINESS_NOTE.get(preview.readiness)
            limitations = tuple(rendered.limitations) + (
                (note,) if note else ()
            )
            return self._outcome_attempt(
                group_key,
                remote_name,
                remote_name,
                group,
                outcome,
                correlation,
                content=rendered.content,
                markdown_content=rendered.markdown,
                limitations=limitations,
            )

        act_capability = _find_act_capability(
            group, require_proposal_handle=True
        )
        digest = proposal_digest(preview.proposal_ref)
        fingerprint = preview_fingerprint(preview)

        # Deterministic provider-neutral confirmation decision
        # (§6.140): the structural confirmation requirement on the
        # owner PREPARE proposal is the sole authority — the model
        # never decides destructiveness, no owner-vocabulary op policy
        # is consulted, and malformed/absent policy fails closed as an
        # owner-contract defect rather than degrading into auto-ACT or
        # a lazy confirmation prompt.
        confirmation_policy = _effective_confirmation_policy(preview)
        self._audit(
            stage="CONFIRMATION_POLICY",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=confirmation_policy,
            proposal_digest=digest,
            preview_fingerprint=fingerprint,
        )
        if confirmation_policy == CONFIRMATION_POLICY_INVALID:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="owner_policy_invalid",
                content=(
                    "O proprietário não declarou uma política de "
                    "confirmação consistente para esta operação — "
                    "nenhuma escrita foi executada."
                ),
            )
        if act_capability is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                content=(
                    "A proposta foi preparada pelo especialista, mas "
                    "nenhuma capacidade de confirmação (ACT) está "
                    "anunciada pelo proprietário — a escrita não pode "
                    "prosseguir."
                ),
            )
        # Post-PREPARE operation-bound scope choice (B2 closure,
        # §6.184): a free-text MESSAGE is never ACT-eligible — a READY
        # proposal is ALWAYS held as a backend pending write awaiting a
        # typed decision (APPLY_PREPARED/REJECT_PREPARED) bound to the
        # exact proposal on a later turn. The owner confirmation policy
        # keeps its own meaning: `explicit_user_confirmation=false`
        # does NOT skip the user's execution-scope choice — it only
        # declares that the bound APPLY needs no ADDITIONAL owner
        # confirmation; `true` makes the same bound decision satisfy
        # the owner confirmation too. Either way, zero ACT this turn.
        pending_purpose = (
            PENDING_PURPOSE_SCOPE_PLUS_CONFIRMATION
            if confirmation_policy == CONFIRMATION_POLICY_CONFIRM
            else PENDING_PURPOSE_SCOPE_CHOICE
        )
        decision = evaluate_write_continuation(
            capability_live=act_capability is not None,
            confirmation_required=True,
            preview=preview,
            confirmation=None,
            now_epoch=time.time(),
        )
        self._audit(
            stage="DECISION_GATE",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=decision.status.value,
            proposal_digest=digest,
            preview_fingerprint=fingerprint,
            execution_mode=pending_purpose,
        )

        now = time.time()
        expires = preview.expires_at_epoch
        if expires is None:
            expires = now + DEFAULT_PENDING_TTL_SECONDS
        pending = PendingWrite(
            digest=digest,
            capability_ref=capability_ref,
            group_key=group_key,
            actor_user_id=str(actor_user_id or ""),
            session_id=str(session_id or ""),
            expires_at_epoch=expires,
            created_at_epoch=now,
            preview=preview,
            act_remote_capability=act_capability.remote_name,
            correlation_id=correlation,
            pending_purpose=pending_purpose,
        )
        self._pending_writes.put(pending)
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
            correlation_id=correlation,
            outcome=outcome,
            provenance=self._provenance(
                group_key, remote_name, remote_name, group, outcome
            ),
            content=_preview_render(preview),
            confirmation_context={
                "session_id": pending.session_id,
                "capability_ref": capability_ref,
                "proposal_digest": digest,
                "preview_fingerprint": fingerprint,
                "expires_at_epoch": expires,
                "pending_purpose": pending_purpose,
            },
            limitations=outcome.limitations,
        )

    def _attempt_direct_act(
        self,
        group_key: str,
        descriptor: ProviderCapability,
        arguments: Mapping[str, Any],
        group: CapabilityGroup,
        actor_user_id: str | None,
        session_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Gate a model-selected ACT capability — always fail closed.

        A cold ACT selection on a free-text MESSAGE can never execute
        (B2 closure, §6.184 §5): an ACT whose owner schema requires
        ``proposal_handle`` lacks the live PREPARE proposal it needs,
        and an ACT-only capability has no owner-verified preview to
        which a typed APPLY_PREPARED decision could bind — the runtime
        must not fabricate one. Both are refused truthfully.
        """
        if prepare_only:
            # Execution ceiling: an ACT capability can never run while
            # the turn is capped at PREPARE.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="execution_ceiling",
                content=(
                    "Esta sessão está limitada a preparação — a "
                    "operação não foi executada."
                ),
            )
        capability_ref = f"{group_key}.{descriptor.remote_name}"
        keys, required = _schema_keys(descriptor)
        if PROPOSAL_HANDLE_FIELD in keys or PROPOSAL_HANDLE_FIELD in required:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                content=(
                    "Essa operação exige uma proposta preparada pelo "
                    "especialista. Peça a alteração primeiro para gerar "
                    "uma prévia confirmável."
                ),
            )
        # ACT-only without a verifiable owner PREPARE proposal (B2
        # closure §5): there is no owner-verified preview/digest to
        # which a typed APPLY_PREPARED decision could bind — the
        # runtime cannot fabricate a preview, so the cold ACT
        # selection is refused truthfully instead of executing or
        # staging an unverifiable pending intent.
        self._audit(
            stage="DECISION_GATE",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=descriptor.remote_name,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision="PRECONDITION_REQUIRED",
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.WRITE_REJECTED,
            correlation_id=correlation,
            error_code="precondition_required",
            content=(
                "Essa operação é uma escrita sem prévia verificável "
                "do especialista — a execução não pode prosseguir a "
                "partir de texto livre."
            ),
        )

    def _attempt_confirmation(
        self,
        confirmation_payload: Mapping[str, Any],
        *,
        actor_user_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Bind a structured confirmation to a pending write.

        Fail closed on every dimension: unknown/expired digest,
        actor/session/fingerprint mismatch, reclassified or removed
        owner capability. The raw proposal handle stays backend-only —
        the wire carries digests only.
        """
        if prepare_only:
            # Execution ceiling (LOOP-03R1): no confirmation can reach
            # ACT while the turn is capped at PREPARE.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="execution_ceiling",
                content=(
                    "Esta sessão está limitada a preparação — a "
                    "operação não foi executada."
                ),
            )
        digest = str(confirmation_payload.get("proposal_digest") or "")
        record = self._pending_writes.get(digest)
        if record is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_unknown",
                content=(
                    "Nenhuma operação pendente corresponde a esta "
                    "confirmação — ela pode ter expirado ou já ter sido "
                    "respondida."
                ),
            )
        if str(actor_user_id or "") != record.actor_user_id:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.AUTHZ_DENIED,
                correlation_id=correlation,
                error_code="actor_mismatch",
                content="A confirmação não pertence a este usuário.",
            )
        session_id = str(confirmation_payload.get("session_id") or "")
        if not session_id or not record.session_id or (
            session_id != record.session_id
        ):
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="session_mismatch",
                content="A confirmação não pertence a esta sessão.",
            )
        fingerprint = str(
            confirmation_payload.get("preview_fingerprint") or ""
        )
        raw_decision = str(confirmation_payload.get("decision") or "")
        try:
            decision = ConfirmationDecision(raw_decision.upper())
        except ValueError:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_invalid",
                content="Decisão de confirmação inválida.",
            )

        if record.preview is None:
            # Pending intents without an owner-verified preview are no
            # longer created (§6.184 §5) — a bound decision has no
            # verified proposal to bind to, so it fails closed.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_unknown",
                content=(
                    "Nenhuma proposta preparada corresponde a esta "
                    "confirmação."
                ),
            )
        return self._confirm_proposal(
            record, decision, fingerprint, actor_user_id, session_id,
            correlation, deadline,
        )

    def _confirm_proposal(
        self,
        record: PendingWrite,
        decision: ConfirmationDecision,
        fingerprint: str,
        actor_user_id: str | None,
        session_id: str,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        preview = record.preview
        assert preview is not None
        bound = bind_confirmation(
            preview=preview,
            confirmation=StructuredConfirmation(
                actor_user_id=str(actor_user_id or ""),
                session_id=session_id,
                capability_ref=record.capability_ref,
                proposal_digest=record.digest,
                preview_fingerprint=fingerprint,
                decision=decision,
                occurred_at_epoch=time.time(),
            ),
            expected_actor_id=record.actor_user_id,
            expected_session_id=record.session_id,
            now_epoch=time.time(),
        )
        # Validate before claiming: an invalid fingerprint, actor or
        # session may NEVER consume another caller's legitimate pending
        # proposal. A validated CONFIRM/REJECT still needs to win the
        # exclusive claim below before any ACT can proceed.
        if bound.state not in (
            ConfirmationState.CONFIRMED,
            ConfirmationState.REJECTED,
        ):
            reasons = ",".join(r.value for r in bound.reason_codes)
            self._audit(
                stage="CONFIRMATION_INVALID",
                capability_ref=record.capability_ref,
                group_id=record.group_key,
                owner_capability=preview.owner_capability,
                correlation_id=correlation,
                actor_user_id=actor_user_id,
                decision=bound.state.value,
                proposal_digest=record.digest,
                preview_fingerprint=fingerprint,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_mismatch",
                content=(
                    "A confirmação não corresponde à proposta exata "
                    f"({reasons}). Nenhuma escrita foi executada."
                ),
            )
        # RW-01: validated binding alone is NOT a winning claim.
        # Two requests can read the same pending record concurrently;
        # only the atomic, identity-checked consumer may proceed to ACT.
        # Do not hold the store lock across owner/network calls.
        claimed = self._pending_writes.take_if_current(
            record.digest, record
        )
        if claimed is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_unknown",
                content=(
                    "Esta operação já foi respondida ou expirou. "
                    "Nenhuma escrita foi executada por esta decisão."
                ),
            )
        self._audit(
            stage="CONFIRMATION_BOUND",
            capability_ref=record.capability_ref,
            group_id=record.group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=bound.state.value,
            proposal_digest=record.digest,
            preview_fingerprint=fingerprint,
        )
        if bound.state is ConfirmationState.REJECTED:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                content="Operação cancelada — nenhuma escrita foi executada.",
            )
        # CONFIRMED still authorizes nothing: fresh live revalidation of
        # the owner surface precedes the ACT call, and live Core/Domain
        # AuthZ is enforced by the owner.
        #
        # Pending purpose (§6.184): `execution_scope_choice` — the owner
        # declared explicit_user_confirmation=false, so the bound APPLY
        # is the user's scope choice ONLY; it is NOT an owner
        # confirmation and must not reach the owner as one (confirmed=
        # False argument, reduction-only gate). `execution_scope_plus_
        # owner_confirmation` (and any legacy/unknown purpose — the
        # fail-safe direction) — the same bound decision additionally
        # satisfies the owner-required confirmation.
        requires_owner_confirmation = (
            record.pending_purpose != PENDING_PURPOSE_SCOPE_CHOICE
        )
        return self._execute_prepared_act(
            group_key=record.group_key,
            capability_ref=record.capability_ref,
            act_remote_capability=record.act_remote_capability,
            preview=preview,
            digest=record.digest,
            fingerprint=fingerprint,
            confirmation=bound if requires_owner_confirmation else None,
            execution_mode=(
                "explicit_user_confirmation"
                if requires_owner_confirmation
                else "execution_scope_choice"
            ),
            actor_user_id=actor_user_id,
            correlation=correlation,
            deadline=deadline,
        )

    def _execute_prepared_act(
        self,
        *,
        group_key: str,
        capability_ref: str,
        act_remote_capability: str | None,
        preview: WriteProposalPreview,
        digest: str,
        fingerprint: str,
        confirmation: ConfirmationRecord | None,
        execution_mode: str,
        actor_user_id: str | None,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """The single governed ACT execution path.

        A bound explicit user confirmation and an owner-declared
        direct policy converge here — fresh surface revalidation,
        capability-liveness check, decision gate, owner-invoked ACT
        and postcondition verification are identical for both; only
        the confirmation input differs. No path past this point can
        skip a gate.
        """
        try:
            group = self._fresh_group(group_key, correlation, deadline)
        except CapabilityProviderError as exc:
            return _error_attempt(correlation, exc)
        if group is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="capability_group_offline",
                content=(
                    "O grupo de capacidades não está mais disponível. "
                    "Nenhuma escrita foi executada."
                ),
            )
        act_capability = (
            next(
                (
                    cap
                    for cap in group.capabilities
                    if cap.remote_name == act_remote_capability
                ),
                None,
            )
            if act_remote_capability
            else _find_act_capability(group, require_proposal_handle=True)
        )
        decision_gate = evaluate_write_continuation(
            capability_live=(
                act_capability is not None
                and invocable_in_interactive_phase(
                    act_capability.operation_class
                )
            ),
            confirmation_required=(
                execution_mode == "explicit_user_confirmation"
            ),
            preview=preview,
            confirmation=confirmation,
            now_epoch=time.time(),
        )
        self._audit(
            stage="DECISION_GATE",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=decision_gate.status.value,
            proposal_digest=digest,
            preview_fingerprint=fingerprint,
            execution_mode=execution_mode,
        )
        if decision_gate.status.value != "READY_FOR_LIVE_REVALIDATION":
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code=",".join(
                    r.value for r in decision_gate.reason_codes
                ),
                content=(
                    "A capacidade de confirmação não está mais "
                    "disponível na superfície viva do especialista. "
                    "Nenhuma escrita foi executada."
                ),
            )
        assert act_capability is not None
        act_arguments = _act_arguments(
            act_capability,
            preview.proposal_ref,
            confirmed=confirmation is not None,
        )
        return self._invoke_act(
            group,
            act_capability.remote_name,
            act_arguments,
            correlation,
            deadline,
            actor_user_id=actor_user_id,
            capability_ref=(
                f"{group_key}.{act_capability.remote_name}"
            ),
            execution_mode=execution_mode,
        )

    def _invoke_act(
        self,
        group: CapabilityGroup,
        remote_name: str,
        arguments: Mapping[str, Any],
        correlation: str,
        deadline: TurnDeadline | None = None,
        *,
        actor_user_id: str | None,
        capability_ref: str,
        execution_mode: str | None = None,
    ) -> GovernedCapabilityAttempt:
        """Invoke the owner ACT capability and project the outcome.

        A technical success is never projected as a verified business
        outcome — only the owner's explicit ``verified`` postcondition
        evidence produces VERIFIED.
        """
        group_key = f"{group.provider_id}:{group.group_id}"
        self._audit(
            stage="ACT_ATTEMPT",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=remote_name,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision="INVOKED",
            execution_mode=execution_mode,
        )
        try:
            outcome = self._invoke(
                group, remote_name, dict(arguments), correlation,
                deadline,
            )
        except CapabilityProviderError as exc:
            _logger.info(
                "orchestration stage=act_invoke decision=error "
                "error_code=%s detail=%s correlation_id=%s",
                exc.code,
                exc.message[:240],
                correlation,
            )
            return _error_attempt(correlation, exc)
        projection = project_write_outcome(
            capability_ref=capability_ref,
            remote_capability=remote_name,
            owner_payload=outcome.structured or {},
            specialist_id=group_key,
            correlation_id=correlation,
            occurred_at=outcome.provenance.observed_at,
            limitations=outcome.limitations,
        )
        self._audit(
            stage="OUTCOME_VERIFIED",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=remote_name,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=projection.status.value,
            execution_mode=execution_mode,
        )
        rendered = render_specialist_outcome_rich(
            outcome, field_labels=self._field_labels
        )
        content = rendered.content
        limitations = rendered.limitations
        markdown_content = rendered.markdown
        note = _OUTCOME_NOTE.get(projection.status)
        if note is not None:
            content = f"{content}\n\n{note}" if content else note
            if markdown_content is not None:
                markdown_content = f"{markdown_content}\n\n{note}"
        return self._outcome_attempt(
            group_key,
            remote_name,
            remote_name,
            group,
            outcome,
            correlation,
            content=content,
            markdown_content=markdown_content,
            limitations=limitations,
        )

    def _provenance(
        self,
        group_key: str,
        remote_used: str,
        action_id: str,
        group: CapabilityGroup,
        outcome: SpecialistOutcome,
    ):
        """Bounded user-facing provenance of one owner invocation."""
        source = group.source or SourceRef(
            source_id=group.owner_ref,
            source_system=group.owner_ref,
            provider_name=group.display_name,
        )
        return GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id=source.source_id,
                    source_system=source.source_system,
                    provider_name=source.provider_name,
                    observed_at=outcome.provenance.observed_at,
                ),
            ),
            specialist_id=outcome.provenance.specialist_id,
            remote_capability=outcome.provenance.remote_name,
            action_id=action_id,
            protocol=outcome.provenance.protocol.value,
            observed_at=outcome.provenance.observed_at,
            correlation_id=outcome.provenance.correlation_id,
            is_complete=outcome.is_complete,
            provider_id=group.provider_id,
            capability_group_id=group.group_id,
        )


    # ---- CRI E3 — grounded conversational composition ------------


    def _outcome_attempt(
        self,
        group_key: str,
        remote_used: str,
        action_id: str,
        group: CapabilityGroup,
        outcome: SpecialistOutcome,
        correlation: str,
        *,
        content: str | None = None,
        limitations: tuple[str, ...] | None = None,
        markdown_content: str | None = None,
        extra_source_refs: tuple[SourceRef, ...] = (),
        input_text: str | None = None,
        composition_mode: str | None = None,
    ) -> GovernedCapabilityAttempt:
        """Assemble a SUCCESS attempt from an owner outcome.

        ``extra_source_refs`` appends additional bounded business
        sources (multi-source corroboration) after the primary ref —
        deduplicated, deterministic order. ``input_text`` enables
        goal-aligned deterministic rendering when synthesis demotes.
        ``composition_mode`` carries the effective answer composition
        observed at this seam (e.g. ``"cri"``) — presentation-only,
        never authority. ``markdown_content`` carries the deterministic
        markdown projection of the same admitted structured payload —
        callers that synthesize prose pass ``content`` without it, so
        model text never becomes ``markdown_safe`` (Category C).
        """
        binding = GovernedCapabilityBinding(
            binding_id=f"{group_key}.{remote_used}",
            group_key=group_key,
            remote_capability=remote_used,
            action_id=action_id,
            source=(
                group.source
                or SourceRef(
                    source_id=group.owner_ref,
                    source_system=group.owner_ref,
                    provider_name=group.display_name,
                )
            ),
            provider_id=group.provider_id,
            capability_group_id=group.group_id,
        )

        def _render(out: SpecialistOutcome) -> RenderedSpecialistOutcome:
            return render_specialist_outcome_rich(
                out,
                input_text=input_text,
                field_labels=self._field_labels,
            )

        if content is None and not extra_source_refs:
            attempt = _success_attempt(
                correlation_id=correlation,
                binding=binding,
                outcome=outcome,
                render=_render,
            )
            if composition_mode is not None:
                attempt = dataclasses.replace(
                    attempt, composition_mode=composition_mode
                )
            return attempt
        provenance = self._provenance(
            group_key, remote_used, action_id, group, outcome
        )
        if extra_source_refs:
            seen = {
                (ref.source_id, ref.source_system)
                for ref in provenance.source_refs
            }
            provenance = dataclasses.replace(
                provenance,
                source_refs=provenance.source_refs
                + tuple(
                    ref
                    for ref in extra_source_refs
                    if (ref.source_id, ref.source_system) not in seen
                ),
            )
        if content is None:
            rendered = render_specialist_outcome_rich(
                outcome,
                input_text=input_text,
                field_labels=self._field_labels,
            )
            content = rendered.content
            markdown_content = rendered.markdown
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            outcome=outcome,
            provenance=provenance,
            content=content,
            markdown_content=markdown_content,
            # Synthesized/alternate content never drops owner-reported
            # limitations — they stay attached to the attempt.
            limitations=(
                limitations
                if limitations is not None
                else outcome.limitations
            ),
            composition_mode=composition_mode,
        )

    def _audit(
        self,
        *,
        stage: str,
        capability_ref: str,
        group_id: str,
        owner_capability: str,
        correlation_id: str,
        actor_user_id: str | None,
        decision: str,
        proposal_digest: str | None = None,
        preview_fingerprint: str | None = None,
        execution_mode: str | None = None,
    ) -> None:
        """Bounded audit event — digest refs only, never raw handles."""
        _logger.info(
            "governed_write stage=%s decision=%s group_id=%s "
            "capability_ref=%s owner_capability=%s correlation_id=%s "
            "actor_user_id=%s proposal_digest=%s preview_fingerprint=%s "
            "execution_mode=%s",
            stage,
            decision,
            group_id,
            capability_ref,
            owner_capability,
            correlation_id,
            actor_user_id or "",
            proposal_digest or "",
            preview_fingerprint or "",
            execution_mode or "",
        )

    # ---------------- internals ----------------


    def _groups(
        self,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> tuple[dict[str, CapabilityGroup], list[str]]:
        """Live provider capability groups keyed by group key."""
        groups: dict[str, CapabilityGroup] = {}
        failures: list[str] = []
        for provider_id, provider in self._providers.items():
            # LOOP-03R2A-R1: each provider consultation is bounded by
            # the remaining turn budget — never starts exhausted and
            # never widens the provider's own stage max.
            if deadline is not None:
                deadline.check("surface_list")
            if _cancel_observed():
                raise _TurnCancelled()
            try:
                surface = provider.list_groups(
                    correlation_id=correlation,
                    timeout_seconds=(
                        deadline.remaining_seconds()
                        if deadline is not None
                        else None
                    ),
                )
            except CapabilityProviderError as exc:
                # One bounded retry for a transient listing failure.
                # A timeout is not proof the owner has no capabilities.
                retried = False
                if (
                    deadline is not None
                    and deadline.remaining_seconds() > 15
                    and _listing_failure_is_transient(exc.code)
                ):
                    try:
                        surface = provider.list_groups(
                            correlation_id=correlation,
                            timeout_seconds=min(
                                15.0, deadline.remaining_seconds()
                            ),
                        )
                        retried = True
                    except CapabilityProviderError as retry_exc:
                        failures.append(exc.code)
                        failures.append(retry_exc.code)
                        continue
                if not retried:
                    failures.append(exc.code)
                    continue
            # A provider that overran the remaining budget may not
            # contribute results to this turn — fail truthfully.
            if deadline is not None:
                deadline.check("surface_list")
            failures.extend(surface.failures)
            for group in surface.groups:
                groups[f"{provider_id}:{group.group_id}"] = group
        return groups, failures

    def _fresh_group(
        self,
        group_key: str,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> CapabilityGroup | None:
        """Re-resolve one group live — provider-side revalidation."""
        provider_id, _, group_id = group_key.partition(":")
        provider = self._providers.get(provider_id)
        if provider is None or not group_id:
            return None
        if deadline is not None:
            deadline.check("surface_relist")
        if _cancel_observed():
            raise _TurnCancelled()
        surface = provider.list_groups(
            correlation_id=correlation,
            timeout_seconds=(
                deadline.remaining_seconds()
                if deadline is not None
                else None
            ),
        )
        if deadline is not None:
            deadline.check("surface_relist")
        return next(
            (g for g in surface.groups if g.group_id == group_id), None
        )




    def _model_stage_proposal(
        self,
        input_text: str,
        *,
        block_tag: str,
        block_payload: str,
        instruction_id: str,
        instruction: str,
        instruction_lineage: tuple[str, ...],
        expected_fields: tuple[str, ...],
        input_kind: str,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str | None = None,
        deadline: TurnDeadline | None = None,
    ) -> Mapping[str, Any] | None:
        """One bounded model stage — raw structured proposal or None.

        Shared invocation mechanics for every orchestrator-owned model
        call: deadline check, stage-timeout resolution with cold-start
        headroom, minimum-viable-budget fail-fast, request assembly,
        error/timeout taxonomy and bounded stage logging. Per-purpose
        proposal validation stays with each caller.
        """
        if self._invoke_model is None or self._model_ref is None:
            return None
        if deadline is not None:
            try:
                deadline.check("model_propose")
            except TurnBudgetExhausted as exc:
                raise _StageDeadlineExceeded(
                    "turn_budget_exhausted"
                ) from exc
        # CP5/R3: cancellation observed mid-attempt stops the next real
        # operation — no new model call (and no replay) after a
        # disconnect; the attempt unwinds to the honest terminal.
        if _cancel_observed():
            raise _TurnCancelled()
        # CP4 governed resume: a recorded proposal replays only for a
        # byte-identical stage input — completed typed work survives a
        # downstream timeout without re-spending the model, and every
        # deterministic gate downstream still re-validates it against
        # the fresh live surface.
        resume_state = _RESUME_STATE.get()
        stage_key = _resume_stage_key(
            instruction_id, input_text, block_tag, block_payload
        )
        if resume_state is not None and stage_key in resume_state.proposals:
            _logger.info(
                "orchestration stage=model_propose decision=resumed "
                "purpose=%s correlation_id=%s",
                instruction_id,
                correlation or "",
            )
            return resume_state.proposals[stage_key]
        stage_timeout = (
            deadline.stage_timeout(self._model_stage_timeout_seconds)
            if deadline is not None
            else self._model_stage_timeout_seconds
        )
        # Honest stop: do not start a model stage that cannot finish
        # usefully within the remaining turn budget.
        if stage_timeout < MIN_VIABLE_MODEL_STAGE_SECONDS:
            _logger.info(
                "orchestration stage=model_propose "
                "decision=budget_too_small purpose=%s "
                "remaining_ms=%d correlation_id=%s",
                instruction_id,
                int(stage_timeout * 1000),
                correlation or "",
            )
            raise _StageDeadlineExceeded("turn_budget_exhausted")
        workspace_block = (
            "\n<workspace_context>\n"
            + workspace_context.to_prompt_block()
            + "\n</workspace_context>"
            if workspace_context is not None
            else ""
        )
        # Doc 103: governed retry INSIDE one logical model call — the
        # same bounded request may be invoked at most
        # LLM_CALL_MAX_ATTEMPTS times for recoverable classes (call
        # timeout, transient provider failure, invalid structured
        # output), only while budget remains and no cancellation was
        # observed. Never a retry of the turn, the MCP invoke or any
        # material operation.
        call_attempt = 0
        while True:
            call_attempt += 1
            # Per-call ceiling: min(60s stage cap, remaining budget).
            call_timeout = (
                min(stage_timeout, deadline.remaining_seconds())
                if deadline is not None
                else stage_timeout
            )
            if call_timeout < MIN_VIABLE_MODEL_STAGE_SECONDS:
                raise _StageDeadlineExceeded("turn_budget_exhausted")
            # Stage 6 budget attribution: budget still available when
            # this invocation was granted its timeout.
            call_remaining_ms = (
                int(deadline.remaining_seconds() * 1000)
                if deadline is not None
                else None
            )
            started = time.monotonic()
            try:
                result = self._invoke_model.execute(
                    ModelInvocationRequest(
                        invocation_id=ModelInvocationId(str(uuid.uuid4())),
                        model_ref=self._model_ref,
                        prior_context=prior_turns,
                        input_text=(
                            "<user_message>\n"
                            + input_text
                            + "\n</user_message>"
                            + workspace_block
                            + "\n<"
                            + block_tag
                            + ">\n"
                            + block_payload
                            + "\n</"
                            + block_tag
                            + ">"
                        ),
                        task_purpose_id=instruction_id,
                        output_schema_id=instruction_id,
                        output_schema_version=SELECTION_INSTRUCTION_VERSION,
                        expected_fields=expected_fields,
                        instruction_lineage=instruction_lineage,
                        instruction_content=instruction,
                        timeout_seconds=call_timeout,
                        declared_epistemic_class=EpistemicClass.HYPOTHESIS,
                        untrusted_external_metadata={
                            "interaction_surface": "delia-mfe",
                            "input_kind": input_kind,
                        },
                    )
                )
                break
            except ModelInvocationError as exc:
                # Prompt 5: a REAL model call that failed or timed out —
                # counted as a call; usage stays absent (never
                # fabricated).
                ledger = current_call_ledger()
                if ledger is not None:
                    ledger.record_error(
                        stage=instruction_id,
                        finish_status=(
                            "timeout" if exc.code == TIMEOUT else "error"
                        ),
                        attempt=_ATTEMPT_INDEX.get(),
                        duration_ms=int(
                            (time.monotonic() - started) * 1000
                        ),
                        budget_remaining_ms=call_remaining_ms,
                        error_code=exc.code,
                        context_budget=getattr(
                            exc, "context_budget", None
                        ),
                    )
                _logger.info(
                    "orchestration stage=model_propose decision=error "
                    "purpose=%s error_code=%s call_attempt=%d "
                    "timing_ms=%d correlation_id=%s",
                    instruction_id,
                    exc.code,
                    call_attempt,
                    int((time.monotonic() - started) * 1000),
                    correlation or "",
                )
                if (
                    instruction_id == INTERACTION_ADMISSION_INSTRUCTION_ID
                    and exc.code == TIMEOUT
                ):
                    # Admission is a classifier. A timeout already
                    # consumed its useful bound; repeating it delays
                    # the live catalog and the owner reads that must
                    # still fit in the same turn.
                    raise _StageDeadlineExceeded("model_timeout") from exc
                if not call_retry_eligible(
                    exc.code, call_attempt, self._llm_call_max_attempts
                ):
                    # LOOP-03R2A: a model-stage TIMEOUT is a governed
                    # orchestration failure — it terminates at the
                    # attempt boundary, never as a NOT_APPLICABLE that
                    # degrades into a general-model answer.
                    if exc.code == TIMEOUT:
                        raise _StageDeadlineExceeded(
                            "model_timeout"
                        ) from exc
                    return None
                # Cancellation between retries must not start a new
                # real call — unwind to the honest terminal.
                if _cancel_observed():
                    raise _TurnCancelled()
                _emit_activity(
                    phase=ActivityPhase.CONTINUING,
                    correlation=correlation,
                )
                _logger.info(
                    "orchestration stage=model_propose decision=retry "
                    "purpose=%s call_attempt=%d correlation_id=%s",
                    instruction_id,
                    call_attempt + 1,
                    correlation or "",
                )
                continue
        # LOOP-03R1 (latency): bounded stage timing per proposal
        # purpose — no payload, no user text, no values.
        _logger.info(
            "orchestration stage=model_propose decision=ok "
            "purpose=%s timing_ms=%d correlation_id=%s",
            instruction_id,
            int((time.monotonic() - started) * 1000),
            correlation or "",
        )
        # Prompt 5: a REAL model call completed — provider usage and
        # measured duration were already carried by
        # ModelInvocationResult; record them verbatim for the
        # presentation-only observability projection.
        ledger = current_call_ledger()
        if ledger is not None:
            ledger.record_result(
                stage=instruction_id,
                result=result,
                attempt=_ATTEMPT_INDEX.get(),
                budget_remaining_ms=call_remaining_ms,
            )
        proposal = result.structured_output
        if not isinstance(proposal, Mapping):
            return None
        if resume_state is not None:
            resume_state.proposals[stage_key] = proposal
        return proposal

    def _propose(
        self,
        input_text: str,
        *,
        block_tag: str,
        block_payload: str,
        instruction_id: str,
        instruction: str,
        expected_fields: tuple[str, ...],
        input_kind: str,
        allowed_keys: frozenset[str],
        instruction_version: str | None = None,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str | None = None,
        deadline: TurnDeadline | None = None,
    ) -> Mapping[str, Any] | None:
        """One bounded model proposal — structured output only."""
        proposal = self._model_stage_proposal(
            input_text,
            block_tag=block_tag,
            block_payload=block_payload,
            instruction_id=instruction_id,
            instruction=instruction,
            instruction_lineage=_lineage(
                instruction_id,
                instruction,
                instruction_version or SELECTION_INSTRUCTION_VERSION,
            ),
            expected_fields=expected_fields,
            input_kind=input_kind,
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return None
        # Surplus keys (e.g. adapter-suggested "limitations" on a
        # selection-only schema) must not discard a valid proposal —
        # Stage 05 live: grounded_synthesis returned ok then prior
        # continuity saw proposal_absent after a hard allowed_keys
        # reject. Project to the declared contract instead.
        extra = set(proposal) - allowed_keys
        if extra:
            _logger.info(
                "orchestration stage=model_propose "
                "decision=strip_extra purpose=%s extra_keys=%s "
                "correlation_id=%s",
                instruction_id,
                ",".join(sorted(str(k) for k in extra)[:8]),
                correlation or "",
            )
            proposal = {
                key: value
                for key, value in proposal.items()
                if key in allowed_keys
            }
        # Selection proposals may declare applicable=false with null
        # companion ids — do not reject solely for a missing
        # capability_group_id / remote_name in that case.
        applicable = proposal.get("applicable")
        if isinstance(applicable, str):
            applicable = applicable.strip().lower() == "true"
        if applicable is False and "applicable" in expected_fields:
            return proposal
        if any(field not in proposal for field in expected_fields):
            return None
        return proposal

    # -------- C3-INTELLIGENCE-LOOP-01: bounded user-facing stages --------

    MAX_REPLAN_ROUNDS = 1











    def _admit_conversational_turn(
        self,
        input_text: str,
        *,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> tuple[str | None, bool]:
        """Cheap typed admission: non-operational turns skip selection.

        Returns ``(interaction_class, owner_required)``: the admitted
        class ("conversation", "explanation", "hypothetical" or
        "surface_inquiry") only when the model declares
        requires_owner_surface=false. ``owner_required`` is True when
        the proposal proceeded to the governed owner path (requires
        true, or operational/ambiguous class); False when admission
        never ran (budget skip, timeout, invalid proposal) or admitted
        a conversational class. Ambiguous/failed admission returns
        ``(None, False)`` and falls through to selection with the
        conversational fallback preserved (never invents business
        facts by skipping owners). "surface_inquiry" answers from the
        deterministic live-surface projection — still no owner
        invocation, but the live listing IS consulted.
        """
        # Q02-A: prior turns no longer skip admission — the model must
        # classify topic change vs operational continuity explicitly.
        remaining = deadline.remaining_seconds()
        if remaining < (
            MIN_VIABLE_MODEL_STAGE_SECONDS
            + CONVERSATIONAL_FALLBACK_RESERVE_SECONDS
        ):
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=budget_skip remaining_ms=%d "
                "correlation_id=%s",
                int(remaining * 1000),
                correlation,
            )
            return None, False
        try:
            proposal = self._propose(
                input_text,
                block_tag="admission",
                block_payload=(
                    '{"owner_surfaces":"live governed owner '
                    'surfaces exist; their catalog is listed '
                    'only after admission - decide whether '
                    'the request requires governed owner '
                    'data or can be answered '
                    'conversationally"}'
                ),
                instruction_id=INTERACTION_ADMISSION_INSTRUCTION_ID,
                instruction=self._instruction(INTERACTION_ADMISSION_INSTRUCTION_ID),
                expected_fields=(
                    "requires_owner_surface",
                    "interaction_class",
                ),
                input_kind="interaction_admission",
                allowed_keys=frozenset(
                    {
                        "requires_owner_surface",
                        "interaction_class",
                        "limitations",
                    }
                ),
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded:
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=budget_exhausted correlation_id=%s",
                correlation,
            )
            return None, False
        if proposal is None:
            return None, False
        raw_req = proposal.get("requires_owner_surface")
        if isinstance(raw_req, str):
            requires = raw_req.strip().lower() == "true"
        elif raw_req is True:
            requires = True
        elif raw_req is False:
            requires = False
        else:
            return None, False
        raw_class = proposal.get("interaction_class")
        if not isinstance(raw_class, str):
            return None, False
        interaction_class = raw_class.strip().lower()
        if interaction_class not in {
            "conversation",
            "explanation",
            "hypothetical",
            "operational",
            "surface_inquiry",
            "ambiguous",
        }:
            return None, False
        if interaction_class == "surface_inquiry" and requires:
            # Declared-invariant violation: the instruction defines
            # surface_inquiry as "requires stays false" — a true flag
            # in the same proposal makes the pair contradictory.
            # One bounded re-proposal (same malformed-output precedent
            # as the other stages); if the contradiction repeats, the
            # instruction's own asymmetry rule applies — a missed
            # owner path fabricates business facts — so it resolves
            # to the owner path, never the listing.
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=surface_inquiry_requires_contradiction "
                "correlation_id=%s",
                correlation,
            )
            try:
                retry = self._propose(
                    input_text,
                    block_tag="admission",
                    block_payload=(
                        '{"owner_surfaces":"live governed owner '
                        'surfaces exist; their catalog is listed '
                        'only after admission - decide whether '
                        'the request requires governed owner '
                        'data or can be answered '
                        'conversationally"}'
                    ),
                    instruction_id=INTERACTION_ADMISSION_INSTRUCTION_ID,
                    instruction=self._instruction(
                        INTERACTION_ADMISSION_INSTRUCTION_ID
                    ),
                    expected_fields=(
                        "requires_owner_surface",
                        "interaction_class",
                    ),
                    input_kind="interaction_admission",
                    allowed_keys=frozenset(
                        {
                            "requires_owner_surface",
                            "interaction_class",
                            "limitations",
                        }
                    ),
                    workspace_context=workspace_context,
                    prior_turns=prior_turns,
                    correlation=correlation,
                    deadline=deadline,
                )
            except _StageDeadlineExceeded:
                retry = None
            if isinstance(retry, Mapping):
                r_raw = retry.get("requires_owner_surface")
                r_class = retry.get("interaction_class")
                if (
                    isinstance(r_class, str)
                    and r_class.strip().lower() == "surface_inquiry"
                    and r_raw is False
                ):
                    # The retry produced the coherent pair — the
                    # surface listing stands.
                    return "surface_inquiry", True
            # Persistent contradiction: the typed class is the
            # semantic statement — the deterministic surface listing
            # is bounded live metadata and never fabricates business
            # facts, so it is the fail-safe resolution.
            return "surface_inquiry", True
        if interaction_class == "surface_inquiry":
            # The typed class is the semantic statement: a surface
            # inquiry is answered by the deterministic live-surface
            # projection — bounded, read-only, never an invocation.
            return interaction_class, True
        if requires or interaction_class in {"operational", "ambiguous"}:
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=owner_surface class=%s correlation_id=%s",
                interaction_class,
                correlation,
            )
            return None, True
        return interaction_class, False

    def _surface_inquiry_attempt(
        self,
        groups: Mapping[str, CapabilityGroup],
        failures: list[str],
        correlation: str,
    ) -> GovernedCapabilityAttempt:
        """Deterministic surface answer: the live listing projected
        verbatim — surface metadata observed this turn, never an
        invocation result and never an authorization claim."""
        content = _surface_inquiry_content(groups, failures)
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id=correlation,
            admission_outcome=SURFACE_INQUIRY_ADMISSION,
            content=content,
            limitations=(LIMITATION_CAPABILITY_SURFACE_LISTING,),
            markdown_content=content,
        )

    def _project_semantic_tool_catalog(
        self,
        *,
        correlation: str,
        deadline: TurnDeadline,
        actor_user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Live READ/DISCOVERY/ANALYSIS catalog for Agent tools (doc 231).

        Write classes are omitted. Entries are untrusted metadata —
        never authorization. Schemas are size-bounded. Live Core AuthZ
        is applied by ``_groups`` (request-scoped identity); the actor
        id is logged for audit lineage only.
        """
        groups, failures = self._groups(correlation, deadline)
        catalog: list[dict[str, Any]] = []
        for group in groups.values():
            for cap in group.capabilities:
                if cap.operation_class in _WRITE_OPERATION_CLASSES:
                    continue
                if cap.operation_class not in {
                    SpecialistOperationClass.READ,
                    SpecialistOperationClass.DISCOVERY,
                    SpecialistOperationClass.ANALYSIS,
                }:
                    continue
                schema = cap.input_schema if isinstance(
                    cap.input_schema, Mapping
                ) else {}
                # Bound schema projection — property names + types only.
                props = schema.get("properties") if isinstance(
                    schema.get("properties"), Mapping
                ) else {}
                slim_props = {
                    str(name): {
                        "type": (
                            spec.get("type")
                            if isinstance(spec, Mapping)
                            else None
                        ),
                        "description": (
                            str(spec.get("description") or "")[:160]
                            if isinstance(spec, Mapping)
                            else None
                        ),
                    }
                    for name, spec in list(props.items())[:24]
                }
                catalog.append(
                    {
                        "capability_id": cap.capability_id,
                        "group_id": group.group_id,
                        "provider_id": group.provider_id,
                        "remote_name": cap.remote_name,
                        "owner": cap.owner,
                        "operation_class": cap.operation_class.value,
                        "description": (cap.description or "")[:320],
                        "input_schema": {
                            "type": "object",
                            "properties": slim_props,
                            "required": list(schema.get("required") or [])[
                                :24
                            ],
                        },
                    }
                )
        bounded = catalog[:80]
        by_owner: dict[str, int] = {}
        for entry in bounded:
            owner = str(entry.get("owner") or entry.get("provider_id") or "?")
            by_owner[owner] = by_owner.get(owner, 0) + 1
        _logger.info(
            "orchestration stage=semantic_tool_catalog "
            "decision=project actor=%s catalog_len=%d "
            "owners=%s failures=%s correlation_id=%s",
            (actor_user_id or "")[:64] or "-",
            len(bounded),
            ",".join(f"{k}:{v}" for k, v in sorted(by_owner.items())[:12])
            or "-",
            ",".join(str(item) for item in failures[:8]) or "-",
            correlation,
        )
        _LAST_CATALOG_FAILURES.set(
            tuple(str(item) for item in failures[:8])
        )
        return bounded

    def _native_toolset_config(
        self,
        *,
        provider_id: str,
        group_id: str,
        timeout_seconds: float | None = None,
    ):
        """Delegate native-discovery config to the owning provider.

        Provider families without a native client surface simply
        contribute no toolset — ``None`` is honest absence, never an
        unauthenticated or synthesized config.
        """
        provider = self._providers.get(provider_id)
        resolve = getattr(provider, "native_toolset_config", None)
        if resolve is None:
            return None
        return resolve(group_id, timeout_seconds=timeout_seconds)

    def _governed_semantic_tool_invoke(
        self,
        *,
        capability_id: str,
        arguments: Mapping[str, Any],
        input_text: str,
        correlation: str,
        actor_user_id: str | None,
        session_id: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        prepare_only: bool,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt:
        """Single-capability Agent tool invoke under live gates (doc 231).

        Resolves ``capability_id`` on the fresh live surface, rejects
        write classes on this surface, validates arguments against the
        owner schema, and routes through ``_invoke_selected`` so
        discovery-first candidate binding stays Application-owned.

        AuthZ: live surface from ``_groups`` (Core identity already
        bound on the request). ``prepare_only`` cannot elevate writes —
        write classes are rejected on this tool surface. Actor/session
        are retained for audit lineage.
        """
        cap_id = (capability_id or "").strip()
        _logger.info(
            "orchestration stage=semantic_tool_invoke "
            "decision=start capability=%s actor=%s session=%s "
            "prepare_only=%s correlation_id=%s",
            cap_id[:120],
            (actor_user_id or "")[:64] or "-",
            (session_id or "")[:64] or "-",
            bool(prepare_only),
            correlation,
        )
        if not cap_id:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="capability_id_required",
            )
        groups, failures = self._groups(correlation, deadline)
        if not groups and failures:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                correlation_id=correlation,
                error_code=failures[0],
            )
        matched: tuple[str, CapabilityGroup, ProviderCapability] | None = None
        for group_key, group in groups.items():
            for cap in group.capabilities:
                if cap.capability_id == cap_id or (
                    f"{group.group_id}:{cap.remote_name}" == cap_id
                ):
                    matched = (group_key, group, cap)
                    break
            if matched is not None:
                break
        if matched is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="capability_not_on_surface",
            )
        group_key, group, descriptor = matched
        if descriptor.operation_class in _WRITE_OPERATION_CLASSES:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="write_capability_not_exposed_to_agent_tools",
            )
        # READ tool surface never executes prepare/act even when the
        # turn ceiling is prepare_only — writes stay on confirmation
        # chain. prepare_only is recorded for audit only.
        args = dict(arguments or {})
        # Candidate-bound capabilities declare ``candidate_token`` as a
        # required input the agent relays verbatim — it is owner-issued
        # opaque data, not an orchestration-control field the model
        # could forge into state (the owner validates it downstream).
        # ``validate_arguments`` denies ORCHESTRATED_FIELDS at the
        # parameter boundary by design, so the token is extracted here
        # as a bounded string and handed to ``_invoke_selected``, which
        # passes it back to the owner unchanged.
        relayed_candidate_token: str | None = None
        if _is_candidate_bound(descriptor):
            raw_token = args.get(CANDIDATE_TOKEN_FIELD)
            if raw_token is not None:
                if not (
                    isinstance(raw_token, str)
                    and raw_token.strip()
                    and len(raw_token.encode("utf-8")) <= 4096
                ):
                    return GovernedCapabilityAttempt(
                        status=GovernedCapabilityStatus.NOT_APPLICABLE,
                        correlation_id=correlation,
                        error_code="arguments_schema_rejected",
                    )
                relayed_candidate_token = raw_token.strip()
                args = {
                    k: v
                    for k, v in args.items()
                    if k != CANDIDATE_TOKEN_FIELD
                }
        # Generic schema binding: when the owner requires ``query`` and
        # the agent omitted it, bind the turn utterance. This does not
        # select a capability — the agent already chose the tool.
        args = _bind_missing_required_query(
            args,
            input_schema=descriptor.input_schema,
            input_text=input_text,
        )
        if descriptor.input_schema is not None:
            try:
                validated = _validate_instance(args, descriptor.input_schema)
            except Exception:
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    error_code="arguments_schema_rejected",
                )
            if validated is None:
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    error_code="arguments_schema_rejected",
                )
            args = dict(validated)
        if relayed_candidate_token is not None:
            args[CANDIDATE_TOKEN_FIELD] = relayed_candidate_token
        try:
            invoked = self._invoke_selected(
                group_key,
                descriptor.remote_name,
                args,
                group,
                input_text,
                correlation,
                prior_turns=prior_turns,
                deadline=deadline,
                workspace_context=workspace_context,
            )
        except CapabilityProviderError as exc:
            return _error_attempt(correlation, exc)
        except (_StageDeadlineExceeded, TurnBudgetExhausted, _TurnCancelled):
            raise
        except Exception:
            _logger.exception(
                "orchestration stage=semantic_tool_invoke "
                "decision=error capability=%s correlation_id=%s",
                cap_id,
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                correlation_id=correlation,
                error_code="semantic_tool_invoke_failed",
            )
        if invoked is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="owner_no_resolvable_candidate",
            )
        outcome, action_id, remote_used = invoked
        binding = GovernedCapabilityBinding(
            binding_id=f"{correlation}:{group.group_id}:{remote_used}",
            group_key=group_key,
            remote_capability=remote_used,
            action_id=str(action_id or remote_used),
            source=SourceRef(
                source_id=group.group_id,
                source_system=group.provider_id,
                provider_name=group.provider_id,
            ),
            provider_id=group.provider_id,
            capability_group_id=group.group_id,
        )

        def _render(out: SpecialistOutcome) -> RenderedSpecialistOutcome:
            return render_specialist_outcome_rich(
                out,
                input_text=input_text,
                invocation_arguments=args,
                field_labels=self._field_labels,
            )

        attempt = _success_attempt(
            correlation_id=correlation,
            binding=binding,
            outcome=outcome,
            render=_render,
        )
        # Tag pure discovery envelopes so finalize never treats catalog
        # / candidate lists as business facts (R2). When discovery-first
        # already chained to an owner READ (remote_used != discover
        # remote), the attempt IS business evidence — do not mask it.
        if descriptor.operation_class is SpecialistOperationClass.DISCOVERY:
            chained_owner_read = (
                str(remote_used or "").strip()
                and str(remote_used).strip() != str(descriptor.remote_name).strip()
            )
            if not chained_owner_read:
                limitations = tuple(attempt.limitations) + (
                    "discovery_metadata_observation",
                )
                return GovernedCapabilityAttempt(
                    status=attempt.status,
                    correlation_id=attempt.correlation_id,
                    content=attempt.content,
                    limitations=limitations,
                    error_code=attempt.error_code,
                    provenance=attempt.provenance,
                    outcome=attempt.outcome,
                    markdown_content=attempt.markdown_content,
                    admission_outcome=attempt.admission_outcome,
                    verified_composition=attempt.verified_composition,
                )
            _logger.info(
                "orchestration stage=semantic_tool_invoke "
                "decision=discovery_chained_read "
                "discover=%s read=%s action=%s correlation_id=%s",
                descriptor.remote_name,
                remote_used,
                action_id,
                correlation,
            )
        return attempt

    def _accept_semantic_investigation_plan(
        self,
        *,
        goal_class: str,
        comparison_requested: bool,
        target_identities: object,
        evidence_needed: object = (),
        business_subject: str | None = None,
        correlation: str,
    ) -> SemanticInvestigationPlan | None:
        """Validate Agent-declared investigation plan into typed contract.

        Reuses ``_TurnGoal`` vocabulary — no parallel goal model.
        """
        klass = (goal_class or "").strip()
        if klass not in self._GOAL_CLASSES:
            _logger.info(
                "orchestration stage=semantic_plan "
                "decision=invalid_class correlation_id=%s",
                correlation,
            )
            return None
        if klass == "compare":
            comparison_requested = True
        subject = (
            str(business_subject).strip()[:240] if business_subject else None
        ) or None
        goal = self._TurnGoal(
            goal_class=klass,
            comparison_requested=bool(comparison_requested),
            business_subject=subject,
            declared=True,
        )
        targets = _normalize_identity_tuple(target_identities)
        needed = _normalize_identity_tuple(evidence_needed) or targets
        return SemanticInvestigationPlan(
            goal=goal,
            target_identities=targets,
            evidence_needed=needed,
        )

    def _compose_observation_pair(
        self,
        *,
        left: GovernedCapabilityAttempt,
        right: GovernedCapabilityAttempt,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt | None:
        """Optional deterministic composition of two verified observations.

        Agent-requested analysis capability — not an intent router.
        Both sides must be business evidence with authoritative roots.
        """
        if not (
            _is_business_evidence_attempt(left)
            and _is_business_evidence_attempt(right)
        ):
            return None
        left_root = _authoritative_structure_root(left)
        right_root = _authoritative_structure_root(right)
        if (
            left_root is None
            or right_root is None
            or left_root.casefold() == right_root.casefold()
        ):
            return None
        left_records = _comparison_records(left.outcome)  # type: ignore[arg-type]
        right_records = _comparison_records(right.outcome)  # type: ignore[arg-type]
        composed = self._compose_multi_evidence(
            {left_root: left_records, right_root: right_records},
            "",
            correlation=correlation,
            workspace_context=workspace_context,
            deadline=deadline,
        )
        if composed is None:
            return None
        content, limitations, verdict = composed
        if verdict not in ("agreement", "differences_found"):
            return None
        verified = VerifiedCompositeEvidence(
            source_roots=(left_root, right_root),
            source_lineage=(
                left.provenance.source_refs,  # type: ignore[union-attr]
                right.provenance.source_refs,  # type: ignore[union-attr]
            ),
            observed_at=max(
                left.outcome.provenance.observed_at,  # type: ignore[union-attr]
                right.outcome.provenance.observed_at,  # type: ignore[union-attr]
            ),
            correlation_id=correlation,
            verdict=verdict,
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            content=content,
            limitations=tuple(limitations)[:24],
            verified_composition=verified,
        )

    def _finalize_semantic_investigation(
        self,
        *,
        input_text: str,
        collected: tuple[GovernedCapabilityAttempt, ...],
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
        unbound_outcome: str | None,
        plan: SemanticInvestigationPlan | None = None,
        clarification_question: str | None = None,
        composed_attempt: GovernedCapabilityAttempt | None = None,
        declared_answer: InvestigationAnswer | None = None,
    ) -> GovernedCapabilityAttempt:
        """Conclude from typed coverage + authoritative evidence."""
        terminal = _finalize_agent_collected_attempts(
            self,
            input_text=input_text,
            collected=collected,
            correlation=correlation,
            workspace_context=workspace_context,
            deadline=deadline,
            unbound_outcome=unbound_outcome,
            plan=plan,
            clarification_question=clarification_question,
            composed_attempt=composed_attempt,
        )
        return _apply_declared_answer(
            terminal=terminal,
            declared_answer=declared_answer,
            collected=collected,
            plan=plan,
            correlation=correlation,
            unbound_outcome=unbound_outcome,
        )









    def _invoke_selected(
        self,
        group_key: str,
        remote_name: str,
        arguments: dict[str, Any],
        group: CapabilityGroup,
        input_text: str,
        correlation: str,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        deadline: TurnDeadline | None = None,
        workspace_context: WorkspaceContext | None = None,
    ) -> tuple[SpecialistOutcome, str, str] | None:
        """Invoke honoring the owner's flow shape — deterministic only.

        No second semantic controller lives here: the Agent already
        selected the capability and produced the arguments. Application
        validates, binds candidates deterministically and invokes the
        owner. Returns (outcome, action_id, remote_name_used), or None
        when the owner produced no resolvable candidate (truthful
        NOT_APPLICABLE — the agent may then call the owner discovery
        tool itself and retry with an explicit candidate_token).
        """
        capabilities = {
            cap.remote_name: cap for cap in group.capabilities
        }
        selected = capabilities[remote_name]

        if _is_candidate_bound(selected):
            token = arguments.get(CANDIDATE_TOKEN_FIELD)
            if isinstance(token, str) and token.strip():
                # Agent-supplied owner-issued candidate handle: opaque
                # untrusted data passed back to the owner verbatim —
                # never synthesized here, never an authorization.
                inner = arguments.get("arguments")
                merged = (
                    validate_untyped_arguments(inner)
                    if isinstance(inner, Mapping)
                    else ({} if inner is None else None)
                )
                if merged is None:
                    return None
                outcome = self._invoke(
                    group,
                    remote_name,
                    {
                        CANDIDATE_TOKEN_FIELD: token.strip(),
                        "arguments": merged,
                    },
                    correlation,
                    deadline,
                )
                return outcome, remote_name, remote_name
            found = self._discover_candidate(
                group,
                input_text,
                correlation,
                deadline,
                prior_turns,
            )
            if found is None:
                return None
            candidate, _discovery_outcome = found
            if candidate is None:
                return None
            inner = arguments.get("arguments")
            merged = self._candidate_arguments(
                candidate,
                inner if isinstance(inner, Mapping) else {},
                input_text,
                correlation=correlation,
            )
            if merged is None:
                return None
            outcome = self._invoke(
                group,
                remote_name,
                {
                    CANDIDATE_TOKEN_FIELD: candidate[CANDIDATE_TOKEN_FIELD],
                    "arguments": merged,
                },
                correlation,
                deadline,
            )
            return (
                outcome,
                str(candidate.get("action_id") or remote_name),
                remote_name,
            )

        outcome = self._invoke(
            group, remote_name, arguments, correlation, deadline
        )
        if selected.operation_class.value == "DISCOVERY":
            # Owner discovery may return exactly one executable
            # candidate for a candidate-bound READ on the same
            # specialist — chain deterministically. Multiple usable
            # candidates are returned to the agent, never picked by a
            # second model stage; the agent selects via a follow-up
            # tool call carrying the chosen candidate_token.
            candidate = self._resolve_candidate(
                outcome.structured,
                input_text,
                prior_turns,
                workspace_context=workspace_context,
            )
            if candidate is None and not self._candidates_present(
                outcome.structured
            ):
                folded = _context_folded_discovery_query(
                    input_text, prior_turns
                )
                if folded is not None:
                    _logger.info(
                        "orchestration stage=discovery_retry "
                        "decision=context_folded correlation_id=%s",
                        correlation,
                    )
                    retry = self._invoke(
                        group,
                        remote_name,
                        {"query": folded},
                        correlation,
                        deadline,
                    )
                    candidate = self._resolve_candidate(
                        retry.structured,
                        input_text,
                        prior_turns,
                        workspace_context=workspace_context,
                    )
                    if candidate is None and not (
                        self._candidates_present(retry.structured)
                    ):
                        outcome = retry
            executors = [
                cap
                for cap in group.capabilities
                if cap.operation_class.value == "READ"
                and _is_candidate_bound(cap)
            ]
            if candidate is not None and len(executors) == 1:
                merged = self._candidate_arguments(
                    candidate,
                    arguments,
                    input_text,
                    correlation=correlation,
                )
                if merged is not None:
                    chained = self._invoke(
                        group,
                        executors[0].remote_name,
                        {
                            CANDIDATE_TOKEN_FIELD: candidate[
                                CANDIDATE_TOKEN_FIELD
                            ],
                            "arguments": merged,
                        },
                        correlation,
                        deadline,
                    )
                    return (
                        chained,
                        str(
                            candidate.get("action_id")
                            or executors[0].remote_name
                        ),
                        executors[0].remote_name,
                    )
            if self._candidates_present(outcome.structured):
                # Candidates visible to the agent through the bounded
                # tool projection — selection is the agent's next tool
                # call with the owner-issued token.
                return outcome, remote_name, remote_name
            # S2 (RQ-SA04 / D5): the DISCOVERY payload may itself
            # publish the answer — owner-authored catalog/guidance
            # sections projected deterministically; the search miss is
            # declared only when nothing projectable remains.
            content = None
            guidance = _deterministic_guidance_content(
                outcome.structured, field_labels=self._field_labels
            )
            if guidance is not None:
                content, _guidance_omitted = guidance
            if not content:
                content = _render_zero_candidate_discovery(
                    outcome.structured
                    if isinstance(outcome.structured, Mapping)
                    else None,
                    group,
                )
            _logger.info(
                "orchestration stage=discovery_terminal "
                "decision=%s eligible=%s correlation_id=%s",
                _discovery_empty_result_class(
                    outcome.structured
                    if isinstance(outcome.structured, Mapping)
                    else None
                ),
                _owner_eligible_action_count(
                    outcome.structured
                    if isinstance(outcome.structured, Mapping)
                    else None
                ),
                correlation,
            )
            truthful = dataclasses.replace(
                outcome,
                content_text=content,
                structured=None,
                contract_facts=_contract_fact_rows(outcome),
                projected_content=(
                    content if guidance is not None else None
                ),
            )
            return truthful, remote_name, remote_name
        return outcome, remote_name, remote_name

    def _discover_candidate(
        self,
        group: CapabilityGroup,
        input_text: str,
        correlation: str,
        deadline: TurnDeadline | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
    ) -> tuple[Mapping[str, Any] | None, SpecialistOutcome | None] | None:
        """Owner discovery flow: exactly one DISCOVERY capability must
        exist for the candidate-bound READ to be resolvable. On a
        zero-candidate miss with prior context, one bounded retry uses
        the context-folded query. Returns the resolved candidate (or
        None) plus the discovery envelope outcome."""
        discovery_caps = [
            cap
            for cap in group.capabilities
            if cap.operation_class.value == "DISCOVERY"
        ]
        if len(discovery_caps) != 1:
            return None
        outcome = self._invoke(
            group,
            discovery_caps[0].remote_name,
            {"query": input_text[:MAX_DISCOVERY_QUERY_CHARS]},
            correlation,
            deadline,
        )
        candidate = self._resolve_candidate(
            outcome.structured,
            input_text,
            (),
        )
        if candidate is not None:
            return candidate, outcome
        if self._candidates_present(outcome.structured):
            return None, outcome
        folded = _context_folded_discovery_query(input_text, prior_turns)
        if folded is None:
            return None, outcome
        _logger.info(
            "orchestration stage=discovery_retry "
            "decision=context_folded correlation_id=%s",
            correlation,
        )
        retry = self._invoke(
            group,
            discovery_caps[0].remote_name,
            {"query": folded},
            correlation,
            deadline,
        )
        return (
            self._resolve_candidate(
                retry.structured,
                input_text,
                (),
            ),
            retry,
        )

    @staticmethod
    def _candidates_present(
        structured: Mapping[str, object] | None,
    ) -> bool:
        if not isinstance(structured, Mapping):
            return False
        candidates = structured.get("candidates")
        return isinstance(candidates, (list, tuple)) and bool(candidates)

    def _resolve_candidate(
        self,
        structured: Mapping[str, object] | None,
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        workspace_context: "WorkspaceContext | None" = None,
    ) -> Mapping[str, Any] | None:
        """Resolve the owner candidate to chain — deterministic only.

        Exactly one live-token, non-dead-end candidate chains. Zero or
        ambiguous sets resolve to ``None`` — the candidates stay
        visible to the Agent through the discovery projection and the
        semantic pick happens as a native tool call carrying the
        owner-issued candidate_token, never as a second LLM selector.
        """
        if not isinstance(structured, Mapping):
            return None
        candidates = structured.get("candidates")
        if not isinstance(candidates, (list, tuple)):
            return None
        matching = [
            c
            for c in candidates
            if isinstance(c, Mapping)
            and isinstance(c.get(CANDIDATE_TOKEN_FIELD), str)
            and c[CANDIDATE_TOKEN_FIELD].strip()
        ]
        if not matching:
            return None
        literals = _resolvable_identifier_literals(
            workspace_context, prior_turns
        )
        usable = [
            c
            for c in matching
            if not _candidate_needs_missing_identifier(
                c, input_text, literals
            )
        ]
        if len(usable) == 1:
            return usable[0]
        return None

    def _candidate_arguments(
        self,
        candidate: Mapping[str, Any],
        proposed: Mapping[str, Any],
        input_text: str,
        correlation: str = "",
    ) -> dict[str, Any] | None:
        """Resolve inner args against the candidate's own schema.

        Deterministic validation only — the Agent already produced
        the arguments. When the proposal does not satisfy the owner
        schema, a single bounded utterance-identifier binding is the
        last deterministic resort; otherwise the call fails closed and
        the agent decides the retry.
        """
        schema = candidate.get("argument_schema")
        effective_schema: Mapping[str, Any] | None = None
        if isinstance(schema, Mapping):
            effective_schema = dict(schema)
        required_args = candidate.get("required_arguments")
        if isinstance(required_args, (list, tuple)) and required_args:
            effective_schema = (
                dict(effective_schema)
                if effective_schema is not None
                else {}
            )
            effective_schema["required"] = [
                str(r) for r in required_args
            ]
        if effective_schema is not None:
            merged = _validate_instance(dict(proposed), effective_schema)
        else:
            merged = (
                validate_untyped_arguments(proposed)
                if isinstance(proposed, Mapping)
                else None
            )
        if merged is not None:
            return merged
        fallback = _bind_identifier_args_from_utterance(
            effective_schema, input_text
        )
        if fallback is None:
            return None
        fallback_validated = (
            _validate_instance(fallback, effective_schema)
            if effective_schema is not None
            else fallback
        )
        if fallback_validated is None:
            return None
        _logger.info(
            "orchestration stage=candidate_arguments "
            "decision=utterance_identifier_bind keys=%s "
            "correlation_id=%s",
            ",".join(sorted(fallback_validated)),
            correlation,
        )
        return dict(fallback_validated)


    def _invoke(
        self,
        group: CapabilityGroup,
        remote_name: str,
        arguments: Mapping[str, Any],
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> SpecialistOutcome:
        """Dispatch one invocation through the owning provider adapter.

        The orchestrator never inspects the capability's binding —
        provider mechanics (transport, protocols, delegated
        credentials) stay inside the adapter.
        """
        capability = next(
            (
                cap
                for cap in group.capabilities
                if cap.remote_name == remote_name
            ),
            None,
        )
        if capability is None:
            raise CapabilityProviderError(
                "capability_not_on_surface",
                "capability is not on the live provider surface",
            )
        if deadline is not None:
            deadline.check("provider_invoke")
        # CP5/R3: cancellation observed mid-attempt stops the provider
        # call too — no new operation after a disconnect.
        if _cancel_observed():
            raise _TurnCancelled()
        # CP4 governed resume frontier — the capability is resolved
        # from the FRESH live group above, never from the checkpoint.
        # A recorded outcome replays only for an identical
        # non-mutating invocation; a PREPARE/ACT (or any class not
        # allowlisted) marks the frontier — once a material
        # invocation has started, no further attempt may run.
        resume_state = _RESUME_STATE.get()
        resumable = (
            capability.operation_class in _RESUMABLE_OPERATION_CLASSES
        )
        invoke_key = _resume_invoke_key(
            group.group_id, remote_name, arguments
        )
        if resume_state is not None:
            if not resumable:
                resume_state.mutating_invoke_started = True
            elif invoke_key in resume_state.invoke_outcomes:
                _logger.info(
                    "orchestration stage=provider_invoke "
                    "decision=resumed capability=%s.%s "
                    "correlation_id=%s",
                    group.group_id,
                    remote_name,
                    correlation,
                )
                return resume_state.invoke_outcomes[invoke_key]
        provider = self._providers.get(group.provider_id)
        if provider is None:
            raise CapabilityProviderError(
                "provider_unavailable",
                "capability provider is not configured",
            )
        started = time.monotonic()
        # LOOP-03R1 (observability): declared argument KEYS only —
        # never values, tokens, or payload content.
        arg_keys = ",".join(sorted(str(k) for k in arguments))[:200]
        # Real observation: the invocation is about to happen — emit the
        # semantic started event only at this boundary, never earlier.
        _emit_activity(
            phase=ActivityPhase.SOURCE_QUERY_STARTED,
            correlation=correlation,
            capability_ref=_activity_capability_ref(
                remote_name=remote_name,
                operation_class=capability.operation_class.value,
            ),
            **_group_activity_refs(group),
        )
        try:
            outcome = provider.invoke(
                capability,
                arguments,
                correlation_id=correlation,
                # LOOP-03R2A-R1: the invocation is bounded by the
                # remaining turn budget — the provider clamps to its
                # own stage max underneath.
                timeout_seconds=(
                    deadline.remaining_seconds()
                    if deadline is not None
                    else None
                ),
            )
        except CapabilityProviderError as exc:
            # Stage 6 attribution: a real owner-surface call that
            # failed — operational elapsed time, never model time.
            op_ledger = current_call_ledger()
            if op_ledger is not None:
                op_ledger.record_operational(
                    capability=remote_name,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    finish_status=(
                        "timeout"
                        if "timeout" in str(exc.code).lower()
                        else "error"
                    ),
                )
            # LOOP-03R1 (latency): bounded stage timing — declared keys
            # only, never values/tokens.
            _logger.info(
                "orchestration stage=provider_invoke decision=error "
                "capability=%s.%s class=%s arg_keys=%s timing_ms=%d "
                "correlation_id=%s",
                group.group_id,
                remote_name,
                capability.operation_class.value,
                arg_keys,
                int((time.monotonic() - started) * 1000),
                correlation,
            )
            _emit_activity(
                phase=ActivityPhase.SOURCE_QUERY_COMPLETED,
                state=ActivityState.FAILED,
                correlation=correlation,
                capability_ref=_activity_capability_ref(
                    remote_name=remote_name,
                    operation_class=capability.operation_class.value,
                ),
                outcome_ref=_activity_outcome_ref(
                    status=ActivityOutcomeStatus.ERROR
                ),
                **_group_activity_refs(group),
            )
            raise
        _logger.info(
            "orchestration stage=provider_invoke decision=ok "
            "capability=%s.%s class=%s arg_keys=%s timing_ms=%d "
            "correlation_id=%s",
            group.group_id,
            remote_name,
            capability.operation_class.value,
            arg_keys,
            int((time.monotonic() - started) * 1000),
            correlation,
        )
        # Stage 6 attribution: measured owner-surface execution time —
        # separated from semantic decision time in the turn ledger.
        op_ledger = current_call_ledger()
        if op_ledger is not None:
            op_ledger.record_operational(
                capability=remote_name,
                duration_ms=int((time.monotonic() - started) * 1000),
                finish_status="completed",
            )
        # The outcome provenance is the only legitimate protocol
        # evidence — it was actually observed on this invocation.
        _emit_activity(
            phase=ActivityPhase.SOURCE_QUERY_COMPLETED,
            state=(
                ActivityState.PARTIAL
                if outcome.status is SpecialistResultStatus.PARTIAL
                else ActivityState.COMPLETED
            ),
            correlation=correlation,
            capability_ref=_activity_capability_ref(
                remote_name=remote_name,
                protocol=outcome.provenance.protocol.value,
                operation_class=capability.operation_class.value,
            ),
            outcome_ref=_activity_outcome_summary(outcome),
            **_group_activity_refs(group),
        )
        # Only a verified non-mutating outcome is recorded — replay
        # applies to the identical invocation of a later attempt. It
        # is recorded BEFORE the post-invoke deadline check: the call
        # provably completed; a late deadline must not turn a finished
        # READ into a duplicated one on resume.
        # CP5/R1: only a COMPLETE, fully-postconditioned outcome is a
        # verifiable checkpoint — a partial/incomplete result is
        # degraded evidence, so the resumed attempt re-issues the same
        # non-mutating read instead of freezing it.
        if (
            resume_state is not None
            and resumable
            and outcome.is_complete
            and outcome.status is SpecialistResultStatus.COMPLETED
        ):
            resume_state.invoke_outcomes[invoke_key] = outcome
        # An outcome that arrives after the turn deadline may not be
        # processed — fail truthfully at the boundary.
        if deadline is not None:
            deadline.check("provider_invoke")
        return outcome
