# app/domain/ports/shared_quality/audit_event_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)


class AuditEventRepositoryPort(ABC):
    @abstractmethod
    def create(self, event: NonconformityAuditEvent) -> NonconformityAuditEvent:
        raise NotImplementedError