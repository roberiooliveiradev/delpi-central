from __future__ import annotations

from production_pulse_app.infrastructure.drivers.http_gauge_driver import HttpGaugeDriver

_DRIVER_KEY = "esp8266_gauge_v1"


class Esp8266GaugeDriver(HttpGaugeDriver):
    def __init__(self, **kwargs) -> None:
        super().__init__(driver_key=_DRIVER_KEY, **kwargs)


__all__ = ["Esp8266GaugeDriver"]
