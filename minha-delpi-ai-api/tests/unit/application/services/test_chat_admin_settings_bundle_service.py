from unittest.mock import MagicMock

from app.application.services.chat_admin_settings_bundle_service import (
    ChatAdminSettingsBundleService,
)
from app.infrastructure.config.chat_admin_settings_bundles import (
    CHAT_RESPONSE_MODE_BUNDLE,
)


def test_bundle_resolve_uses_defaults_when_db_empty():
    service = ChatAdminSettingsBundleService(CHAT_RESPONSE_MODE_BUNDLE, None)
    resolved = service.resolve()

    assert resolved["responseModesEnabled"] is True


def test_bundle_ensure_defaults_seeded_writes_once():
    repository = MagicMock()
    repository.get_json.return_value = None

    service = ChatAdminSettingsBundleService(CHAT_RESPONSE_MODE_BUNDLE, repository)
    service.ensure_defaults_seeded()

    repository.set_json.assert_called_once()
    key, payload = repository.set_json.call_args[0]
    assert key == "chat_response_mode_settings"
    assert "responseModesEnabled" in payload


def test_bundle_admin_prevails_over_defaults():
    repository = MagicMock()
    repository.get_json.return_value = {"responseModesEnabled": False}

    service = ChatAdminSettingsBundleService(CHAT_RESPONSE_MODE_BUNDLE, repository)
    result = service.to_dict()

    assert result["responseModesEnabled"] is False
    assert result["source"] == "admin"


def test_bundle_save_merges_partial_payload():
    repository = MagicMock()
    repository.get_json.return_value = {"responseModesEnabled": True}

    service = ChatAdminSettingsBundleService(CHAT_RESPONSE_MODE_BUNDLE, repository)
    service.save({"responseModesEnabled": False})

    repository.set_json.assert_called_once()
    _, payload = repository.set_json.call_args[0]
    assert payload["responseModesEnabled"] is False
