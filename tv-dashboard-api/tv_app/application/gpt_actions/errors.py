"""Façade errors for Custom GPT Actions (stable codes, not a second AuthZ)."""

from __future__ import annotations

from typing import Any


class GptActionsError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int = 400,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = int(status_code)
        self.retryable = bool(retryable)
        self.details = details or {}
