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

import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

from app.application.interaction.contracts import (
    LIMITATION_RESULT_TRUNCATED,
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.governed_read import (
    GovernedRead,
    GovernedReadStatus,
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

# C4-MCP-GOVERNED-READS-01: canonical limitation code + disclosure for
# answers produced while the authoritative DELPI source could not be
# consulted. Never lets a model fabricate current DELPI state.
LIMITATION_DELPI_SOURCE_UNVERIFIED = "delpi_source_unverified"
DELPI_UNVERIFIED_DISCLOSURE = (
    "Não consegui consultar a fonte DELPI neste momento. A resposta é "
    "conhecimento geral e não confirma o dado atual da DELPI."
)

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
        governed_read: GovernedRead | None = None,
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
        # C4-MCP-GOVERNED-READS-01: optional bounded governed read. When
        # absent the handler behaves exactly like the C3 runtime.
        self._governed_read = governed_read

    def execute(self, request: InteractiveTurnRequest) -> InteractiveTurnResult:
        self._require_access(request.access_context)
        input_text = self._validate_input(request.input_text)
        prior_turns = self._validate_prior_context(request.prior_turns)

        session = InteractionSession(
            session_id=str(uuid.uuid4()),
            actor_ref=UserRef(user_id=request.access_context.user_id),
            started_at=_now_utc(),
        )

        user_turn = InteractionTurn(
            turn_id=str(uuid.uuid4()),
            session_id=session.session_id,
            kind=TurnKind.USER_INPUT,
            content=input_text,
            occurred_at=_now_utc(),
        )
        session, user_validation = record_interaction_turn(session, user_turn)
        if not user_validation.valid:
            raise InteractionError(
                INVALID_REQUEST,
                ",".join(code.value for code in user_validation.error_codes),
            )

        # C4-MCP-GOVERNED-READS-01/02: the bounded governed reads are
        # tried first. Model selection/answers never authorize them —
        # static bindings, owner discovery, and deterministic
        # validation do.
        attempt = (
            self._governed_read.attempt(input_text)
            if self._governed_read is not None
            else None
        )

        if attempt is not None and attempt.status is GovernedReadStatus.SUCCESS:
            return self._grounded_result(session, user_turn, attempt)

        model_result = self._invoke(input_text, prior_turns)
        content, limitations = self._validate_result(model_result)
        if attempt is not None and attempt.status in (
            GovernedReadStatus.SOURCE_UNAVAILABLE,
            GovernedReadStatus.AUTHZ_DENIED,
        ):
            # Truthful fallback: the model may answer from general
            # knowledge but the response must disclose that current
            # DELPI data was not verified.
            content = f"{content}\n\n{DELPI_UNVERIFIED_DISCLOSURE}"
            limitations = limitations + (
                LIMITATION_DELPI_SOURCE_UNVERIFIED,
            )

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

        return InteractiveTurnResult(
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

    def _require_access(self, context: PlatformAccessContext | None) -> None:
        if context is None:
            raise InteractionError(UNAUTHENTICATED, "unauthenticated")
        if not has_delia_access(context):
            raise InteractionError(
                FORBIDDEN,
                f"missing required permission '{CORE_PERMISSION}'",
            )

    def _validate_input(self, input_text: str) -> str:
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

    def _grounded_result(
        self,
        session: InteractionSession,
        user_turn: InteractionTurn,
        attempt,
    ) -> InteractiveTurnResult:
        """Record a grounded DELIA_RESULT from the authoritative read.

        Deterministic rendering only — the bound read already produced
        the bounded content/limitations at the binding edge; no model
        wording is needed (OPERATIONAL path). The governed read outcome
        stays OBSERVATION; grounding marks provenance, never FACT
        elevation.
        """
        outcome = attempt.outcome
        provenance = attempt.provenance
        content = attempt.content
        limitations = attempt.limitations
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

    def _invoke(
        self,
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...],
    ) -> ModelInvocationResult:
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
            timeout_seconds=self._timeout_seconds,
            declared_epistemic_class=EpistemicClass.HYPOTHESIS,
            # Request-local correlation metadata only; no authority fields
            # and no raw input duplication.
            untrusted_external_metadata={
                "interaction_surface": "delia-mfe",
                "input_kind": "text",
                "context_turn_count": len(prior_turns),
            },
        )
        try:
            return self._invoke_model.execute(invocation_request)
        except ModelInvocationError as exc:
            raise _map_invocation_error(exc) from exc

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
    }
