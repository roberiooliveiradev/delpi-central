from datetime import datetime, timezone
from uuid import UUID

from app.extensions.db import db
from app.infrastructure.db.models.admin_guideline_model import AiAdminGuidelineModel


class PostgresAdminGuidelineRepository:
    def list(self) -> list[dict]:
        rows = (
            AiAdminGuidelineModel.query
            .order_by(AiAdminGuidelineModel.created_at.asc())
            .all()
        )

        return [self._to_dict(row) for row in rows]

    def create_or_update(
        self,
        *,
        guideline_id: str | None,
        title: str,
        description: str,
        content: str,
        category: str,
        status: str,
        metadata: dict | None,
        user_id: str | None,
    ) -> dict:
        row = None

        if guideline_id:
            row = AiAdminGuidelineModel.query.filter_by(id=UUID(str(guideline_id))).first()

        if row is None:
            row = AiAdminGuidelineModel(
                title=title,
                description=description,
                content=content,
                category=category,
                status=status,
                guideline_metadata=metadata or {},
                created_by=user_id,
                updated_by=user_id,
            )
            db.session.add(row)
        else:
            row.title = title
            row.description = description
            row.content = content
            row.category = category
            row.status = status
            row.guideline_metadata = metadata or {}
            row.updated_by = user_id

        db.session.flush()
        return self._to_dict(row)

    def publish(self, guideline_id: str, *, user_id: str | None) -> dict | None:
        row = AiAdminGuidelineModel.query.filter_by(id=UUID(str(guideline_id))).first()

        if row is None:
            return None

        row.status = "active"
        row.published_at = datetime.now(timezone.utc)
        row.archived_at = None
        row.updated_by = user_id
        db.session.flush()

        return self._to_dict(row)

    def archive(self, guideline_id: str, *, user_id: str | None) -> dict | None:
        row = AiAdminGuidelineModel.query.filter_by(id=UUID(str(guideline_id))).first()

        if row is None:
            return None

        row.status = "archived"
        row.archived_at = datetime.now(timezone.utc)
        row.updated_by = user_id
        db.session.flush()

        return self._to_dict(row)

    def _to_dict(self, row: AiAdminGuidelineModel) -> dict:
        return {
            "id": str(row.id),
            "title": row.title,
            "description": row.description,
            "content": row.content,
            "category": row.category,
            "status": row.status,
            "metadata": row.guideline_metadata or {},
            "createdBy": row.created_by,
            "updatedBy": row.updated_by,
            "publishedAt": row.published_at.isoformat() if row.published_at else None,
            "archivedAt": row.archived_at.isoformat() if row.archived_at else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
