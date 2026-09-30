from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApplicationError(Exception):
    """Single application error type — wire code + safe details.

    HTTP status is a transport concern; the interface layer maps `code`.
    """

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.code}: {self.message}"


MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
REVISION_NOT_FOUND = "REVISION_NOT_FOUND"
MODEL_ARCHIVED = "MODEL_ARCHIVED"
INVALID_DISPLAY_NAME = "INVALID_DISPLAY_NAME"
CONFLICT = "CONFLICT"
NO_CHANGES = "NO_CHANGES"
VALIDATION_BLOCKED = "VALIDATION_BLOCKED"
INPUT_REJECTED_SECURITY = "INPUT_REJECTED_SECURITY"
UNAUTHORIZED_OPERATION = "UNAUTHORIZED_OPERATION"
OUTCOME_VERIFICATION_FAILED = "OUTCOME_VERIFICATION_FAILED"
INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
