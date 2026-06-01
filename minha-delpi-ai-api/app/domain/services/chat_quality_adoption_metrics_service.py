"""Métricas de adoção do chat via auditoria — Playbook 10."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.extensions.db import db
from app.infrastructure.db.models.audit_log_model import AiAuditLogModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel


class ChatQualityAdoptionMetricsService:
    _MESSAGE_ACTIONS = ("chat.message.sent", "chat.message.streamed")

    @classmethod
    def snapshot(cls, *, hours: int = 168) -> dict[str, Any]:
        safe_hours = max(1, min(int(hours), 720))
        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)

        messages_sent = cls._count_actions(cls._MESSAGE_ACTIONS, since=since)
        feedback_submitted = cls._count_action("chat.feedback.submitted", since=since)
        interactivity_clicks = cls._count_action("chat.interactivity.clicked", since=since)
        presentation_events = cls._count_action("chat.presentation.event", since=since)
        active_sessions = (
            db.session.query(AiChatSessionModel)
            .filter(AiChatSessionModel.updated_at >= since)
            .count()
        )
        active_users = (
            db.session.query(AiChatSessionModel.user_id)
            .filter(AiChatSessionModel.updated_at >= since)
            .distinct()
            .count()
        )

        return {
            "windowHours": safe_hours,
            "since": since.isoformat(),
            "messagesSent": messages_sent,
            "feedbackSubmitted": feedback_submitted,
            "interactivityClicks": interactivity_clicks,
            "presentationEvents": presentation_events,
            "activeSessions": active_sessions,
            "activeUsers": active_users,
            "feedbackRate": cls._rate(feedback_submitted, messages_sent),
            "chipClickRate": cls._rate(interactivity_clicks, messages_sent),
        }

    @classmethod
    def _count_action(cls, action: str, *, since: datetime) -> int:
        return (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action == action)
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

    @classmethod
    def _count_actions(cls, actions: tuple[str, ...], *, since: datetime) -> int:
        return (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action.in_(actions))
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

    @classmethod
    def _rate(cls, numerator: int, denominator: int) -> float | None:
        if denominator <= 0:
            return None

        return round(numerator / denominator, 4)
