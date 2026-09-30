"""Conversation/session interaction domain (C3-T8).

Bounded interaction surface only — not a chat product, not Personal
Memory, not Organizational Knowledge, not authorization, not execution.
"""

from app.domain.interaction.model import (
    InteractionSession,
    InteractionTurn,
    InteractionValidationCode,
    InteractionValidationResult,
    SessionContext,
    SessionStatus,
    TurnKind,
)
from app.domain.interaction.rules import (
    close_interaction_session,
    record_interaction_turn,
    validate_interaction_turn,
)

__all__ = [
    "InteractionSession",
    "InteractionTurn",
    "InteractionValidationCode",
    "InteractionValidationResult",
    "SessionContext",
    "SessionStatus",
    "TurnKind",
    "close_interaction_session",
    "record_interaction_turn",
    "validate_interaction_turn",
]
