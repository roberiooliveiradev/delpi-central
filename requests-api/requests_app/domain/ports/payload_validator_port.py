from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PayloadValidatorPort(ABC):
    """Validates create/update payload for a specific request type_code."""

    type_code: str = ""

    @abstractmethod
    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return normalized payload or raise ApplicationError."""
