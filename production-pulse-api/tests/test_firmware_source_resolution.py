from production_pulse_app.application.services.firmware_source_resolution_service import (
    FirmwareSourceResolutionService,
)


class FakeRepo:
    def __init__(self, rows: dict[tuple[str, str], dict]):
        self._rows = rows

    def get_by_key_version(self, *, firmware_key: str, version: str):
        return self._rows.get((firmware_key, version))


def test_installed_source_uses_exact_version_not_latest():
    repo = FakeRepo(
        {
            ("esp8266_counter_v1", "1.2.0"): {
                "id": "a",
                "source_text": "source-120",
            },
            ("esp8266_counter_v1", "1.4.0"): {
                "id": "b",
                "source_text": "source-140",
            },
        }
    )
    svc = FirmwareSourceResolutionService(repository=repo)
    installed = svc.resolve_version_source(
        firmware_key="esp8266_counter_v1",
        version="1.2.0",
    )
    assert installed["available"] is True
    assert installed["sourceText"] == "source-120"

    missing = svc.resolve_version_source(
        firmware_key="esp8266_counter_v1",
        version="9.9.9",
    )
    assert missing["available"] is False
    assert missing["reason"] == "version_not_in_catalog"


def test_device_resolution_separates_installed_target_and_legacy():
    repo = FakeRepo(
        {
            ("esp8266_counter_v1", "1.2.0"): {"id": "a", "source_text": "catalog-120"},
            ("esp8266_counter_v1", "1.3.0"): {"id": "b", "source_text": "catalog-130"},
        }
    )
    svc = FirmwareSourceResolutionService(repository=repo)
    device = {
        "firmware_key": "esp8266_counter_v1",
        "installed_firmware_version": "1.2.0",
        "firmware_source": "legacy-sketch",
    }
    data = svc.resolve_device_firmware_sources(device, target_version="1.3.0")
    assert data["installedSource"]["sourceText"] == "catalog-120"
    assert data["targetSource"]["sourceText"] == "catalog-130"
    assert data["legacySource"]["sourceText"] == "legacy-sketch"
