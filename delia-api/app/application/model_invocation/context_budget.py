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

# Token estimate by structural character class, calibrated on the
# governed local model against 21 measured payloads (doc 151 §13):
# prose runs ~0.30 tok/char while digits and dense product codes reach
# ~1.01, symbols ~0.64, accented latin ~0.80, emoji up to ~1.45 and
# dense case-mixed strings ~0.75. A single chars/token factor cannot
# bound both ends, so the estimate sums per-class weights and applies a
# global safety margin. It remains a labeled heuristic bound: provider
# UsageMetadata is still the only actual count.
_NON_ASCII_WEIGHT = 1.55
_ASCII_DIGIT_WEIGHT = 1.20
_ASCII_UPPER_WEIGHT = 0.65
_ASCII_LOWER_WEIGHT = 0.36
_ASCII_SPACE_WEIGHT = 0.30
# Structural punctuation that BPE merges well (JSON/prose marks) vs.
# rare symbols measured ~1 tok/char on dense adversarial runs.
_ASCII_PUNCT_MERGEABLE = frozenset(".,:;!\"'{}[]()-_")
_ASCII_PUNCT_WEIGHT = 0.45
_ASCII_RARE_SYMBOL_WEIGHT = 1.00
# Whitespace-free runs longer than a normal word tokenize like dense
# identifiers — lowercase inside them is priced at the dense bound.
_DENSE_LOWER_WEIGHT = 0.65
_DENSE_RUN_LENGTH = 24
_ESTIMATE_SAFETY_MARGIN = 1.12

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


def estimate_text_tokens(text: str) -> int:
    """Structural token estimate for one payload segment.

    Weighted by character class so digit/code/unicode-dense content is
    not priced like prose. Never a measured count — see module docstring.
    """
    if not text:
        return 0
    weight = 0.0
    for run in text.split():
        dense = len(run) > _DENSE_RUN_LENGTH
        for ch in run:
            if ord(ch) > 127:
                weight += _NON_ASCII_WEIGHT
            elif "0" <= ch <= "9":
                weight += _ASCII_DIGIT_WEIGHT
            elif "A" <= ch <= "Z":
                weight += _ASCII_UPPER_WEIGHT
            elif "a" <= ch <= "z":
                weight += _DENSE_LOWER_WEIGHT if dense else _ASCII_LOWER_WEIGHT
            elif ch in _ASCII_PUNCT_MERGEABLE:
                weight += _ASCII_PUNCT_WEIGHT
            else:
                weight += _ASCII_RARE_SYMBOL_WEIGHT
        weight += _ASCII_SPACE_WEIGHT
    return math.ceil(weight * _ESTIMATE_SAFETY_MARGIN)


def _mandatory_chars(request: ModelInvocationRequest) -> int:
    return len(request.input_text) + len(request.instruction_content or "")


def _estimated_input_tokens(
    request: ModelInvocationRequest,
    prior_context: tuple,
) -> tuple[int, int]:
    chars = _mandatory_chars(request) + sum(
        len(turn.content) for turn in prior_context
    )
    segments = [request.input_text]
    if request.instruction_content:
        segments.append(request.instruction_content)
    segments.extend(turn.content for turn in prior_context)
    return (
        sum(estimate_text_tokens(segment) for segment in segments)
        + ADAPTER_OVERHEAD_TOKENS,
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
