"""Re-export compat — intake seguro vive em ``shared/bpmn_validation`` (G7)."""

from bpmn_validation.intake import (
    MAX_CANONICAL_UTF8_BYTES,
    MAX_INPUT_BYTES,
    IntakeResult,
    intake_bytes,
)

__all__ = [
    "MAX_CANONICAL_UTF8_BYTES",
    "MAX_INPUT_BYTES",
    "IntakeResult",
    "intake_bytes",
]
