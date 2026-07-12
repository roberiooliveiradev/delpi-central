# app/tests/test_notification_catalog_service.py

from pathlib import Path

import pytest

from app.application.services.notification_catalog_service import NotificationCatalogService
from app.infrastructure.content.notification_catalog_loader import load_notification_catalog


def test_catalog_contains_app_sources():
    catalog = NotificationCatalogService.get()

    assert "api_console" in catalog.categories
    assert catalog.categories["api_console"].source_apps == ("api-delpi-console",)
    assert catalog.categories["quality_action_plans"].plugin_id == "quality-action-plans"
    assert catalog.categories["auditoria_5s"].plugin_id == "auditoria-5s"
    assert catalog.categories["auditoria_5s"].source_apps == ("auditoria-5s",)


def test_resolve_legacy_category_alias():
    catalog = NotificationCatalogService.get()
    assert catalog.resolve_category("quality") == "quality_action_plans"


def test_source_app_plugin_aliases_from_catalog():
    catalog = NotificationCatalogService.get()
    aliases = catalog.source_app_plugin_aliases

    assert aliases["controle_mp"] == "controle-mp"
    assert aliases["api-delpi-console"] == "api-delpi-console"
    assert aliases["auditoria-5s"] == "auditoria-5s"


def test_loader_rejects_app_category_without_source_apps(tmp_path: Path):
    bad_catalog = tmp_path / "bad.json"
    bad_catalog.write_text(
        """
        {
          "version": 1,
          "categories": {
            "broken_app": {
              "label": "Broken",
              "icon": "bell",
              "mutable": true,
              "kind": "app"
            }
          }
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires sourceApps"):
        load_notification_catalog(bad_catalog)
