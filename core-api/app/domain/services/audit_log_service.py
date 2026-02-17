# app/domain/services/audit_log_service.py

from flask import request, g
from app.extensions.db import db
from app.infrastructure.db.models.audit_log import AuditLog


def log_audit(
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict | None = None,
):
    user = getattr(g, "current_user", None)

    row = AuditLog(
        user_id=getattr(user, "id", None),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        payload=payload or None,
        ip_address=request.headers.get(
            "X-Forwarded-For",
            request.remote_addr,
        ),
    )

    db.session.add(row)
    db.session.commit()

    return row

