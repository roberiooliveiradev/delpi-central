from __future__ import annotations

import logging

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.infrastructure.drivers.esp8266_counter_driver import Esp8266CounterDriver
from production_pulse_app.infrastructure.drivers.esp8266_gauge_driver import Esp8266GaugeDriver

logger = logging.getLogger(__name__)
_registered = False


def register_device_drivers() -> None:
    global _registered
    if _registered:
        return

    registry = get_device_driver_registry()
    registry.register_implementation(Esp8266CounterDriver())
    registry.register_implementation(Esp8266GaugeDriver())
    _registered = True
    logger.info("Device drivers registered: esp8266_counter_v1, esp8266_gauge_v1")


def reset_device_driver_registration_for_tests() -> None:
    global _registered
    get_device_driver_registry().clear_implementations_for_tests()
    _registered = False
