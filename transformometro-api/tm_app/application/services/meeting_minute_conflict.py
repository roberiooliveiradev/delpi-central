"""Optimistic concurrency conflicts for meeting minutes."""

from __future__ import annotations


class MeetingMinuteConflictError(Exception):
    """Raised when a write precondition (expected_updated_at) does not match."""

    def __init__(
        self,
        message: str = (
            "A ata foi alterada por outro usuário ou sessão. "
            "Recarregue e tente novamente."
        ),
        *,
        current_updated_at: str | None = None,
    ) -> None:
        super().__init__(message)
        self.current_updated_at = current_updated_at
