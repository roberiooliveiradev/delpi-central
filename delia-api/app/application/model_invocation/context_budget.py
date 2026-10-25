"""Pre-call context budget policy (Context Intelligence WP-A).

Provider-neutral policy over the ModelInvocationRequest contract. The
adapter declares the effective input window; this module estimates the
assembled prompt, reduces only untrusted prior history when needed —
oldest first, in complete USER_INPUT/DELIA_RESULT pairs so the
chronological alternation invariant survives — and marks the request
rejected when mandatory content alone cannot fit.

Estimates are heuristic (chars/token), never measured usage: provider
UsageMetadata remains the only actual count. Nothing here knows or may
know provider-specific fields (num_ctx and friends stay in the adapter).
"""

from __future__ import annotations

import dataclasses
import math

from app.application.model_invocation.contracts import (
    ContextBudgetObservation,
    ModelInvocationRequest,
)
from app.domain.interaction.model import TurnKind

# Conservative estimate bound: measured ~3.0 chars/token for PT-BR and
# JSON payloads on the governed local model; 2.5 leaves ~17% headroom so
# an underestimate (silent provider truncation) cannot be caused by the
# estimator itself.
CHARS_PER_TOKEN_ESTIMATE = 2.5

# Adapter-side prompt additions the request contract cannot see: the
# structured-output directive plus per-message role/framing overhead.
# Measured directive ~200 tokens; framing ~4/message for the maximum
# admissible message count.
ADAPTER_OVERHEAD_TOKENS = 260

# Floor when generation_config.max_output_units is unset — reserves
# generation space inside the window so the prompt never crowds it out.
DEFAULT_GENERATION_RESERVE_TOKENS = 512

WITHIN_BUDGET = "within_budget"
REDUCED = "reduced"
REJECTED = "rejected"
REDUCTION_REASON_PRIOR_TURNS = "prior_turns_omitted_for_window"


def _estimate_tokens(chars: int) -> int:
    if chars <= 0:
        return 0
    return math.ceil(chars / CHARS_PER_TOKEN_ESTIMATE)


def _mandatory_chars(request: ModelInvocationRequest) -> int:
    return len(request.input_text) + len(request.instruction_content or "")


def _estimated_input_tokens(
    request: ModelInvocationRequest,
    prior_context: tuple,
) -> tuple[int, int]:
    chars = _mandatory_chars(request) + sum(
        len(turn.content) for turn in prior_context
    )
    return (
        _estimate_tokens(chars) + ADAPTER_OVERHEAD_TOKENS,
        chars,
    )


def _drop_oldest_pair(
    prior_context: tuple,
) -> tuple:
    """Drop the oldest turns while preserving alternation.

    Complete USER_INPUT/DELIA_RESULT pairs are dropped together. If the
    first turn is not USER_INPUT (defensive — the HTTP boundary enforces
    alternation), single turns are dropped until a pair boundary.
    """
    if not prior_context:
        return prior_context
    if prior_context[0].kind is not TurnKind.USER_INPUT:
        return prior_context[1:]
    return prior_context[min(2, len(prior_context)):]


def apply_context_budget(
    request: ModelInvocationRequest,
    *,
    context_window_tokens: int,
    generation_reserve_tokens: int | None,
) -> tuple[ModelInvocationRequest, ContextBudgetObservation]:
    """Fit the request into the declared effective input window.

    Returns the (possibly reduced) request and the decision record. The
    only reducible element is untrusted prior history; instruction,
    schema lineage, and the current input are mandatory and never
    trimmed. When mandatory content alone exceeds the window the status
    is ``rejected`` — the caller must fail closed before dispatch.
    """
    reserve = (
        generation_reserve_tokens
        if isinstance(generation_reserve_tokens, int)
        and generation_reserve_tokens > 0
        else DEFAULT_GENERATION_RESERVE_TOKENS
    )
    budget = context_window_tokens - reserve
    prior = tuple(request.prior_context)
    omitted = 0
    while prior:
        estimated, _ = _estimated_input_tokens(request, prior)
        if estimated <= budget:
            break
        reduced_prior = _drop_oldest_pair(prior)
        if reduced_prior == prior:
            break
        omitted += len(prior) - len(reduced_prior)
        prior = reduced_prior
    estimated, chars = _estimated_input_tokens(request, prior)
    if estimated > budget:
        status = REJECTED
    elif omitted:
        status = REDUCED
    else:
        status = WITHIN_BUDGET
    observation = ContextBudgetObservation(
        context_window_tokens=context_window_tokens,
        input_chars=chars,
        estimated_input_tokens=estimated,
        generation_reserve_tokens=reserve,
        prior_turns_included=len(prior),
        prior_turns_omitted=omitted,
        reduction_reason=(
            REDUCTION_REASON_PRIOR_TURNS if omitted else None
        ),
        budget_status=status,
    )
    if prior == request.prior_context:
        return request, observation
    return (
        dataclasses.replace(request, prior_context=prior),
        observation,
    )
