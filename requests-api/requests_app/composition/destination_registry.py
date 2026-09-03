from __future__ import annotations

from collections.abc import Callable, Mapping

from requests_app.domain.ports.request_destination_port import RequestDestinationPort
from requests_app.infrastructure.gateways.api_delpi_adapter import ApiDelpiAdapter
from requests_app.infrastructure.gateways.commercial_adapter import CommercialAdapter


class UnknownDestinationAdapterError(KeyError):
    pass


_DEFAULT_FACTORIES: dict[str, Callable[[], RequestDestinationPort]] = {
    "api_delpi": ApiDelpiAdapter,
    "commercial": CommercialAdapter,
}


class DestinationAdapterRegistry:
    """Maps destination_config.adapter → RequestDestinationPort factory."""

    def __init__(
        self,
        factories: Mapping[str, Callable[[], RequestDestinationPort]] | None = None,
    ) -> None:
        self._factories = dict(factories or _DEFAULT_FACTORIES)

    def register(self, name: str, factory: Callable[[], RequestDestinationPort]) -> None:
        self._factories[str(name).strip()] = factory

    def resolve(self, adapter_name: str | None) -> RequestDestinationPort:
        key = str(adapter_name or "").strip()
        if not key:
            raise UnknownDestinationAdapterError("destination adapter is required")
        factory = self._factories.get(key)
        if factory is None:
            raise UnknownDestinationAdapterError(key)
        return factory()

    def resolve_from_config(self, destination_config: Mapping[str, object] | None) -> RequestDestinationPort:
        config = destination_config or {}
        return self.resolve(str(config.get("adapter") or ""))

    def known_adapters(self) -> list[str]:
        return sorted(self._factories.keys())
