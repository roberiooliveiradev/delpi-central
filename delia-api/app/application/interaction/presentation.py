"""Interaction Presentation Contract — C3-CENTRAL-INTERACTION-EXPERIENCE-BACKEND-01.

Deterministic, additive, provider-neutral projection composed at the
serialization edge from the already-governed ``InteractiveTurnResult``.
It never fabricates facts, never re-derives authorization, and never
carries provider payloads, URLs, or model-authored prose — every block
is built exclusively from fields that already passed the existing
governance and grounding boundaries.

The contract is versioned so future component kinds (list, table,
metric, chart, artifact) can be added without breaking consumers. Only
block kinds whose need is proven in the current runtime are emitted:
``text`` (the bounded result content) and ``notice`` (bounded verbatim
owner vocabulary such as a declared precondition). The allowlist is
closed — model or provider output can never introduce new block kinds
or executable payloads (no HTML/JS/layout instructions).
"""

from __future__ import annotations

from typing import Any

PRESENTATION_CONTRACT_VERSION = "1"

# Canonical message kinds — reuse the GovernedCapabilityStatus
# vocabulary rather than inventing parallel semantics.
MESSAGE_KIND_RESULT = "RESULT"
MESSAGE_KIND_CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
MESSAGE_KIND_CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
MESSAGE_KIND_WRITE_REJECTED = "WRITE_REJECTED"
MESSAGE_KIND_AUTHZ_DENIED = "AUTHZ_DENIED"
MESSAGE_KIND_SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
MESSAGE_KIND_PRECONDITION_REQUIRED = "PRECONDITION_REQUIRED"

_KNOWN_MESSAGE_KINDS = frozenset(
    {
        MESSAGE_KIND_RESULT,
        MESSAGE_KIND_CLARIFICATION_REQUIRED,
        MESSAGE_KIND_CONFIRMATION_REQUIRED,
        MESSAGE_KIND_WRITE_REJECTED,
        MESSAGE_KIND_AUTHZ_DENIED,
        MESSAGE_KIND_SOURCE_UNAVAILABLE,
        MESSAGE_KIND_PRECONDITION_REQUIRED,
    }
)

BLOCK_KIND_TEXT = "text"
BLOCK_KIND_NOTICE = "notice"
NOTICE_ROLE_OWNER_HINT = "owner_hint"

# Closed allowlist of emittable block kinds. Future kinds (list/table/
# metric/chart/artifact) must extend this set explicitly with a typed
# schema — they are never accepted from provider or model payloads.
_ALLOWED_BLOCK_KINDS = frozenset({BLOCK_KIND_TEXT, BLOCK_KIND_NOTICE})
_MAX_BLOCKS = 8
_MAX_BLOCK_TEXT_CHARS = 16_384

# Interactions a client may legitimately offer next. They describe the
# existing confirmation vocabulary only (CONFIRM/REJECT — see
# domain.governed_write.model.ConfirmationDecision); they authorize
# nothing and can never widen execution authority.
_INTERACTION_REPLY = "reply"
_INTERACTION_CONFIRM = "confirm"
_INTERACTION_REJECT = "reject"

_ALLOWED_INTERACTIONS_BY_KIND = {
    MESSAGE_KIND_CONFIRMATION_REQUIRED: (
        _INTERACTION_REPLY,
        _INTERACTION_CONFIRM,
        _INTERACTION_REJECT,
    ),
}
_DEFAULT_ALLOWED_INTERACTIONS = (_INTERACTION_REPLY,)


def compose_presentation(result) -> dict[str, Any]:
    """Compose the bounded presentation projection for one result.

    ``result`` is an InteractiveTurnResult; the function reads only its
    already-governed fields. ``message_kind`` is taken verbatim when the
    producer declared a canonical kind; otherwise it is derived from
    the result's structural signals (confirmation surface, owner hint)
    and defaults to RESULT — never guessed from prose.
    """
    message_kind = result.message_kind
    if message_kind not in _KNOWN_MESSAGE_KINDS:
        if result.confirmation_request is not None:
            message_kind = MESSAGE_KIND_CONFIRMATION_REQUIRED
        elif isinstance(result.owner_hint, str) and result.owner_hint:
            message_kind = MESSAGE_KIND_PRECONDITION_REQUIRED
        else:
            message_kind = MESSAGE_KIND_RESULT

    blocks = [
        {
            "kind": BLOCK_KIND_TEXT,
            "text": (result.content or "")[:_MAX_BLOCK_TEXT_CHARS],
        }
    ]
    if isinstance(result.owner_hint, str) and result.owner_hint:
        blocks.append(
            {
                "kind": BLOCK_KIND_NOTICE,
                "role": NOTICE_ROLE_OWNER_HINT,
                "text": result.owner_hint[:_MAX_BLOCK_TEXT_CHARS],
            }
        )
    blocks = blocks[:_MAX_BLOCKS]
    for block in blocks:
        if block["kind"] not in _ALLOWED_BLOCK_KINDS:  # pragma: no cover
            raise ValueError("non-allowlisted presentation block kind")

    return {
        "version": PRESENTATION_CONTRACT_VERSION,
        "message_kind": message_kind,
        "semantic_status": (
            result.epistemic_class.value if result.epistemic_class else None
        ),
        "grounding_status": result.grounding_status.value,
        "blocks": blocks,
        "allowed_interactions": list(
            _ALLOWED_INTERACTIONS_BY_KIND.get(
                message_kind, _DEFAULT_ALLOWED_INTERACTIONS
            )
        ),
    }
