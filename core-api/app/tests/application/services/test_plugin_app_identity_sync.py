# app/tests/application/services/test_plugin_app_identity_sync.py

from app.application.services.plugin_app_identity_sync import (
    app_identity_from_manifest,
    build_app_create_payload,
    sync_app_row_from_manifest,
)


def test_app_identity_cosmetic_omits_structure_fields():
    identity = app_identity_from_manifest(
        {
            "name": "Portal",
            "description": "d",
            "icon": "briefcase-business",
            "type": "microfrontend",
            "basePath": "/apps/commercial",
        },
        mode="cosmetic",
    )
    assert identity == {
        "name": "Portal",
        "description": "d",
        "icon": "briefcase-business",
    }


def test_app_identity_full_includes_type_and_base_path():
    identity = app_identity_from_manifest(
        {
            "name": "Portal",
            "icon": "briefcase-business",
            "type": "microfrontend",
            "basePath": "/apps/commercial",
        },
        mode="full",
    )
    assert identity["app_type"] == "microfrontend"
    assert identity["base_path"] == "/apps/commercial"


def test_build_app_create_payload_uses_shared_identity():
    payload = build_app_create_payload(
        {
            "name": "CRM",
            "description": "x",
            "icon": "layout-dashboard",
            "type": "microfrontend",
            "basePath": "/apps/crm",
        },
        plugin_id="crm",
        version="1.0.0",
    )
    assert payload == {
        "id": "crm",
        "name": "CRM",
        "description": "x",
        "base_path": "/apps/crm",
        "icon": "layout-dashboard",
        "type": "microfrontend",
        "version": "1.0.0",
        "active": True,
    }


def test_sync_cosmetic_does_not_pass_structure_kwargs():
    calls = {}

    class Plugins:
        def update_version(self, *a, **k):
            raise AssertionError("cosmetic sync must not bump version")

        def update_metadata(self, plugin_id, **kwargs):
            calls["kwargs"] = kwargs

    sync_app_row_from_manifest(
        Plugins(),
        "crm",
        {"name": "CRM", "icon": "star", "type": "microfrontend", "basePath": "/apps/crm"},
        mode="cosmetic",
    )
    assert calls["kwargs"]["icon"] == "star"
    assert calls["kwargs"]["app_type"] is None
    assert calls["kwargs"]["base_path"] is None
