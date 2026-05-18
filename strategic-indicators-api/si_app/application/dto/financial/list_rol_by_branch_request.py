from dataclasses import dataclass


@dataclass(frozen=True)
class ListRolByBranchRequest:
    branches: list[str]
    start_date: str | None = None
    end_date: str | None = None
