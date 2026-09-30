"""C3-T8 deterministic interaction-session rules (fail-closed).

Recording a turn never mutates Policy, RBAC, capability semantics, or
authorization. Closing a session only inactivates interaction context —
it does not revoke domain authority, delete Knowledge, or log out users.
"""

from __future__ import annotations

from dataclasses import replace

from app.domain.interaction.model import (
    InteractionSession,
    InteractionTurn,
    InteractionValidationCode,
    InteractionValidationResult,
    SessionStatus,
)


def validate_interaction_turn(
    session: InteractionSession,
    turn: InteractionTurn,
) -> InteractionValidationResult:
    """Validate a turn against its target session, fail-closed.

    A CLOSED session accepts no further interaction; a turn bound to a
    different session is a cross-session reference and never recorded.
    Empty content is invalid input — untrusted text is never coerced.
    """
    errors: list[InteractionValidationCode] = []
    if turn.session_id != session.session_id:
        errors.append(InteractionValidationCode.CROSS_SESSION_REFERENCE)
    if session.status is not SessionStatus.ACTIVE:
        errors.append(InteractionValidationCode.SESSION_CLOSED)
    if not turn.content.strip():
        errors.append(InteractionValidationCode.EMPTY_CONTENT)
    return InteractionValidationResult(
        valid=not errors,
        error_codes=tuple(errors),
        limitations=turn.limitations,
    )


def record_interaction_turn(
    session: InteractionSession,
    turn: InteractionTurn,
) -> tuple[InteractionSession, InteractionValidationResult]:
    """Return an updated session projection when the turn validates.

    Fail-closed: an invalid turn returns the session unchanged and the
    bounded error codes — no partial write, no authorization side effect.
    """
    result = validate_interaction_turn(session, turn)
    if not result.valid:
        return session, result
    return (
        replace(session, last_interaction_at=turn.occurred_at),
        result,
    )


def close_interaction_session(
    session: InteractionSession,
) -> InteractionSession:
    """Inactivate interaction context. != revoked AuthZ / deleted
    Knowledge / cancelled execution / user logout."""
    return replace(session, status=SessionStatus.CLOSED)
