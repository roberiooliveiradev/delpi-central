from __future__ import annotations

from typing import Any, Protocol

from production_pulse_app.domain.models.device_reading import CommandResult, DeviceReading


class DeviceDriver(Protocol):
    @property
    def driver_key(self) -> str: ...

    def read(self, device: dict[str, Any]) -> DeviceReading: ...

    def test(self, device: dict[str, Any]) -> DeviceReading: ...

    def execute(
        self,
        device: dict[str, Any],
        command_key: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> CommandResult: ...

    def capabilities(self) -> frozenset[str]: ...
