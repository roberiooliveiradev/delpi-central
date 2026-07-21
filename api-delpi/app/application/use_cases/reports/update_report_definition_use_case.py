from __future__ import annotations

from typing import Any, Protocol


class ReportsUpdateDefinitionRepository(Protocol):
    def update_definition(
        self,
        *,
        definition_id: str,
        name: str | None = None,
        provider_key: str | None = None,
        params: dict[str, Any] | None = None,
        active: bool | None = None,
    ) -> dict[str, Any] | None: ...


class UpdateReportDefinitionUseCase:
    def __init__(self, repository: ReportsUpdateDefinitionRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        definition_id: str,
        name: str | None = None,
        provider_key: str | None = None,
        params: dict[str, Any] | None = None,
        active: bool | None = None,
    ) -> dict[str, Any] | None:
        return self._repository.update_definition(
            definition_id=definition_id,
            name=name.strip() if isinstance(name, str) else name,
            provider_key=(
                provider_key.strip() if isinstance(provider_key, str) else provider_key
            ),
            params=params,
            active=active,
        )
