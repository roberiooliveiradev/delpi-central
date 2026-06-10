from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class AnonymizeUserDataUseCase:
    """Anonimiza dados pessoais de um titular em todas as tabelas do core-api."""

    def __init__(self, uow):
        self._uow = uow

    def execute(self, target_user_id: str, *, actor_user_id: str) -> dict:
        uid = UUID(target_user_id)
        actor_uid = UUID(actor_user_id)

        if uid == actor_uid:
            raise ValueError("Não é permitido anonimizar a si mesmo.")

        user = self._uow.users.get_by_id(uid)
        if not user:
            raise LookupError("Usuário não encontrado.")

        anon_email = f"anon-{uid}@removed.lgpd"
        anon_name = "Usuário Anonimizado"

        session = self._uow.session

        from app.infrastructure.db.models.user import User
        from app.infrastructure.db.models.audit_log import AuditLog
        from app.infrastructure.db.models.notification import Notification
        from app.infrastructure.db.models.app_module import App

        session.query(User).filter_by(id=uid).update({
            "name": anon_name,
            "email": anon_email,
            "birth_date": None,
            "active": False,
        })

        audit_count = session.query(AuditLog).filter_by(user_id=uid).update({
            "ip_address": None,
            "payload": None,
        })

        notif_count = session.query(Notification).filter_by(user_id=uid).update({
            "deleted_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        })

        for field_pair in [
            ("created_by_user_id", "created_by_email", "created_by_name"),
            ("updated_by_user_id", "updated_by_email", "updated_by_name"),
        ]:
            uid_field, email_field, name_field = field_pair
            session.query(App).filter(
                getattr(App, uid_field) == uid
            ).update({
                email_field: anon_email,
                name_field: anon_name,
            })

        from app.infrastructure.db.models.user_consent import UserConsent
        from app.application.services.usage_tracking_purge_service import (
            purge_usage_tracking_data,
        )

        consent_count = session.query(UserConsent).filter_by(user_id=uid).delete()
        usage_events_removed = purge_usage_tracking_data(self._uow, user_id=uid)
        self._uow.portal_tour.delete_progress(str(uid))

        self._uow.commit()

        logger.info(
            "lgpd_user_anonymized user_id=%s actor=%s audits=%d notifs=%d consents=%d usage=%d",
            uid, actor_uid, audit_count, notif_count, consent_count, usage_events_removed,
        )

        return {
            "anonymized": True,
            "userId": str(uid),
            "auditLogsCleared": audit_count,
            "notificationsRemoved": notif_count,
            "consentsRemoved": consent_count,
            "usageEventsRemoved": usage_events_removed,
        }
