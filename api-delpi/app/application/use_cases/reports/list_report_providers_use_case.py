from __future__ import annotations

from typing import Any, Protocol


class ReportProviderRegistryPort(Protocol):
    def list_providers(self) -> list[Any]: ...


class ListReportProvidersUseCase:
    def __init__(self, registry: ReportProviderRegistryPort) -> None:
        self._registry = registry

    def execute(self) -> dict[str, Any]:
        items = [
            {
                "key": provider.key,
                "paramsSchema": dict(provider.describe_params()),
            }
            for provider in self._registry.list_providers()
        ]
        return {"items": items, "total": len(items)}
