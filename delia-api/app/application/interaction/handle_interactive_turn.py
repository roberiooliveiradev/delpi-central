"""HandleInteractiveConversationTurn — C3-INTERACTION-RUNTIME-01.

Smallest usable vertical slice: Core-authorized user -> request-scoped
InteractionSession -> USER_INPUT turn -> InvokeModel (existing port)
-> validated DELIA_RESULT turn -> bounded response.

Request-scoped only: no session persistence, no history, no business
reads, no RAG, no tool execution, no PREPARE/ACT.

C3-INTERACTION-CONTINUITY-01: bounded prior interaction context may be
carried through the request as untrusted transient data. It is validated
(kinds, epistemic admissibility, alternation, aggregate bound) and
forwarded to the model invocation port — it is never authority, memory,
or evidence.
"""

from __future__ import annotations

import dataclasses
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from app.application.interaction.activity import (
    ActivityEvent,
    ActivityEventSink,
    ActivityPhase,
    ActivityState,
    activity_sink_or_none,
)
from app.application.interaction.contracts import (
    LEGACY_CONFIRMATION_LABELS,
    TURN_COMMAND_MESSAGE,
    TURN_COMMAND_APPLY_PREPARED,
    TURN_COMMAND_REJECT_PREPARED,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    LIMITATION_PRIOR_TURN_CONTINUATION,
    LIMITATION_RESULT_TRUNCATED,
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.capability_provision.contracts import (
    OWNER_RECORD_NOT_FOUND,
)
from app.application.interaction.capability_attempt import (
    EARLY_CONVERSATIONAL_ADMISSION,
    GovernedCapabilityStatus,
    SupportsGovernedCapabilityAttempt,
)
from app.application.interaction.errors import (
    CONTEXT_TOO_LARGE,
    FORBIDDEN,
    FORBIDDEN_MODEL_OUTPUT,
    INTERNAL_ERROR,
    INVALID_MODEL_OUTPUT,
    INVALID_REQUEST,
    MODEL_TIMEOUT,
    MODEL_UNAVAILABLE,
    UNAUTHENTICATED,
    InteractionError,
)
from app.application.interaction.instruction import (
    DELIA_INTERACTION_INSTRUCTION,
    interaction_instruction_lineage,
)
from app.application.interaction.presentation import (
    MESSAGE_KIND_AUTHZ_DENIED,
    MESSAGE_KIND_CLARIFICATION_REQUIRED,
    MESSAGE_KIND_CONFIRMATION_REQUIRED,
    MESSAGE_KIND_PRECONDITION_REQUIRED,
    MESSAGE_KIND_PROCESSING_TIMEOUT,
    MESSAGE_KIND_RESULT,
    MESSAGE_KIND_SOURCE_UNAVAILABLE,
    MESSAGE_KIND_WRITE_REJECTED,
    compose_presentation,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ModelInvocationRequest,
    ModelInvocationResult,
)
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    TIMEOUT,
    ModelInvocationError,
)
from app.application.interaction.turn_budget import (
    DEFAULT_TURN_BUDGET_SECONDS,
    TurnDeadline,
)
from app.application.interaction.turn_observability import (
    COMPOSITION_CRI,
    COMPOSITION_DETERMINISTIC,
    COMPOSITION_MODEL,
    ModelCallLedger,
    bind_turn_call_ledger,
    build_turn_observability,
    current_call_ledger,
    reset_turn_call_ledger,
)
from app.application.model_invocation.invoke_model import (
    MAX_INPUT_CHARS,
    InvokeModel,
)
from app.application.platform_access import PlatformAccessContext
from app.domain.evidence.model import EpistemicClass, ModelRef, UserRef
from app.domain.interaction.model import (
    GroundingStatus,
    InteractionSession,
    InteractionTurn,
    TurnKind,
)
from app.domain.interaction.rules import (
    prior_context_turn_admissible,
    record_interaction_turn,
)
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)


CORE_PERMISSION = "delia.access"

TASK_PURPOSE_ID = "delia.interaction.turn"
OUTPUT_SCHEMA_ID = "delia.interaction.turn"
OUTPUT_SCHEMA_VERSION = "1"
EXPECTED_FIELDS = ("answer",)
INTERACTION_TIMEOUT_SECONDS = 30.0

_logger = logging.getLogger(__name__)
# After governed NOT_APPLICABLE, the free-form conversational fallback
# must not consume the entire remaining turn budget into a gateway
# 504 (G0-02 C02 class: admission→conversational→model_timeout).
CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS = 12.0
LIMITATION_TURN_BUDGET = "turn_budget_limited"
CONVERSATIONAL_BUDGET_MESSAGE = (
    "Não consegui concluir a resposta conversacional dentro do tempo "
    "disponível neste turno. Reformule o pedido ou tente novamente — "
    "não inventei dados operacionais da DELPI."
)

# C4-MCP-GOVERNED-READS-01: canonical limitation code + disclosure for
# answers produced while the authoritative DELPI source could not be
# consulted. Never lets a model fabricate current DELPI state.
LIMITATION_DELPI_SOURCE_UNVERIFIED = "delpi_source_unverified"

