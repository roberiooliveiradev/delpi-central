"""
Job de retenção de dados — LGPD Art. 15/16.

Executa limpeza periódica de dados pessoais que excederam o prazo de retenção.
Deve ser agendado via cron ou scheduler externo (ex.: a cada 24h).

Uso: flask data-retention run
"""
import logging
from datetime import datetime, timedelta, timezone

from app.extensions.db import db
from app.infrastructure.db.models.audit_log import AuditLog
from app.infrastructure.db.models.notification import Notification
from app.infrastructure.db.models.app_usage_event import AppUsageEvent

logger = logging.getLogger(__name__)

AUDIT_LOG_RETENTION_DAYS = 730
NOTIFICATION_RETENTION_DAYS = 180
DELETED_NOTIFICATION_RETENTION_DAYS = 30
USAGE_EVENT_RETENTION_DAYS = 365


def run_data_retention():
    """Remove ou anonimiza dados que excederam o prazo de retenção."""
    now = datetime.now(timezone.utc)
    results = {}

    audit_cutoff = now - timedelta(days=AUDIT_LOG_RETENTION_DAYS)
    count = db.session.query(AuditLog).filter(
        AuditLog.created_at < audit_cutoff
    ).update({"ip_address": None, "payload": None})
    results["audit_logs_anonymized"] = count

    deleted_notif_cutoff = now - timedelta(days=DELETED_NOTIFICATION_RETENTION_DAYS)
    count = db.session.query(Notification).filter(
        Notification.deleted_at.isnot(None),
        Notification.deleted_at < deleted_notif_cutoff,
    ).delete()
    results["deleted_notifications_purged"] = count

    notif_cutoff = now - timedelta(days=NOTIFICATION_RETENTION_DAYS)
    count = db.session.query(Notification).filter(
        Notification.created_at < notif_cutoff,
    ).delete()
    results["old_notifications_purged"] = count

    usage_cutoff = now - timedelta(days=USAGE_EVENT_RETENTION_DAYS)
    count = db.session.query(AppUsageEvent).filter(
        AppUsageEvent.opened_at < usage_cutoff,
    ).delete()
    results["usage_events_purged"] = count

    db.session.commit()

    logger.info("data_retention_completed results=%s", results)
    return results
