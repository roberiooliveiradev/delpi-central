"""Métricas de adoção do chat via auditoria — Playbook 10."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from app.domain.ports.chat_adoption_metrics_repository_port import (
    ChatAdoptionMetricsRepositoryPort,
)


class ChatQualityAdoptionMetricsService:
    _MESSAGE_ACTIONS = ("chat.message.sent", "chat.message.streamed")
    _metrics_repository: ClassVar[ChatAdoptionMetricsRepositoryPort | None] = None

    @classmethod
    def configure(cls, repository: ChatAdoptionMetricsRepositoryPort) -> None:
        cls._metrics_repository = repository

    @classmethod
    def _require_repository(cls) -> ChatAdoptionMetricsRepositoryPort:
        if cls._metrics_repository is None:
            raise RuntimeError(
                "ChatAdoptionMetricsRepositoryPort não configurado — "
                "chame configure_domain_infrastructure_ports()"
            )

        return cls._metrics_repository

    @classmethod
    def snapshot(cls, *, hours: int = 168) -> dict[str, Any]:
        safe_hours = max(1, min(int(hours), 720))
        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)
        repository = cls._require_repository()

        messages_sent = repository.count_audit_actions(cls._MESSAGE_ACTIONS, since=since)
        feedback_submitted = repository.count_audit_action("chat.feedback.submitted", since=since)
        interactivity_clicks = repository.count_audit_action("chat.interactivity.clicked", since=since)
        presentation_events = repository.count_audit_action("chat.presentation.event", since=since)
        active_sessions = repository.count_active_sessions(since=since)
        active_users = repository.count_active_users(since=since)

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
    def _rate(cls, numerator: int, denominator: int) -> float | None:
        if denominator <= 0:
            return None

        return round(numerator / denominator, 4)
