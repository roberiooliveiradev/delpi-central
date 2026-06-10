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
                "callerAppId": e.caller_app_id,
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

        tour_progress = self._uow.portal_tour.get_progress(user_id)
        portal_tour = None
        if tour_progress:
            portal_tour = {
                "tourVersion": tour_progress.tour_version,
                "status": tour_progress.status,
                "completedQuestIds": list(tour_progress.completed_quest_ids),
                "startedAt": tour_progress.started_at.isoformat() if tour_progress.started_at else None,
                "lastActivityAt": tour_progress.last_activity_at.isoformat() if tour_progress.last_activity_at else None,
                "completedAt": tour_progress.completed_at.isoformat() if tour_progress.completed_at else None,
            }

        from app.infrastructure.db.models.user_portal_tour_progress import PortalTourQuestEvent
        quest_events_q = (
            session.query(PortalTourQuestEvent)
            .filter_by(user_id=uid)
            .order_by(PortalTourQuestEvent.completed_at.desc())
            .limit(500)
            .all()
        )
        portal_tour_quest_events = [
            {
                "tourVersion": event.tour_version,
                "questId": event.quest_id,
                "completedAt": event.completed_at.isoformat() if event.completed_at else None,
            }
            for event in quest_events_q
        ]

        return {
            "exportDate": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "profile": profile,
            "consents": consents_data,
            "notifications": notifications,
            "usageEvents": usage_events,
            "auditLogs": audit_logs,
            "portalTour": portal_tour,
            "portalTourQuestEvents": portal_tour_quest_events,
        }
