"""Composition root — integration write-operation tracking."""

from __future__ import annotations

from app.application.services.integration_tracking.tracking_service import (
    IntegrationTrackingService,
)
from app.infrastructure.persistence.plugins.repositories.integration_tracking.postgres_integration_operation_repository import (
    PostgresIntegrationOperationRepository,
)

_repository: PostgresIntegrationOperationRepository | None = None
_service: IntegrationTrackingService | None = None


def build_integration_operation_repository() -> PostgresIntegrationOperationRepository:
    global _repository
    if _repository is None:
        _repository = PostgresIntegrationOperationRepository()
    return _repository


def build_integration_tracking_service() -> IntegrationTrackingService:
    global _service
    if _service is None:
        _service = IntegrationTrackingService(
            repository=build_integration_operation_repository()
        )
    return _service
