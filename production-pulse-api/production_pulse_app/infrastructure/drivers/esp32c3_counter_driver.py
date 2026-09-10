from __future__ import annotations

import httpx

from production_pulse_app.infrastructure.drivers.http_counter_driver import HttpCounterDriver

_DRIVER_KEY = "esp32c3_counter_v1"


class Esp32c3CounterDriver(HttpCounterDriver):
    def __init__(
        self,
        *,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            driver_key=_DRIVER_KEY,
            timeout_seconds=timeout_seconds,
            client=client,
        )


__all__ = ["Esp32c3CounterDriver"]
