# app/tests/test_notification_preference_repository_imports.py


def test_notification_preference_repository_imports_catalog():
    from app.infrastructure.persistence.sqlalchemy.notification_preference_repository import (
        SqlAlchemyNotificationPreferenceRepository,
    )

    assert SqlAlchemyNotificationPreferenceRepository is not None


def test_create_app_bootstraps_notification_catalog():
    from app.create_app import create_app
    from app.application.services.notification_catalog_service import NotificationCatalogService

    app = create_app("testing")
    catalog = NotificationCatalogService.get()

    assert app is not None
    assert "system" in catalog.categories
    assert "api_console" in catalog.mutable_categories