# LOOP-03R1 (D07): a governed-path failure is terminal and
# deterministic — the general model NEVER answers operational
# questions after a selected authoritative source errored or denied
# access (general prose could masquerade as DELPI-verified data).
DELPI_SOURCE_UNAVAILABLE_MESSAGE = (
    "Não consegui consultar a fonte autoritativa da DELPI para esta "
    "solicitação. Nenhum dado operacional foi verificado — tente "
    "novamente em instantes ou reformule o pedido."
)
DELPI_SOURCE_DENIED_MESSAGE = (
    "O acesso à fonte autoritativa necessária para esta solicitação "
    "foi negado. Nenhum dado operacional foi verificado."
)
DELPI_OWNER_RECORD_NOT_FOUND_MESSAGE = (
    "A fonte consultada informou que não há registro para esta "
    "solicitação. Nenhum dado operacional foi inventado."
)
# Doc 88 CP2: a model-stage deadline or the turn budget interrupted
# processing — the authoritative source is NOT blamed when it was
# never consulted. Truthful interruption, no continuity promise: no
# work remains active after this terminal answer.
DELPI_PROCESSING_TIMEOUT_MESSAGE = (
    "O processamento da sua solicitação demorou além do limite e a "
    "tentativa foi interrompida. Não identifiquei uma falha na fonte "
    "de dados — nenhum dado operacional foi verificado. Você pode "
    "tentar novamente."
)

# C3-CENTRAL-INTERACTION-EXPERIENCE-BACKEND-01: producer-declared
# semantic kind per write-lifecycle status — the presentation
# projection never guesses the kind from prose.
_WRITE_LIFECYCLE_MESSAGE_KINDS = {
    GovernedCapabilityStatus.CLARIFICATION_REQUIRED: (
        MESSAGE_KIND_CLARIFICATION_REQUIRED
    ),
    GovernedCapabilityStatus.CONFIRMATION_REQUIRED: (
        MESSAGE_KIND_CONFIRMATION_REQUIRED
    ),
    GovernedCapabilityStatus.WRITE_REJECTED: MESSAGE_KIND_WRITE_REJECTED,
}

DEFAULT_MODEL_REF = ModelRef(
    model_id="delia-deterministic-interaction",
    version="1",
    owner_ref="DELPI",
    provider_ref=None,
)

_ALLOWED_RESULT_CLASSES = frozenset(
    {
        EpistemicClass.OBSERVATION,
        EpistemicClass.CALCULATION,
        EpistemicClass.HYPOTHESIS,
        EpistemicClass.CONCLUSION,
        EpistemicClass.RECOMMENDATION,
    }
)


def has_delia_access(context: PlatformAccessContext | None) -> bool:
    """Core effective permission `delia.access` or superadmin. Fail closed."""
    if context is None:
        return False
    return bool(
        context.is_superadmin
        or CORE_PERMISSION in context.effective_permissions
    )


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decision_turn_content(confirmation: Mapping[str, Any] | None) -> str:
    """Deterministic transcript marker for a typed decision turn.

    APPLY_PREPARED/REJECT_PREPARED carry no free text — the recorded
    user turn is a fixed descriptor, never fabricated prose
    (§6.184 D2).
    """
    decision = str((confirmation or {}).get("decision") or "").upper()
    if decision == "CONFIRM":
        return "Decisão estruturada: executar a proposta preparada."
    return "Decisão estruturada: cancelar a proposta preparada."


