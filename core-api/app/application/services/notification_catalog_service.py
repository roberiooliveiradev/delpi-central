# app/application/services/notification_catalog_service.py

from __future__ import annotations

from pathlib import Path

from app.domain.notifications.notification_catalog_types import NotificationCatalog
from app.infrastructure.content.notification_catalog_loader import load_notification_catalog


class NotificationCatalogService:
    _instance: NotificationCatalog | None = None
    _catalog_path: Path | None = None

    @classmethod
    def get(cls) -> NotificationCatalog:
        if cls._instance is None:
            cls._instance = load_notification_catalog(cls._catalog_path)
        return cls._instance

    @classmethod
    def configure(cls, *, catalog_path: Path | None = None) -> None:
        cls._catalog_path = catalog_path
        cls._instance = None

    @classmethod
    def reset_for_tests(cls) -> None:
        cls._instance = None
        cls._catalog_path = None
