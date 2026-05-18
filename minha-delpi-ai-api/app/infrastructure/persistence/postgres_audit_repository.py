from collections import defaultdict
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import String, cast, func, or_

from app.application.services.audit_trace_service import resolve_audit_trace_id
from app.domain.ports.audit_repository_port import AuditLogQuery, AuditRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.audit_log_model import AiAuditLogModel


SECURITY_ACTIONS = (
    "security.input.blocked",
    "security.input.flagged",
    "admin.security.scanned",
)


class PostgresAuditRepository(AuditRepositoryPort):
    def log(
        self,
        user_id: UUID | None,
        action: str,
        prompt_hash: str | None = None,
        context: str | None = None,
        tool_calls: list | None = None,
        metadata: dict | None = None,
        trace_id: str | None = None,
    ) -> None:
        resolved_trace_id = (trace_id or resolve_audit_trace_id() or "").strip() or None

        model = AiAuditLogModel(
            user_id=user_id,
            action=action,
            prompt_hash=prompt_hash,
            trace_id=resolved_trace_id,
            context=context,
            tool_calls=tool_calls,
            audit_metadata=metadata,
        )

        db.session.add(model)
        db.session.flush()

    def list_logs_page(self, audit_query: AuditLogQuery) -> tuple[list[dict], int]:
        base_query = self._apply_filters(AiAuditLogModel.query, audit_query=audit_query)

        total = base_query.count()

        models = (
            base_query.order_by(AiAuditLogModel.created_at.desc())
            .offset(audit_query.offset)
            .limit(audit_query.limit)
            .all()
        )

        return [self._serialize(model) for model in models], total

    def list_by_prompt_hash(
        self,
        *,
        prompt_hash: str,
        limit: int = 20,
        exclude_id: int | None = None,
    ) -> list[dict]:
        safe_limit = max(1, min(int(limit), 50))

        base_query = AiAuditLogModel.query.filter(
            AiAuditLogModel.prompt_hash == prompt_hash,
        )

        if exclude_id is not None:
            base_query = base_query.filter(AiAuditLogModel.id != exclude_id)

        models = (
            base_query.order_by(AiAuditLogModel.created_at.desc())
            .limit(safe_limit)
            .all()
        )

        return [self._serialize(model) for model in models]

    def list_by_trace_id(
        self,
        *,
        trace_id: str,
        limit: int = 20,
        exclude_id: int | None = None,
    ) -> list[dict]:
        safe_limit = max(1, min(int(limit), 50))
        normalized_trace_id = str(trace_id or "").strip()

        if not normalized_trace_id:
            return []

        base_query = AiAuditLogModel.query.filter(
            AiAuditLogModel.trace_id == normalized_trace_id,
        )

        if exclude_id is not None:
            base_query = base_query.filter(AiAuditLogModel.id != exclude_id)

        models = (
            base_query.order_by(AiAuditLogModel.created_at.desc())
            .limit(safe_limit)
            .all()
        )

        return [self._serialize(model) for model in models]

    def get_timeline_summary(
        self,
        audit_query: AuditLogQuery,
        *,
        max_days: int = 31,
    ) -> dict:
        safe_max_days = max(1, min(int(max_days), 90))
        base_query = self._apply_filters(AiAuditLogModel.query, audit_query=audit_query)

        day_expr = func.date(AiAuditLogModel.created_at)
        action_rows = (
            base_query.with_entities(
                day_expr.label("day"),
                AiAuditLogModel.action.label("action"),
                func.count(AiAuditLogModel.id).label("count"),
            )
            .group_by(day_expr, AiAuditLogModel.action)
            .order_by(day_expr.desc(), func.count(AiAuditLogModel.id).desc())
            .all()
        )

        totals_by_day: dict[str, int] = defaultdict(int)
        actions_by_day: dict[str, list[dict]] = defaultdict(list)

        for day_value, action, count in action_rows:
            day_key = day_value.isoformat() if hasattr(day_value, "isoformat") else str(day_value)
            count_value = int(count or 0)
            totals_by_day[day_key] += count_value
            actions_by_day[day_key].append(
                {
                    "action": action,
                    "count": count_value,
                }
            )

        ordered_days = sorted(totals_by_day.keys(), reverse=True)[:safe_max_days]
        days_payload = []
        total_events = 0

        for day_key in ordered_days:
            day_total = totals_by_day[day_key]
            total_events += day_total

            day_start = datetime.combine(
                date_type.fromisoformat(day_key),
                datetime.min.time(),
                tzinfo=timezone.utc,
            )
            day_end = day_start + timedelta(days=1)

            recent_models = (
                base_query.filter(
                    AiAuditLogModel.created_at >= day_start,
                    AiAuditLogModel.created_at < day_end,
                )
                .order_by(AiAuditLogModel.created_at.desc())
                .limit(5)
                .all()
            )

            days_payload.append(
                {
                    "date": day_key,
                    "total": day_total,
                    "actions": actions_by_day.get(day_key, [])[:8],
                    "recent": [self._serialize(model) for model in recent_models],
                }
            )

        return {
            "days": days_payload,
            "totalEvents": total_events,
            "dayCount": len(days_payload),
        }

    def get_log(self, log_id: int) -> dict | None:
        model = AiAuditLogModel.query.filter(AiAuditLogModel.id == log_id).first()

        if not model:
            return None

        return self._serialize(model)

    def get_security_summary(self, *, hours: int = 24) -> dict:
        since = datetime.now(timezone.utc) - timedelta(hours=max(1, min(hours, 168)))

        blocked_count = self._count_security_action("security.input.blocked", since=since)
        flagged_count = self._count_security_action("security.input.flagged", since=since)
        scanned_count = self._count_security_action("admin.security.scanned", since=since)

        return {
            "windowHours": hours,
            "since": since.isoformat(),
            "blockedCount": blocked_count,
            "flaggedCount": flagged_count,
            "scannedCount": scanned_count,
            "totalEvents": blocked_count + flagged_count + scanned_count,
            "flagDistribution": self._security_flag_distribution(since=since),
        }

    def list_security_events_page(self, query: AuditLogQuery) -> tuple[list[dict], int]:
        base_query = self._apply_filters(AiAuditLogModel.query, audit_query=query)
        base_query = base_query.filter(AiAuditLogModel.action.in_(SECURITY_ACTIONS))

        total = base_query.count()

        models = (
            base_query.order_by(AiAuditLogModel.created_at.desc())
            .offset(query.offset)
            .limit(query.limit)
            .all()
        )

        return [self._serialize(model) for model in models], total

    def _count_security_action(self, action: str, *, since: datetime) -> int:
        return (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action == action)
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

    def _security_flag_distribution(self, *, since: datetime) -> list[dict]:
        rows = (
            db.session.query(AiAuditLogModel.audit_metadata)
            .filter(AiAuditLogModel.action.in_(SECURITY_ACTIONS[:2]))
            .filter(AiAuditLogModel.created_at >= since)
            .all()
        )

        counts: dict[str, int] = {}

        for row in rows:
            metadata = row[0] if isinstance(row, tuple) else row

            if not isinstance(metadata, dict):
                continue

            for flag in metadata.get("flags") or []:
                key = str(flag)
                counts[key] = counts.get(key, 0) + 1

        return [
            {"flag": flag, "count": count}
            for flag, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:12]
        ]

    def _apply_filters(self, sqlalchemy_query, *, audit_query: AuditLogQuery):
        if audit_query.action:
            sqlalchemy_query = sqlalchemy_query.filter(
                AiAuditLogModel.action.ilike(f"%{audit_query.action.strip()}%"),
            )

        if audit_query.context:
            sqlalchemy_query = sqlalchemy_query.filter(
                AiAuditLogModel.context.ilike(f"%{audit_query.context.strip()}%"),
            )

        if audit_query.user_id:
            sqlalchemy_query = sqlalchemy_query.filter(
                AiAuditLogModel.user_id == audit_query.user_id,
            )

        if audit_query.trace_id:
            sqlalchemy_query = sqlalchemy_query.filter(
                AiAuditLogModel.trace_id == audit_query.trace_id.strip(),
            )

        if audit_query.date_from:
            sqlalchemy_query = sqlalchemy_query.filter(
                AiAuditLogModel.created_at >= audit_query.date_from,
            )

        if audit_query.date_to:
            sqlalchemy_query = sqlalchemy_query.filter(
                AiAuditLogModel.created_at <= audit_query.date_to,
            )

        if audit_query.search:
            term = f"%{audit_query.search.strip()}%"
            sqlalchemy_query = sqlalchemy_query.filter(
                or_(
                    AiAuditLogModel.action.ilike(term),
                    AiAuditLogModel.context.ilike(term),
                    cast(AiAuditLogModel.user_id, String).ilike(term),
                    AiAuditLogModel.prompt_hash.ilike(term),
                    AiAuditLogModel.trace_id.ilike(term),
                ),
            )

        return sqlalchemy_query

    def _serialize(self, model: AiAuditLogModel) -> dict:
        return {
            "id": model.id,
            "userId": str(model.user_id) if model.user_id else None,
            "action": model.action,
            "promptHash": model.prompt_hash,
            "traceId": model.trace_id,
            "context": model.context,
            "toolCalls": model.tool_calls,
            "metadata": model.audit_metadata,
            "createdAt": model.created_at.isoformat(),
        }
