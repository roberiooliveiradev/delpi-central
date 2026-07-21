from __future__ import annotations

from typing import Any, Protocol


class ReportsCreateDefinitionRepository(Protocol):
    def create_definition(
        self,
        *,
        name: str,
        provider_key: str,
        params: dict[str, Any],
        active: bool,
        created_by_user_id: str | None,
    ) -> dict[str, Any]: ...


class CreateReportDefinitionUseCase:
    def __init__(self, repository: ReportsCreateDefinitionRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        name: str,
        provider_key: str,
        params: dict[str, Any] | None,
        active: bool,
        created_by_user_id: str | None,
    ) -> dict[str, Any]:
        return self._repository.create_definition(
            name=name.strip(),
            provider_key=provider_key.strip(),
            params=dict(params or {}),
            active=active,
            created_by_user_id=created_by_user_id,
        )
