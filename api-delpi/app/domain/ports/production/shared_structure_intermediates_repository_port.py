"""Port — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from typing import Any, Protocol


class SharedStructureIntermediatesRepositoryPort(Protocol):
    def get_shared_intermediates_summary(
        self,
        *,
        branch: str | None,
        movement_from: str,
        movement_to_exclusive: str,
    ) -> dict[str, Any]: ...

    def get_shared_intermediates(
        self,
        *,
        offset: int,
        page_size: int,
        branch: str | None,
        movement_from: str,
        movement_to_exclusive: str,
    ) -> list[dict[str, Any]]: ...
