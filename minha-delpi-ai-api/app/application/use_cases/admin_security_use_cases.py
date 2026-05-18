from datetime import datetime, timezone
from uuid import UUID

from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.domain.services.chat_input_security_service import ChatInputSecurityService
from app.domain.ports.audit_repository_port import AuditLogQuery, AuditRepositoryPort
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository


class GetAdminSecurityConfigUseCase:
    def __init__(self, input_security_service: ChatInputSecurityService | None = None):
        self.input_security_service = input_security_service or ChatInputSecurityService()

    def execute(self) -> dict:
        return self.input_security_service.build_config()


class GetAdminSecuritySummaryUseCase:
    def __init__(self, audit_repository: AuditRepositoryPort | None = None):
        self.audit_repository = audit_repository or PostgresAuditRepository()

    def execute(self, *, hours: int = 24) -> dict:
        if not hasattr(self.audit_repository, "get_security_summary"):
            return {
                "windowHours": hours,
                "blockedCount": 0,
                "flaggedCount": 0,
                "scannedCount": 0,
                "totalEvents": 0,
                "flagDistribution": [],
            }

        return self.audit_repository.get_security_summary(hours=hours)


class ListAdminSecurityEventsUseCase:
    def __init__(self, audit_repository: AuditRepositoryPort | None = None):
        self.audit_repository = audit_repository or PostgresAuditRepository()

    def execute(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        action: str | None = None,
        user_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        query = AuditLogQuery(
            limit=max(1, min(int(limit), 200)),
            offset=max(0, int(offset)),
            action=(action or "").strip() or None,
            user_id=UUID(str(user_id).strip()) if user_id else None,
            date_from=self._parse_datetime(date_from, end_of_day=False),
            date_to=self._parse_datetime(date_to, end_of_day=True),
        )

        if hasattr(self.audit_repository, "list_security_events_page"):
            items, total = self.audit_repository.list_security_events_page(query)
        else:
            items, total = [], 0

        return {
            "items": items,
            "pagination": {
                "limit": query.limit,
                "offset": query.offset,
                "total": total,
                "hasNext": query.offset + query.limit < total,
                "hasPrevious": query.offset > 0,
            },
        }

    def _parse_datetime(self, value: str | None, *, end_of_day: bool) -> datetime | None:
        if not value:
            return None

        normalized = str(value).strip()

        if not normalized:
            return None

        if len(normalized) == 10:
            normalized = f"{normalized}T23:59:59" if end_of_day else f"{normalized}T00:00:00"

        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)


class ScanAdminSecurityInputUseCase:
    def __init__(
        self,
        *,
        message_security_service: ChatMessageSecurityService | None = None,
        audit_repository: AuditRepositoryPort | None = None,
    ):
        self.message_security_service = message_security_service or ChatMessageSecurityService()
        self.audit_repository = audit_repository

    def execute(
        self,
        *,
        message: str,
        user_id: UUID | None = None,
        context: str | None = None,
    ) -> dict:
        result = self.message_security_service.scan_message(message, source="admin")

        if self.audit_repository:
            self.audit_repository.log(
                user_id=user_id,
                action="admin.security.scanned",
                context=context,
                metadata={
                    "riskScore": result["analysis"]["riskScore"],
                    "riskLevel": result["analysis"]["riskLevel"],
                    "flags": result["analysis"]["flags"],
                    "wouldBlock": result["wouldBlock"],
                    "wouldFlag": result["wouldFlag"],
                    "mode": Settings.CHAT_INPUT_SECURITY_MODE,
                },
            )

        return result
