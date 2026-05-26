from uuid import UUID


class ExportUserDataUseCase:
    """Exporta todos os dados pessoais do titular (LGPD Art. 18, V)."""

    def __init__(self, uow):
        self._uow = uow

    def execute(self, user_id: str) -> dict:
        uid = UUID(user_id)
        session = self._uow.session

        user = self._uow.users.get_by_id(uid)
        if not user:
            raise LookupError("Usuário não encontrado.")

        profile = {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "active": user.active,
            "birthDate": user.birth_date.isoformat() if user.birth_date else None,
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
        }

        from app.infrastructure.db.models.notification import Notification
        notifs_q = (
            session.query(Notification)
            .filter_by(user_id=uid)
            .filter(Notification.deleted_at.is_(None))
            .order_by(Notification.created_at.desc())
            .limit(500)
            .all()
        )
        notifications = [
            {
                "id": str(n.id),
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "category": n.category,
                "createdAt": n.created_at.isoformat() if n.created_at else None,
                "readAt": n.read_at.isoformat() if n.read_at else None,
            }
            for n in notifs_q
        ]

        from app.infrastructure.db.models.app_usage_event import AppUsageEvent
        usage_q = (
            session.query(AppUsageEvent)
            .filter_by(user_id=uid)
            .order_by(AppUsageEvent.opened_at.desc())
            .limit(1000)
            .all()
        )
        usage_events = [
            {
                "appId": e.app_id,
                "routePath": e.route_path,
                "openedAt": e.opened_at.isoformat() if e.opened_at else None,
            }
            for e in usage_q
        ]

        from app.infrastructure.db.models.audit_log import AuditLog
        audits_q = (
            session.query(AuditLog)
            .filter_by(user_id=uid)
            .order_by(AuditLog.created_at.desc())
            .limit(500)
            .all()
        )
        audit_logs = [
            {
                "action": a.action,
                "entityType": a.entity_type,
                "entityId": a.entity_id,
                "createdAt": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audits_q
        ]

        consents = self._uow.consents.list_by_user(uid)
        consents_data = [
            {
                "purpose": c.purpose,
                "granted": c.granted,
                "grantedAt": c.granted_at.isoformat() if c.granted_at else None,
                "revokedAt": c.revoked_at.isoformat() if c.revoked_at else None,
            }
            for c in consents
        ]

        return {
            "exportDate": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "profile": profile,
            "consents": consents_data,
            "notifications": notifications,
            "usageEvents": usage_events,
            "auditLogs": audit_logs,
        }
