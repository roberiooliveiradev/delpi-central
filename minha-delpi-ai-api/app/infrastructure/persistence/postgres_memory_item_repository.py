from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func

from app.extensions.db import db
from app.infrastructure.db.models.memory_item_model import AiMemoryItemModel


class PostgresMemoryItemRepository:
    def find_active_duplicate(
        self,
        *,
        user_id: UUID | None,
        scope: str,
        type: str,
        content_norm: str,
        project_id: UUID | None = None,
    ) -> dict | None:
        query = AiMemoryItemModel.query.filter(
            AiMemoryItemModel.scope == scope,
            AiMemoryItemModel.type == type,
            AiMemoryItemModel.content_norm == content_norm,
            AiMemoryItemModel.status == "active",
        )

        query = (
            query.filter(AiMemoryItemModel.user_id.is_(None))
            if user_id is None
            else query.filter(AiMemoryItemModel.user_id == user_id)
        )

        if project_id is None:
            query = query.filter(AiMemoryItemModel.project_id.is_(None))
        else:
            query = query.filter(AiMemoryItemModel.project_id == project_id)

        row = query.order_by(AiMemoryItemModel.created_at.desc()).first()
        return self._to_dict(row) if row else None

    def create(
        self,
        *,
        type: str,
        content: str,
        content_norm: str,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        session_id: UUID | None = None,
        scope: str = "user",
        content_json: dict | None = None,
        confidence: float | None = None,
        source: str = "auto",
        status: str = "active",
        created_by: UUID | None = None,
        expires_at: datetime | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        row = AiMemoryItemModel(
            type=type,
            content=content,
            content_norm=content_norm[:320],
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            scope=scope,
            content_json=content_json,
            confidence=confidence,
            source=source,
            status=status,
            created_by=created_by,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        db.session.add(row)
        db.session.flush()
        return self._to_dict(row)

    def bump_evidence(self, item_id: int, *, confidence: float | None = None) -> dict | None:
        row = AiMemoryItemModel.query.filter_by(id=item_id).first()

        if not row:
            return None

        row.evidence_count = int(row.evidence_count or 0) + 1

        if confidence is not None:
            row.confidence = confidence

        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._to_dict(row)

    def list_active_for_context(
        self,
        *,
        user_id: UUID | None,
        project_id: UUID | None = None,
        limit: int = 20,
    ) -> list[dict]:
        now = datetime.now(timezone.utc)
        query = AiMemoryItemModel.query.filter(AiMemoryItemModel.status == "active")

        if user_id is not None:
            if project_id is not None:
                query = query.filter(
                    db.or_(
                        AiMemoryItemModel.user_id == user_id,
                        AiMemoryItemModel.project_id == project_id,
                    )
                )
            else:
                query = query.filter(AiMemoryItemModel.user_id == user_id)
        elif project_id is not None:
            query = query.filter(AiMemoryItemModel.project_id == project_id)
        else:
            return []

        query = query.filter(
            db.or_(
                AiMemoryItemModel.expires_at.is_(None),
                AiMemoryItemModel.expires_at > now,
            )
        )

        rows = (
            query.order_by(
                AiMemoryItemModel.evidence_count.desc(),
                AiMemoryItemModel.updated_at.desc(),
            )
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [self._to_dict(row) for row in rows]

    def list_items(
        self,
        *,
        user_id: UUID | None = None,
        scope: str | None = None,
        type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = AiMemoryItemModel.query

        if user_id is not None:
            query = query.filter(AiMemoryItemModel.user_id == user_id)

        if scope:
            query = query.filter(AiMemoryItemModel.scope == scope)

        if type:
            query = query.filter(AiMemoryItemModel.type == type)

        if status:
            query = query.filter(AiMemoryItemModel.status == status)

        total = query.count()
        rows = (
            query.order_by(AiMemoryItemModel.created_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )
        return [self._to_dict(row) for row in rows], total

    def get(self, item_id: int) -> dict | None:
        row = AiMemoryItemModel.query.filter_by(id=item_id).first()
        return self._to_dict(row) if row else None

    def set_status(
        self,
        item_id: int,
        *,
        status: str,
        reviewer_id: UUID | None = None,
    ) -> dict | None:
        row = AiMemoryItemModel.query.filter_by(id=item_id).first()

        if not row:
            return None

        row.status = status
        row.updated_at = datetime.now(timezone.utc)

        if reviewer_id is not None:
            row.reviewer_id = reviewer_id

        db.session.flush()
        return self._to_dict(row)

    def list_active_for_reindex(self, *, limit: int = 2000) -> list[dict]:
        rows = (
            AiMemoryItemModel.query.filter(AiMemoryItemModel.status == "active")
            .order_by(AiMemoryItemModel.updated_at.desc())
            .limit(max(1, min(int(limit), 5000)))
            .all()
        )
        return [self._to_dict(row) for row in rows]

    def summary(self) -> dict:
        model = AiMemoryItemModel

        by_status = dict(
            db.session.query(model.status, func.count()).group_by(model.status).all()
        )
        by_type = dict(
            db.session.query(model.type, func.count())
            .filter(model.status == "active")
            .group_by(model.type)
            .all()
        )

        total = sum(by_status.values())
        active = int(by_status.get("active", 0))
        forgotten = int(by_status.get("forgotten", 0))

        return {
            "total": int(total),
            "active": active,
            "forgotten": forgotten,
            "byStatus": {str(key): int(value) for key, value in by_status.items()},
            "byType": {str(key): int(value) for key, value in by_type.items()},
        }

    def _to_dict(self, row: AiMemoryItemModel) -> dict:
        payload = {
            "id": int(row.id),
            "userId": str(row.user_id) if row.user_id else None,
            "projectId": str(row.project_id) if row.project_id else None,
            "sessionId": str(row.session_id) if row.session_id else None,
            "scope": str(row.scope),
            "type": str(row.type),
            "content": str(row.content),
            "confidence": float(row.confidence) if row.confidence is not None else None,
            "evidenceCount": int(row.evidence_count or 0),
            "source": str(row.source),
            "status": str(row.status),
            "createdBy": str(row.created_by) if row.created_by else None,
            "reviewerId": str(row.reviewer_id) if row.reviewer_id else None,
            "expiresAt": row.expires_at.isoformat() if row.expires_at else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

        if isinstance(row.content_json, dict):
            payload["contentJson"] = dict(row.content_json)

        return payload
