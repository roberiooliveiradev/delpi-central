"""DAVI dynamic READ application errors (transport-agnostic)."""

from __future__ import annotations


class GovernedExecutionError(RuntimeError):
    """Rejected or failed governed execution (no HTTP semantics)."""

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code
