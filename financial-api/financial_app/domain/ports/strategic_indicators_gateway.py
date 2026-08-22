from __future__ import annotations

from typing import Any, Protocol


class StrategicIndicatorsGatewayPort(Protocol):
    """Leitura do IDD/IGD no dono do bounded context (strategic-indicators-api)."""

    def fetch_department_indicators(
        self,
        *,
        department_id: str,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]: ...

    def fetch_departments_indicators(
        self,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]: ...

    def fetch_global_score(
        self,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]: ...
