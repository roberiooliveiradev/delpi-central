"""Port for Core solution-catalog reads — Bearer-forwarded, user-parity.

The catalog is KNOWLEDGE, not authorization: `accessible` reports the
user's effective access as computed by Core; it never grants it.
"""

from __future__ import annotations

from typing import Any, Protocol


class SolutionCatalogPort(Protocol):
    def list_solutions(self, authorization: str) -> list[dict[str, Any]]:
        """All discoverable solutions with `accessible` flag."""
        ...

    def get_solution(self, plugin_id: str, authorization: str) -> dict[str, Any] | None:
        """Single solution detail; None when unknown/inactive."""
        ...
