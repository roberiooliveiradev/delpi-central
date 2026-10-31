"""Port for the R12/R15 closing-state marker reads."""

from __future__ import annotations

from typing import Protocol


class ClosingStateRepositoryPort(Protocol):
    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]: ...

    def last_snapshot_dates(
        self, *, branches: tuple[str, ...]
    ) -> dict[str, str]: ...

    def mv_ulmes_values(
        self, *, branches: tuple[str, ...]
    ) -> dict[str, str]: ...

    def ttat_write_window(
        self,
        *,
        log_table: str,
        field_name: str,
        window_start: str,
        window_end: str,
    ) -> dict: ...
