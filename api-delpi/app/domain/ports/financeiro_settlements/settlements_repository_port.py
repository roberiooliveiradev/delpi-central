from __future__ import annotations

from typing import Protocol


class SettlementsRepositoryPort(Protocol):
    """Read-only access to Protheus settlement events (FK1 receivables,
    FK2 payables) with audited FK7/SE1/SE2/SED enrichment."""

    def list_settlements(
        self,
        *,
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def count_settlements(
        self,
        *,
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> int: ...

    def quality_counters(
        self,
        *,
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> dict: ...

    def summary_groups(
        self,
        *,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> list[dict]: ...

    def nature_descriptions(
        self, *, nature_codes: tuple[str, ...]
    ) -> dict[str, str]: ...

    def movement_descriptions(
        self, *, movement_types: tuple[str, ...]
    ) -> dict[str, str]: ...
