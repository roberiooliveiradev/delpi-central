"""Public port for the Strategic Indicators integrations contract.

The adapter talks to the shared HTTP client. No SI repository/ORM/SQL.
"""

from __future__ import annotations

from typing import Any, Protocol


class StrategicIndicatorsPort(Protocol):
    def get_department_score(
        self,
        *,
        department_id: str,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any] | None: ...

    def get_department_indicators(
        self,
        *,
        department_id: str,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any] | None: ...

    def list_dashboard_goals(
        self,
        *,
        source_keys: list[str],
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        department_id: str | None,
    ) -> dict[str, Any] | None: ...
