from datetime import datetime, timezone
from uuid import UUID

from app.application.services.audit_csv_exporter_service import AuditCsvExporterService
from app.domain.ports.audit_repository_port import AuditLogQuery, AuditRepositoryPort


class ListAdminAuditLogsUseCase:
    EXPORT_MAX_ITEMS = 5000
    TIMELINE_MAX_DAYS = 31

    def __init__(
        self,
        audit_repository: AuditRepositoryPort,
        csv_exporter: AuditCsvExporterService | None = None,
    ):
        self.audit_repository = audit_repository
        self.csv_exporter = csv_exporter or AuditCsvExporterService()

    def execute(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        action: str | None = None,
        context: str | None = None,
        user_id: str | None = None,
        trace_id: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        query = self._build_query(
            limit=limit,
            offset=offset,
            action=action,
            context=context,
            user_id=user_id,
            trace_id=trace_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
            max_limit=200,
        )

        items, total = self.audit_repository.list_logs_page(query)

        return {
            "items": items,
            "pagination": {
                "limit": query.limit,
                "offset": query.offset,
                "total": total,
                "hasNext": query.offset + query.limit < total,
                "hasPrevious": query.offset > 0,
            },
            "filters": {
                "action": action or "",
                "context": context or "",
                "userId": user_id or "",
                "traceId": trace_id or "",
                "search": search or "",
                "dateFrom": date_from or "",
                "dateTo": date_to or "",
            },
        }

    def execute_timeline(
        self,
        *,
        action: str | None = None,
        context: str | None = None,
        user_id: str | None = None,
        trace_id: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        max_days: int | None = None,
    ) -> dict:
        query = self._build_query(
            limit=1,
            offset=0,
            action=action,
            context=context,
            user_id=user_id,
            trace_id=trace_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
            max_limit=1,
        )

        safe_max_days = self.TIMELINE_MAX_DAYS

        if max_days is not None:
            safe_max_days = max(1, min(int(max_days), 90))

        timeline = self.audit_repository.get_timeline_summary(
            query,
            max_days=safe_max_days,
        )

        return {
            **timeline,
            "filters": {
                "action": action or "",
                "context": context or "",
                "userId": user_id or "",
                "traceId": trace_id or "",
                "search": search or "",
                "dateFrom": date_from or "",
                "dateTo": date_to or "",
            },
        }

    def execute_export(
        self,
        *,
        action: str | None = None,
        context: str | None = None,
        user_id: str | None = None,
        trace_id: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        items, total = self._export_items(
            action=action,
            context=context,
            user_id=user_id,
            trace_id=trace_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "items": items,
            "total": total,
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "action": action or "",
                "context": context or "",
                "userId": user_id or "",
                "traceId": trace_id or "",
                "search": search or "",
                "dateFrom": date_from or "",
                "dateTo": date_to or "",
            },
        }

    def execute_export_csv(
        self,
        *,
        action: str | None = None,
        context: str | None = None,
        user_id: str | None = None,
        trace_id: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        items, _total = self._export_items(
            action=action,
            context=context,
            user_id=user_id,
            trace_id=trace_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )

        return self.csv_exporter.export_rows(items)

    def execute_detail(self, log_id: int) -> dict | None:
        log = self.audit_repository.get_log(log_id)

        if not log:
            return None

        related = []
        trace_related = []

        if log.get("promptHash"):
            related = self.audit_repository.list_by_prompt_hash(
                prompt_hash=log["promptHash"],
                exclude_id=log["id"],
            )

        if log.get("traceId"):
            trace_related = self.audit_repository.list_by_trace_id(
                trace_id=log["traceId"],
                exclude_id=log["id"],
            )

        return {
            "log": log,
            "relatedLogs": related,
            "traceRelatedLogs": trace_related,
        }

    def _export_items(
        self,
        *,
        action: str | None,
        context: str | None,
        user_id: str | None,
        trace_id: str | None,
        search: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> tuple[list[dict], int]:
        query = self._build_query(
            limit=self.EXPORT_MAX_ITEMS,
            offset=0,
            action=action,
            context=context,
            user_id=user_id,
            trace_id=trace_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
            max_limit=self.EXPORT_MAX_ITEMS,
        )

        return self.audit_repository.list_logs_page(query)

    def _build_query(
        self,
        *,
        limit: int,
        offset: int,
        action: str | None,
        context: str | None,
        user_id: str | None,
        trace_id: str | None,
        search: str | None,
        date_from: str | None,
        date_to: str | None,
        max_limit: int,
    ) -> AuditLogQuery:
        safe_limit = max(1, min(int(limit), max_limit))
        safe_offset = max(0, int(offset))

        parsed_user_id = None

        if user_id:
            parsed_user_id = UUID(str(user_id).strip())

        return AuditLogQuery(
            limit=safe_limit,
            offset=safe_offset,
            action=(action or "").strip() or None,
            context=(context or "").strip() or None,
            user_id=parsed_user_id,
            trace_id=(trace_id or "").strip() or None,
            search=(search or "").strip() or None,
            date_from=self._parse_datetime(date_from, end_of_day=False),
            date_to=self._parse_datetime(date_to, end_of_day=True),
        )

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