class HandleInteractiveConversationTurn:
    """One text turn through the canonical interaction + invocation chain."""

    def __init__(
        self,
        invoke_model: InvokeModel,
        *,
        model_ref: ModelRef = DEFAULT_MODEL_REF,
        instruction_lineage: InstructionLineage | None = None,
        instruction_content: str | None = None,
        timeout_seconds: float = INTERACTION_TIMEOUT_SECONDS,
        capability_orchestration: SupportsGovernedCapabilityAttempt | None = None,
        turn_budget_seconds: float = DEFAULT_TURN_BUDGET_SECONDS,
        response_intelligence_enabled: bool = False,
    ) -> None:
        self._invoke_model = invoke_model
        self._model_ref = model_ref
        self._instruction_lineage = (
            instruction_lineage or interaction_instruction_lineage()
        )
        self._instruction_content = instruction_content or (
            DELIA_INTERACTION_INSTRUCTION
        )
        self._timeout_seconds = timeout_seconds
        # ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03: optional
        # bounded capability orchestration (all owner classes under
        # generic governance). When absent the handler behaves exactly
        # like the C3 runtime.
        self._capability_orchestration = capability_orchestration
        # LOOP-03R2A: one monotonic deadline shared by the whole turn —
        # orchestration stages and the general model call each receive
        # at most the remaining budget, so a turn can never outlive
        # the edge request deadline.
        self._turn_budget_seconds = float(turn_budget_seconds)
        # CRI E1 (doc 73 §7 / spec 75 §4.1): composition-resolved
        # response mode at the governed-outcome → response boundary.
        # It marks observability only in this gate — selection,
        # authorization, evidence and presentation are unchanged.
        self._response_mode = (
            "cri" if response_intelligence_enabled else "baseline"
        )

    def execute(
        self,
        request: InteractiveTurnRequest,
        *,
        activity_channel: Callable[[ActivityEvent], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> InteractiveTurnResult:
        self._require_access(request.access_context)
        # Contract defense-in-depth: in-process callers must not bypass
        # the HTTP discriminator by supplying confirmation alone.
        self._validate_turn_command(request)
        input_text = self._validate_input(
            request.input_text, confirmation=request.confirmation
        )
        if request.confirmation is not None and self._capability_orchestration is None:
            raise InteractionError(
                INVALID_REQUEST,
                "a typed decision requires governed capability orchestration",
            )
        prior_turns = self._validate_prior_context(request.prior_turns)
        self._validate_execution_ceiling(request.max_execution_stage)
        turn_deadline = TurnDeadline.start(self._turn_budget_seconds)

        session = InteractionSession(
            session_id=str(uuid.uuid4()),
            actor_ref=UserRef(user_id=request.access_context.user_id),
            started_at=_now_utc(),
        )

        user_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.USER_INPUT,
            content=(
                input_text
                if input_text.strip()
                else _decision_turn_content(request.confirmation)
            ),
            occurred_at=_now_utc(),
        )
        session, user_validation = record_interaction_turn(session, user_turn)
        if not user_validation.valid:
            raise InteractionError(
                INVALID_REQUEST,
                ",".join(code.value for code in user_validation.error_codes),
            )

        # DELIA-C3-PROGRESSIVE-ACTIVITY (doc 70 §16): a request-scoped
        # observation sink bound to the real session/turn identity. The
        # channel is a transport seam — when absent (legacy JSON mode)
        # the use case is byte-for-byte identical.
        sink = activity_sink_or_none(
            activity_channel,
            session_id=session.session_id,
            turn_id=user_turn.turn_id,
        )
        if sink is not None:
            sink.emit(phase=ActivityPhase.REQUEST_RECEIVED)

        # Prompt 5: request-scoped model-call ledger — every real
        # InvokeModel.execute call inside this turn records provider
        # usage/duration verbatim; replayed governed-resume proposals
        # and deterministic revalidation never enter it.
        ledger_token = bind_turn_call_ledger(ModelCallLedger())
        try:
            return self._execute_observed(
                request,
                session,
                user_turn,
                input_text,
                prior_turns,
                turn_deadline,
                sink,
                cancel_check,
            )
        except InteractionError:
            if sink is not None:
                sink.emit(phase=ActivityPhase.FAILED)
            raise
        except Exception:
            if sink is not None:
                sink.emit(phase=ActivityPhase.FAILED)
            raise
        finally:
            reset_turn_call_ledger(ledger_token)

    def _execute_observed(
        self,
        request: InteractiveTurnRequest,
        session: InteractionSession,
        user_turn: InteractionTurn,
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...],
        turn_deadline: TurnDeadline,
        sink: ActivityEventSink | None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> InteractiveTurnResult:
        # CRI E1 (doc 73 §7): one response-mode marker per processed
        # turn at the governed-outcome → response boundary — identity
        # fields only, never payload. E2/E3 attach at this point.
        _logger.info(
            "interaction stage=response_mode decision=%s "
            "session_id=%s turn_id=%s",
            self._response_mode,
            session.session_id,
            user_turn.turn_id,
        )
        # ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03: the bounded
        # governed capability orchestration is tried first. Model
        # selection/answers never authorize anything — the fresh live
        # owner surface, deterministic validation and the write
        # governance chain decide.
        attempt = (
            self._capability_orchestration.attempt(
                input_text,
                actor_user_id=request.access_context.user_id,
                session_id=session.session_id,
                confirmation=request.confirmation,
                workspace_context=request.workspace_context,
                prior_turns=prior_turns,
                max_execution_stage=request.max_execution_stage,
                turn_deadline=turn_deadline,
                activity_sink=sink,
                cancel_check=cancel_check,
            )
            if self._capability_orchestration is not None
            else None
        )

        if attempt is not None and (
            attempt.status is GovernedCapabilityStatus.SUCCESS
        ):
            # Prior-turn continuity returns SUCCESS without a fresh
            # owner outcome — honest NON_GROUNDED, never fake grounding.
            if attempt.outcome is None:
                result = self._prior_continuation_result(
                    session, user_turn, attempt
                )
            else:
                result = self._grounded_result(session, user_turn, attempt)
            _emit_terminal(sink, ActivityPhase.COMPLETED)
            return self._with_observability(
                result,
                turn_deadline,
                composition_mode=(
                    COMPOSITION_CRI
                    if attempt.composition_mode == COMPOSITION_CRI
                    else COMPOSITION_DETERMINISTIC
                ),
                governed_attempts=attempt.governed_attempts,
            )

        if attempt is not None and attempt.status in (
            GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
            GovernedCapabilityStatus.AUTHZ_DENIED,
            GovernedCapabilityStatus.PROCESSING_TIMEOUT,
        ):
            # LOOP-03R1 (D07) + doc 88 CP2: a selected authoritative
            # source that errored or denied — or a processing deadline
            # that interrupted the turn — is a deterministic terminal
            # answer; the general model never narrates an operational
            # failure as if it were a DELPI-verified answer.
            result = self._source_terminal_result(
                session, user_turn, attempt
            )
            _emit_terminal(
                sink,
                ActivityPhase.BLOCKED,
                state=(
                    ActivityState.DENIED
                    if attempt.status is GovernedCapabilityStatus.AUTHZ_DENIED
                    else (
                        ActivityState.FAILED
                        if attempt.status
                        is GovernedCapabilityStatus.PROCESSING_TIMEOUT
                        else ActivityState.BLOCKED
                    )
                ),
            )
            return self._with_observability(
                result,
                turn_deadline,
                composition_mode=COMPOSITION_DETERMINISTIC,
                governed_attempts=attempt.governed_attempts,
            )

        if attempt is not None and attempt.status in (
            GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
            GovernedCapabilityStatus.WRITE_REJECTED,
            GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        ):
            # Write-class lifecycle answers and clarification ask-backs
            # are deterministic and truthful — never routed through the
            # model.
            result = self._write_lifecycle_result(
                session, user_turn, attempt
            )
            if attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED:
                _emit_terminal(sink, ActivityPhase.WAITING_CONFIRMATION)
            elif attempt.status is GovernedCapabilityStatus.WRITE_REJECTED:
                _emit_terminal(
                    sink, ActivityPhase.BLOCKED, state=ActivityState.DENIED
                )
            else:
                _emit_terminal(
                    sink, ActivityPhase.BLOCKED, state=ActivityState.WAITING
                )
            return self._with_observability(
                result,
                turn_deadline,
                composition_mode=COMPOSITION_DETERMINISTIC,
                governed_attempts=attempt.governed_attempts,
            )

        # R1 (doc 35): model-backed inconclusive selection returns
        # CLARIFICATION_REQUIRED above — never a second free-form model
        # call. Bare NOT_APPLICABLE (empty surface / no governed path)
        # may still use the ordinary conversational fallback when budget
        # remains. Cap the fallback stage and soft-land on timeout so a
        # hung general model cannot become HTTP 504 after admission
        # already spent part of the 30s turn (G0-02).

        if sink is not None:
            sink.emit(phase=ActivityPhase.OUTCOME_PREPARING)
        # Product Master 2026-10-20: the 12s cap applies only after
        # orchestration has already run. Typed early conversational
        # admission uses the remaining global deadline. A bare
        # NOT_APPLICABLE without that marker keeps the cap.
        early_admission = (
            attempt is not None
            and attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
            and attempt.admission_outcome == EARLY_CONVERSATIONAL_ADMISSION
        )
        fallback_cap = (
            None
            if early_admission
            else (
                CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS
                if (
                    attempt is not None
                    and attempt.status
                    is GovernedCapabilityStatus.NOT_APPLICABLE
                )
                else None
            )
        )
        try:
            model_result = self._invoke(
                input_text,
                prior_turns,
                deadline=turn_deadline,
                stage_cap_seconds=fallback_cap,
            )
        except InteractionError as exc:
            if (
                exc.code == MODEL_TIMEOUT
                and attempt is not None
                and attempt.status
                is GovernedCapabilityStatus.NOT_APPLICABLE
            ):
                result = self._conversational_budget_result(
                    session, user_turn
                )
                _emit_terminal(
                    sink,
                    ActivityPhase.COMPLETED,
                    state=ActivityState.BLOCKED,
                )
                return self._with_observability(
                    result,
                    turn_deadline,
                    composition_mode=COMPOSITION_DETERMINISTIC,
                    governed_attempts=(
                        attempt.governed_attempts
                        if attempt is not None
                        else None
                    ),
                )
            raise
        content, limitations = self._validate_result(model_result)

        result_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.DELIA_RESULT,
            content=content,
            occurred_at=_now_utc(),
            epistemic_class=model_result.epistemic_class,
            limitations=limitations,
        )
        session, result_validation = record_interaction_turn(session, result_turn)
        if not result_validation.valid:
            raise InteractionError(
                INTERNAL_ERROR,
                "validated DELIA_RESULT turn rejected by session rules",
            )

        result = InteractiveTurnResult(
            session_id=session.session_id,
            user_turn_id=user_turn.turn_id,
            result_turn_id=result_turn.turn_id,
            content=content,
            epistemic_class=model_result.epistemic_class,
            limitations=limitations,
            generated_at=model_result.generated_at,
            model_invocation_id=model_result.invocation_id.value,
            grounding_status=GroundingStatus.NON_GROUNDED,
        )
        _emit_terminal(sink, ActivityPhase.COMPLETED)
        return self._with_observability(
            result,
            turn_deadline,
            composition_mode=COMPOSITION_MODEL,
            governed_attempts=(
                attempt.governed_attempts
                if attempt is not None
                else None
            ),
        )

    def _with_observability(
        self,
        result: InteractiveTurnResult,
        turn_deadline: TurnDeadline,
        *,
        composition_mode: str,
        governed_attempts: int | None = None,
    ) -> InteractiveTurnResult:
        """Attach the bounded presentation-only observability
        projection (Prompt 5).

        Real model calls recorded in the request-scoped ledger carry
        provider usage/duration verbatim — replayed checkpoint
        proposals and deterministic revalidation never enter it.
        ``composition_mode`` is what actually produced this answer
        (CRI / deterministic / model), never the configured flag.
        """
        ledger = current_call_ledger()
        calls = ledger.calls if ledger is not None else ()
        duration_ms = None
        if turn_deadline.started_at is not None:
            duration_ms = int(
                (turn_deadline.clock() - turn_deadline.started_at) * 1000
            )
        return dataclasses.replace(
            result,
            observability=build_turn_observability(
                model_ref=self._model_ref,
                response_mode=self._response_mode,
                composition_mode=composition_mode,
                calls=calls,
                duration_ms=duration_ms,
                governed_attempts=governed_attempts or 1,
                operational_calls=(
                    ledger.operational_calls
                    if ledger is not None
                    else ()
                ),
                timeout_source=(
                    ledger.timeout_source if ledger is not None else None
                ),
                composition_ms=(
                    ledger.composition_ms if ledger is not None else 0
                ),
            ),
        )

    def _require_access(self, context: PlatformAccessContext | None) -> None:
        if context is None:
            raise InteractionError(UNAUTHENTICATED, "unauthenticated")
        if not has_delia_access(context):
            raise InteractionError(
                FORBIDDEN,
                f"missing required permission '{CORE_PERMISSION}'",
            )

    def _validate_turn_command(
        self, request: InteractiveTurnRequest
    ) -> None:
        """Application-layer execution-scope contract (RW-02).

        An authenticated direct consumer cannot bypass typed decision
        validation. Legacy confirmation labels are an explicit,
        temporary exact-match migration exception.
        """
        kind = request.command_type
        confirmation = request.confirmation
        text = request.input_text
        if kind == TURN_COMMAND_MESSAGE:
            if confirmation is not None:
                # Even direct in-process callers cannot turn MESSAGE
                # into ACT by adding confirmation. The HTTP boundary
                # normalizes a published legacy label to a typed
                # decision command before this validation runs.
                raise InteractionError(
                    INVALID_REQUEST,
                    "MESSAGE cannot carry a structured decision",
                )
            return
        if kind not in (
            TURN_COMMAND_APPLY_PREPARED,
            TURN_COMMAND_REJECT_PREPARED,
        ):
            raise InteractionError(INVALID_REQUEST, "invalid turn command")
        if not isinstance(confirmation, Mapping):
            raise InteractionError(
                INVALID_REQUEST, "typed decision requires confirmation"
            )
        expected = (
            "CONFIRM"
            if kind == TURN_COMMAND_APPLY_PREPARED
            else "REJECT"
        )
        # The HTTP mapper resolves legacy fixed labels into the same
        # typed command. Accept ONLY the published exact label during
        # migration; free text and contradictory payloads stay invalid.
        if not isinstance(text, str) or (
            text.strip() and text != LEGACY_CONFIRMATION_LABELS[expected]
        ):
            raise InteractionError(
                INVALID_REQUEST, "typed decision cannot carry free text"
            )
        if str(confirmation.get("decision") or "").upper() != expected:
            raise InteractionError(
                INVALID_REQUEST, "command and decision do not match"
            )
        if (
            kind == TURN_COMMAND_APPLY_PREPARED
            and request.max_execution_stage == "prepare"
        ):
            raise InteractionError(
                INVALID_REQUEST, "prepare ceiling forbids APPLY_PREPARED"
            )

    def _validate_input(
        self,
        input_text: str,
        confirmation: Mapping[str, Any] | None = None,
    ) -> str:
        if confirmation is not None:
            # Typed decision turn (APPLY_PREPARED/REJECT_PREPARED): the
            # bound decision IS the turn — free text is never a hidden
            # instruction here. Empty input is canonical; during the
            # migration window only the exact published MFE labels are
            # tolerated — anything else is a contract conflict, fail
            # closed (§6.184 D2).
            text = input_text if isinstance(input_text, str) else ""
            if not text.strip():
                return ""
            decision = str(confirmation.get("decision") or "").upper()
            if text == LEGACY_CONFIRMATION_LABELS.get(decision):
                return text
            raise InteractionError(
                INVALID_REQUEST,
                "a structured decision turn cannot carry free text",
            )
        if not isinstance(input_text, str) or not input_text.strip():
            raise InteractionError(INVALID_REQUEST, "input is required")
        if len(input_text) > MAX_INPUT_CHARS:
            raise InteractionError(
                INVALID_REQUEST,
                f"input exceeds bound ({MAX_INPUT_CHARS})",
            )
        return input_text

    def _validate_prior_context(
        self,
        prior_turns: tuple[ConversationContextTurn, ...],
    ) -> tuple[ConversationContextTurn, ...]:
        """Validate client-supplied transient context, fail closed.

        Prior turns are untrusted data: only USER_INPUT/DELIA_RESULT
        kinds, canonical epistemic admissibility (FACT never accepted),
        chronological USER_INPUT/DELIA_RESULT alternation, and an
        aggregate character budget reusing the model-input bound. No
        truncation — an oversized context is rejected wholesale.
        """
        if not isinstance(prior_turns, (tuple, list)):
            raise InteractionError(
                INVALID_REQUEST, "context must be a list of prior turns"
            )
        total_chars = 0
        expected_kind = TurnKind.USER_INPUT
        for index, turn in enumerate(prior_turns):
            if not isinstance(turn, ConversationContextTurn) or not isinstance(
                turn.kind, TurnKind
            ):
                raise InteractionError(
                    INVALID_REQUEST,
                    f"context[{index}] is not a valid prior turn",
                )
            if not isinstance(turn.content, str) or not turn.content.strip():
                raise InteractionError(
                    INVALID_REQUEST,
                    f"context[{index}] content must be a non-empty string",
                )
            if not prior_context_turn_admissible(
                turn.kind, turn.epistemic_class
            ):
                raise InteractionError(
                    INVALID_REQUEST,
                    f"context[{index}] epistemic_class is not admissible "
                    "for its kind",
                )
            if turn.kind is not expected_kind:
                raise InteractionError(
                    INVALID_REQUEST,
                    "context must alternate USER_INPUT/DELIA_RESULT "
                    "starting with USER_INPUT",
                )
            expected_kind = (
                TurnKind.DELIA_RESULT
                if expected_kind is TurnKind.USER_INPUT
                else TurnKind.USER_INPUT
            )
            total_chars += len(turn.content)
        if total_chars > MAX_INPUT_CHARS:
            raise InteractionError(
                CONTEXT_TOO_LARGE,
                f"context exceeds aggregate bound ({MAX_INPUT_CHARS})",
            )
        return tuple(prior_turns)

    def _prior_continuation_result(
        self,
        session: InteractionSession,
        user_turn: InteractionTurn,
        attempt,
    ) -> InteractiveTurnResult:
        """Record continuity from prior DELIA_RESULT content.

        No fresh owner outcome — NON_GROUNDED with an explicit
        limitation. Never elevates prior conversational text to FACT
        or reuses prior AuthZ as authority for a new capability call.
        """
        content = attempt.content
        if not isinstance(content, str) or not content.strip():
            raise InteractionError(
                INTERNAL_ERROR,
                "prior continuation produced no bounded content",
            )
        limitations = attempt.limitations or (
            LIMITATION_PRIOR_TURN_CONTINUATION,
        )
        if LIMITATION_PRIOR_TURN_CONTINUATION not in limitations:
            limitations = limitations + (
                LIMITATION_PRIOR_TURN_CONTINUATION,
            )
        occurred = _now_utc()
        result_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.DELIA_RESULT,
            content=content,
            occurred_at=occurred,
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=limitations,
        )
        session, result_validation = record_interaction_turn(
            session, result_turn
        )
        if not result_validation.valid:
            raise InteractionError(
                INTERNAL_ERROR,
                "prior continuation DELIA_RESULT rejected by session rules",
            )
        return InteractiveTurnResult(
            session_id=session.session_id,
            user_turn_id=user_turn.turn_id,
            result_turn_id=result_turn.turn_id,
            content=content,
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=limitations,
            generated_at=occurred,
            model_invocation_id=None,
            grounding_status=GroundingStatus.NON_GROUNDED,
        )

    def _grounded_result(
        self,
        session: InteractionSession,
        user_turn: InteractionTurn,
        attempt,
    ) -> InteractiveTurnResult:
        """Record a grounded DELIA_RESULT from the authoritative read.

        Deterministic rendering only — the bound read already produced
        the bounded content/limitations at the binding edge; no model
        wording is needed (OPERATIONAL path). The governed capability outcome
        stays OBSERVATION; grounding marks provenance, never FACT
        elevation.
        """
        outcome = attempt.outcome
        provenance = attempt.provenance
        content = attempt.content
        limitations = attempt.limitations
        if outcome is None:
            raise InteractionError(
                INTERNAL_ERROR,
                "grounded read requires a fresh owner outcome",
            )
        if not isinstance(content, str) or not content.strip():
            raise InteractionError(
                INTERNAL_ERROR,
                "grounded read produced no bounded content",
            )
        source_refs = (
            provenance.source_refs if provenance is not None else ()
        )
        result_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.DELIA_RESULT,
            content=content,
            occurred_at=_now_utc(),
            epistemic_class=EpistemicClass.OBSERVATION,
            source_refs=source_refs,
            limitations=limitations,
        )
        session, result_validation = record_interaction_turn(
            session, result_turn
        )
        if not result_validation.valid:
            raise InteractionError(
                INTERNAL_ERROR,
                "grounded DELIA_RESULT turn rejected by session rules",
            )
        return InteractiveTurnResult(
            session_id=session.session_id,
            user_turn_id=user_turn.turn_id,
            result_turn_id=result_turn.turn_id,
            content=content,
            epistemic_class=EpistemicClass.OBSERVATION,
            limitations=limitations,
            generated_at=outcome.provenance.observed_at,
            model_invocation_id=None,
            grounding_status=GroundingStatus.GROUNDED,
            provenance=provenance,
        )

    def _write_lifecycle_result(
        self,
        session: InteractionSession,
        user_turn: InteractionTurn,
        attempt,
    ) -> InteractiveTurnResult:
        """Record a deterministic write-lifecycle DELIA_RESULT.

        CONFIRMATION_REQUIRED carries the bounded confirmation surface
        (digests only — never the raw owner proposal handle) and marks
        provenance when the pending write came from an owner PREPARE.
        WRITE_REJECTED is a truthful refusal/cancellation — never a
        model narration and never a fabricated success.
        """
        content = attempt.content
        if not isinstance(content, str) or not content.strip():
            raise InteractionError(
                INTERNAL_ERROR,
                "write lifecycle attempt produced no bounded content",
            )
        provenance = attempt.provenance
        grounded = provenance is not None
        # Epistemic consistency (LOOP-03R1 §46): an ungrounded
        # clarification ask-back is a bounded HYPOTHESIS — the runtime
        # proposes a question, it does not conclude a fact. Grounded
        # write-lifecycle answers stay OBSERVATION; deterministic
        # refusals stay CONCLUSION.
        epistemic_class = (
            EpistemicClass.OBSERVATION
            if grounded
            else (
                EpistemicClass.HYPOTHESIS
                if attempt.status
                is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
                else EpistemicClass.CONCLUSION
            )
        )
        result_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.DELIA_RESULT,
            content=content,
            occurred_at=_now_utc(),
            epistemic_class=epistemic_class,
            source_refs=(
                provenance.source_refs if grounded else ()
            ),
            limitations=attempt.limitations,
        )
        session, result_validation = record_interaction_turn(
            session, result_turn
        )
        if not result_validation.valid:
            raise InteractionError(
                INTERNAL_ERROR,
                "write lifecycle DELIA_RESULT turn rejected by session rules",
            )
        return InteractiveTurnResult(
            session_id=session.session_id,
            user_turn_id=user_turn.turn_id,
            result_turn_id=result_turn.turn_id,
            content=content,
            epistemic_class=result_turn.epistemic_class,
            limitations=attempt.limitations,
            generated_at=_now_utc(),
            model_invocation_id=None,
            grounding_status=(
                GroundingStatus.GROUNDED
                if grounded
                else GroundingStatus.NON_GROUNDED
            ),
            provenance=provenance,
            confirmation_request=attempt.confirmation_context,
            message_kind=_WRITE_LIFECYCLE_MESSAGE_KINDS.get(attempt.status),
        )

    def _source_terminal_result(
        self,
        session: InteractionSession,
        user_turn: InteractionTurn,
        attempt,
    ) -> InteractiveTurnResult:
        """Deterministic terminal answer for a governed-path failure.

        SOURCE_UNAVAILABLE, AUTHZ_DENIED and PROCESSING_TIMEOUT are
        truthful terminal states: the selected authoritative source
        errored or denied access, or an internal processing deadline
        interrupted the turn — in all cases no operational data was
        verified. The result is HYPOTHESIS-class (ungrounded) and
        carries the canonical unverified-source limitation — never a
        general-model answer masquerading as DELPI data.
        """
        denied = attempt.status is GovernedCapabilityStatus.AUTHZ_DENIED
        processing_timeout = (
            attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
        )
        not_found = attempt.error_code == OWNER_RECORD_NOT_FOUND
        # Owner-declared precondition (bounded, verbatim owner
        # vocabulary — never a URL): tells the user WHAT the source
        # reported missing, without granting or inventing anything.
        owner_hint = getattr(attempt, "owner_hint", None)
        has_hint = isinstance(owner_hint, str) and bool(owner_hint)
        if processing_timeout:
            # Doc 88 CP2: internal deadline/budget exhaustion — the
            # source is never blamed when it was never consulted.
            content = DELPI_PROCESSING_TIMEOUT_MESSAGE
            message_kind = MESSAGE_KIND_PROCESSING_TIMEOUT
            limitations = (LIMITATION_DELPI_SOURCE_UNVERIFIED,)
        elif denied:
            content = DELPI_SOURCE_DENIED_MESSAGE
            message_kind = MESSAGE_KIND_AUTHZ_DENIED
            limitations = (LIMITATION_DELPI_SOURCE_UNVERIFIED,)
        elif not_found:
            # Owner envelope proved a non-recoverable 404. That is
            # absence of the requested record, not a dead source.
            content = DELPI_OWNER_RECORD_NOT_FOUND_MESSAGE
            if has_hint:
                content = content + f" A fonte informou: {owner_hint}"
            message_kind = MESSAGE_KIND_RESULT
            limitations = (LIMITATION_INSUFFICIENT_EVIDENCE,)
        else:
            content = DELPI_SOURCE_UNAVAILABLE_MESSAGE
            if has_hint:
                content = content + f" A fonte informou: {owner_hint}"
            # An owner-declared precondition is presented distinctly
            # from a bare source failure — PRECONDITION_REQUIRED
            # signals a user-actionable requirement (bounded, verbatim).
            message_kind = (
                MESSAGE_KIND_PRECONDITION_REQUIRED
                if has_hint
                else MESSAGE_KIND_SOURCE_UNAVAILABLE
            )
            limitations = (LIMITATION_DELPI_SOURCE_UNVERIFIED,)
        result_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.DELIA_RESULT,
            content=content,
            occurred_at=_now_utc(),
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=limitations,
        )
        session, result_validation = record_interaction_turn(
            session, result_turn
        )
        if not result_validation.valid:
            raise InteractionError(
                INTERNAL_ERROR,
                "terminal DELIA_RESULT turn rejected by session rules",
            )
        return InteractiveTurnResult(
            session_id=session.session_id,
            user_turn_id=user_turn.turn_id,
            result_turn_id=result_turn.turn_id,
            content=content,
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=limitations,
            generated_at=_now_utc(),
            model_invocation_id=None,
            grounding_status=GroundingStatus.NON_GROUNDED,
            message_kind=message_kind,
            owner_hint=owner_hint if has_hint else None,
        )

    @staticmethod
    def _validate_execution_ceiling(max_execution_stage: Any) -> None:
        """Application-layer defense for the reduction-only ceiling.

        The HTTP boundary already validates the wire shape; this
        second gate guarantees an internally constructed request
        (``max_execution_stage="act"``) can never silently behave as
        unrestricted execution — fail closed at the use-case boundary.
        """
        if max_execution_stage is None or max_execution_stage == "prepare":
            return
        raise InteractionError(
            INVALID_REQUEST,
            "max_execution_stage only accepts 'prepare' — it can "
            "reduce, never request, execution authority",
        )

    def _conversational_budget_result(
        self,
        session: InteractionSession,
        user_turn: InteractionTurn,
    ) -> InteractiveTurnResult:
        """Honest NON_GROUNDED answer when conversational fallback times out.

        Preserves the 30s turn ceiling without converting a hung general
        model call into an edge HTTP 504 after NOT_APPLICABLE admission.
        """
        occurred = _now_utc()
        result_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.DELIA_RESULT,
            content=CONVERSATIONAL_BUDGET_MESSAGE,
            occurred_at=occurred,
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=(LIMITATION_TURN_BUDGET,),
        )
        session, result_validation = record_interaction_turn(
            session, result_turn
        )
        if not result_validation.valid:
            raise InteractionError(
                INTERNAL_ERROR,
                "validated DELIA_RESULT turn rejected by session rules",
            )
        return InteractiveTurnResult(
            session_id=session.session_id,
            user_turn_id=user_turn.turn_id,
            result_turn_id=result_turn.turn_id,
            content=CONVERSATIONAL_BUDGET_MESSAGE,
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=(LIMITATION_TURN_BUDGET,),
            generated_at=occurred,
            model_invocation_id=None,
            grounding_status=GroundingStatus.NON_GROUNDED,
        )

    def _invoke(
        self,
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline | None = None,
        *,
        stage_cap_seconds: float | None = None,
    ) -> ModelInvocationResult:
        configured = self._timeout_seconds
        if stage_cap_seconds is not None:
            configured = min(configured, float(stage_cap_seconds))
        if deadline is not None:
            if deadline.exhausted():
                raise InteractionError(
                    MODEL_TIMEOUT,
                    "interaction turn budget exhausted",
                )
            timeout_seconds = deadline.stage_timeout(configured)
        else:
            timeout_seconds = configured
        invocation_request = ModelInvocationRequest(
            invocation_id=ModelInvocationId(str(uuid.uuid4())),
            model_ref=self._model_ref,
            input_text=input_text,
            prior_context=prior_turns,
            task_purpose_id=TASK_PURPOSE_ID,
            output_schema_id=OUTPUT_SCHEMA_ID,
            output_schema_version=OUTPUT_SCHEMA_VERSION,
            expected_fields=EXPECTED_FIELDS,
            instruction_lineage=self._instruction_lineage,
            instruction_content=self._instruction_content,
            timeout_seconds=timeout_seconds,
            declared_epistemic_class=EpistemicClass.HYPOTHESIS,
            # Request-local correlation metadata only; no authority fields
            # and no raw input duplication.
            untrusted_external_metadata={
                "interaction_surface": "delia-mfe",
                "input_kind": "text",
                "context_turn_count": len(prior_turns),
            },
        )
        # Stage 6 budget attribution: budget still available when this
        # conversational call was granted its timeout.
        granted_remaining_ms = (
            int(deadline.remaining_seconds() * 1000)
            if deadline is not None
            else None
        )
        started = time.monotonic()
        try:
            result = self._invoke_model.execute(invocation_request)
        except ModelInvocationError as exc:
            ledger = current_call_ledger()
            if ledger is not None:
                ledger.record_error(
                    stage=TASK_PURPOSE_ID,
                    finish_status=(
                        "timeout" if exc.code == TIMEOUT else "error"
                    ),
                    duration_ms=int(
                        (time.monotonic() - started) * 1000
                    ),
                    budget_remaining_ms=granted_remaining_ms,
                )
            raise _map_invocation_error(exc) from exc
        ledger = current_call_ledger()
        if ledger is not None:
            ledger.record_result(
                stage=TASK_PURPOSE_ID,
                result=result,
                budget_remaining_ms=granted_remaining_ms,
            )
        return result

    def _validate_result(
        self,
        result: ModelInvocationResult,
    ) -> tuple[str, tuple[str, ...]]:
        if result.epistemic_class not in _ALLOWED_RESULT_CLASSES:
            raise InteractionError(
                FORBIDDEN_MODEL_OUTPUT,
                "result epistemic class is not admissible for DELIA_RESULT",
            )
        content = result.structured_output.get("answer")
        if not isinstance(content, str) or not content.strip():
            raise InteractionError(
                INVALID_MODEL_OUTPUT,
                "structured output missing bounded 'answer' field",
            )
        limitations = result.structured_output.get("limitations", [])
        if not _is_string_list(limitations):
            raise InteractionError(
                INVALID_MODEL_OUTPUT,
                "structured output 'limitations' must be a list of strings",
            )
        return content, tuple(str(item) for item in limitations)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and all(
        isinstance(item, str) for item in value
    )


