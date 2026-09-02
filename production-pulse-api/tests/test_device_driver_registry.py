import pytest

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverRegistryService,
)
from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.domain.services.device_validation_service import resolve_driver


def test_registry_loads_mvp_drivers():
    registry = DeviceDriverRegistryService()
    drivers = registry.list_catalog_drivers()
    keys = {item["key"] for item in drivers}
    assert "esp8266_counter_v1" in keys
    assert "esp8266_gauge_v1" in keys


def test_registry_counter_capabilities():
    registry = DeviceDriverRegistryService()
    caps = registry.build_capabilities("esp8266_counter_v1")
    assert caps["metrics"] == ["counter"]
    assert caps["commands"] == ["increment", "decrement", "reset"]
    assert caps["operatorSurface"] == "counter_pad"


def test_registry_gauge_capabilities():
    registry = DeviceDriverRegistryService()
    caps = registry.build_capabilities("esp8266_gauge_v1")
    assert caps["metrics"] == ["rpm", "temperature_c"]
    assert caps["commands"] == []
    assert caps["operatorSurface"] == "gauge_readout"
    assert caps["thresholds"]["temperature_c"]["warnAbove"] == 75


def test_resolve_driver_maps_role_key():
    resolved = resolve_driver("esp8266_gauge_v1")
    assert resolved.driver_key == "esp8266_gauge_v1"
    assert resolved.role_key == "process_gauge"


def test_resolve_driver_unknown_raises():
    with pytest.raises(DeviceValidationError, match="Driver desconhecido"):
        resolve_driver("modbus_plc_v99")


def test_poll_timeout_ms_default_and_override():
    registry = DeviceDriverRegistryService()
    assert registry.poll_timeout_ms("esp8266_counter_v1") == 3000
