from datetime import datetime, timezone

from app.extensions.db import db
from app.infrastructure.db.models.chat_quality_report_model import AiChatQualityReportModel


class PostgresChatQualityReportRepository:
    def create(
        self,
        *,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        summary_json: dict,
        markdown: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        row = AiChatQualityReportModel(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            summary_json=summary_json,
            markdown=markdown,
            created_at=now,
        )
        db.session.add(row)
        db.session.flush()
        return self._to_dict(row)

    def get_latest(self, *, report_type: str = "weekly") -> dict | None:
        row = (
            AiChatQualityReportModel.query.filter_by(report_type=report_type)
            .order_by(AiChatQualityReportModel.created_at.desc())
            .first()
        )

        if not row:
            return None

        return self._to_dict(row)

    def list_recent(self, *, report_type: str = "weekly", limit: int = 12) -> list[dict]:
        rows = (
            AiChatQualityReportModel.query.filter_by(report_type=report_type)
            .order_by(AiChatQualityReportModel.created_at.desc())
            .limit(max(1, min(limit, 52)))
            .all()
        )

        return [self._to_dict(row) for row in rows]

    def _to_dict(self, row: AiChatQualityReportModel) -> dict:
        return {
            "id": int(row.id),
            "reportType": str(row.report_type),
            "periodStart": row.period_start.isoformat() if row.period_start else None,
            "periodEnd": row.period_end.isoformat() if row.period_end else None,
            "summary": row.summary_json if isinstance(row.summary_json, dict) else {},
            "markdown": str(row.markdown or ""),
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        }
