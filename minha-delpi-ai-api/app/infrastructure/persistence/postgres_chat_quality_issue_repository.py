from datetime import datetime, timedelta, timezone

from app.extensions.db import db
from app.infrastructure.db.models.chat_quality_issue_model import AiChatQualityIssueModel


class PostgresChatQualityIssueRepository:
    def find_open_by_code(self, code: str, *, within_days: int = 7) -> dict | None:
        since = datetime.now(timezone.utc) - timedelta(days=max(1, within_days))
        row = (
            AiChatQualityIssueModel.query.filter(
                AiChatQualityIssueModel.code == code,
                AiChatQualityIssueModel.status == "open",
                AiChatQualityIssueModel.created_at >= since,
            )
            .order_by(AiChatQualityIssueModel.created_at.desc())
            .first()
        )

        if not row:
            return None

        return self._to_dict(row)

    def create(
        self,
        *,
        code: str,
        title: str,
        description: str,
        source: str,
        metadata: dict | None = None,
        external_url: str | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        row = AiChatQualityIssueModel(
            code=code,
            title=title[:240],
            description=description,
            status="open",
            source=source,
            issue_metadata=metadata,
            external_url=external_url,
            created_at=now,
            updated_at=now,
        )
        db.session.add(row)
        db.session.flush()
        return self._to_dict(row)

    def list_issues(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = AiChatQualityIssueModel.query

        if status:
            query = query.filter(AiChatQualityIssueModel.status == status)

        total = query.count()
        rows = (
            query.order_by(AiChatQualityIssueModel.created_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )

        return [self._to_dict(row) for row in rows], total

    def update_status(self, issue_id: int, *, status: str) -> dict | None:
        row = AiChatQualityIssueModel.query.filter_by(id=issue_id).first()

        if not row:
            return None

        now = datetime.now(timezone.utc)
        row.status = status
        row.updated_at = now

        if status in {"resolved", "dismissed"}:
            row.resolved_at = now
        else:
            row.resolved_at = None

        db.session.flush()
        return self._to_dict(row)

    def _to_dict(self, row: AiChatQualityIssueModel) -> dict:
        payload = {
            "id": int(row.id),
            "code": str(row.code),
            "title": str(row.title),
            "description": str(row.description),
            "status": str(row.status),
            "source": str(row.source),
            "externalUrl": row.external_url,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
            "resolvedAt": row.resolved_at.isoformat() if row.resolved_at else None,
        }

        if isinstance(row.issue_metadata, dict):
            payload["metadata"] = dict(row.issue_metadata)

        return payload
