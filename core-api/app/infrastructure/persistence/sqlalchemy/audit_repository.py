# app/infrastructure/persistence/sqlalchemy/audit_repository.py

from __future__ import annotations

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.infrastructure.db.models import AuditLog


class SqlAlchemyAuditRepository(AuditRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def log(self, data: Dict[str, Any]) -> None:
        self.session.add(
            AuditLog(
                user_id=data.get("user_id"),
                action=data.get("action"),
                entity_type=data.get("entity_type"),
                entity_id=data.get("entity_id"),
                payload=data.get("payload"),
                ip_address=data.get("ip_address"),
            )
        )