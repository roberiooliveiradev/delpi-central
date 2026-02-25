# app/domain/ports/audit_repository.py

from typing import Protocol
from app.infrastructure.db.models.audit_log import AuditLog


class AuditRepository(Protocol):

    def log(self, audit: AuditLog) -> None:
        ...