def _emit_terminal(
    sink: ActivityEventSink | None,
    phase: ActivityPhase,
    *,
    state: ActivityState | None = None,
) -> None:
    """Terminal-phase observation — emitted only after the authoritative
    result is assembled, so a failure mid-assembly can never masquerade
    as a completed turn."""
    if sink is None:
        return
    sink.emit(phase=phase, state=state)


def _map_invocation_error(exc: ModelInvocationError) -> InteractionError:
    code = exc.code
    if code == TIMEOUT:
        return InteractionError(MODEL_TIMEOUT, exc.message)
    if code == INVALID_STRUCTURED_OUTPUT:
        lowered = exc.message.lower()
        if any(
            marker in lowered
            for marker in ("tool", "secret", "chain_of_thought", "forbidden")
        ):
            return InteractionError(FORBIDDEN_MODEL_OUTPUT, exc.message)
        return InteractionError(INVALID_MODEL_OUTPUT, exc.message)
    if code == INVALID_REQUEST:
        return InteractionError(INVALID_REQUEST, exc.message)
    return InteractionError(MODEL_UNAVAILABLE, exc.message)


def serialize_result(result: InteractiveTurnResult) -> Mapping[str, Any]:
    """Bounded HTTP-safe projection of the application result."""
    return {
        "session_id": result.session_id,
        "user_turn_id": result.user_turn_id,
        "result_turn_id": result.result_turn_id,
        "content": result.content,
        "epistemic_class": (
            result.epistemic_class.value if result.epistemic_class else None
        ),
        "limitations": list(result.limitations),
        "generated_at": result.generated_at,
        "model_invocation_id": result.model_invocation_id,
        # C4-MCP-GOVERNED-READS-01: grounding marker is always explicit;
        # provenance is a bounded projection (no transport internals,
        # no tokens, no endpoint URLs).
        "grounding_status": result.grounding_status.value,
        "provenance": (
            result.provenance.to_projection()
            if result.provenance is not None
            else None
        ),
        # Bounded confirmation surface (digests only — never raw owner
        # proposal handles) emitted when a write awaits confirmation.
        "confirmation_request": (
            dict(result.confirmation_request)
            if result.confirmation_request is not None
            else None
        ),
        # C3-CENTRAL-INTERACTION-EXPERIENCE-BACKEND-01: additive,
        # versioned presentation projection — the single provider-
        # neutral contract a future MFE consumes. Legacy top-level
        # fields remain unchanged for backward compatibility.
        "presentation": compose_presentation(result),
        # Prompt 5: additive bounded observability projection —
        # presentation-only, already sanitized at build. ``None`` for
        # in-process results produced before the ledger was bound.
        "observability": (
            dict(result.observability)
            if result.observability is not None
            else None
        ),
    }
