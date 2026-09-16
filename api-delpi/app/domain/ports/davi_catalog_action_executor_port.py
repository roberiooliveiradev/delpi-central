"""Port for catalog-fixed DAVI action execution (no HTTP/transport concepts)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class CatalogActionExecutionResult:
    """Semantic outcome of a catalog action (AuthZ/operation result, not HTTP)."""

    outcome: Literal["ok", "unauthorized", "forbidden", "error"]
    payload: Any = None
    error_message: str | None = None


class CatalogActionExecutorPort(Protocol):
    """Execute one already-validated catalog action for the current bound actor.

    Infrastructure owns transport, Authorization propagation, and technical
    resolution of action_id → fixed catalog contract. Application never passes
    method/path/headers/tokens.
    """

    def execute(
        self,
        *,
        action_id: str,
        validated_arguments: dict[str, Any],
    ) -> CatalogActionExecutionResult: ...
