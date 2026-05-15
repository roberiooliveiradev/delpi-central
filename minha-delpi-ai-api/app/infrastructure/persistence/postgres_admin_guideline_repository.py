from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.extensions.db import db
from app.infrastructure.db.models.admin_guideline_model import AiAdminGuidelineModel
from app.infrastructure.db.models.admin_guideline_version_model import AiAdminGuidelineVersionModel


class PostgresAdminGuidelineRepository:
    def list(self) -> list[dict]:
        rows = (
            AiAdminGuidelineModel.query
            .order_by(AiAdminGuidelineModel.created_at.asc())
            .all()
        )

        return [self._to_dict(row) for row in rows]

    def list_active(self, *, environment: str | None = None) -> list[dict]:
        normalized_environment = self._normalize_environment(environment)
        environments = ["global"]

        if normalized_environment != "global":
            environments.append(normalized_environment)

        rows = (
            AiAdminGuidelineModel.query
            .filter(AiAdminGuidelineModel.status == "active")
            .filter(AiAdminGuidelineModel.environment.in_(environments))
            .order_by(
                AiAdminGuidelineModel.environment.asc(),
                AiAdminGuidelineModel.category.asc(),
                AiAdminGuidelineModel.created_at.asc(),
            )
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
        environment: str | None = None,
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
                environment=self._normalize_environment(environment),
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
            row.environment = self._normalize_environment(environment)
            row.status = status
            row.guideline_metadata = metadata or {}
            row.updated_by = user_id

        db.session.flush()
        self._create_version(row, event="saved", user_id=user_id)
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
        self._create_version(row, event="published", user_id=user_id)

        return self._to_dict(row)

    def archive(self, guideline_id: str, *, user_id: str | None) -> dict | None:
        row = AiAdminGuidelineModel.query.filter_by(id=UUID(str(guideline_id))).first()

        if row is None:
            return None

        row.status = "archived"
        row.archived_at = datetime.now(timezone.utc)
        row.updated_by = user_id
        db.session.flush()
        self._create_version(row, event="archived", user_id=user_id)

        return self._to_dict(row)

    def list_versions(self, guideline_id: str) -> list[dict]:
        rows = (
            AiAdminGuidelineVersionModel.query
            .filter_by(guideline_id=UUID(str(guideline_id)))
            .order_by(AiAdminGuidelineVersionModel.version.desc())
            .all()
        )

        return [self._version_to_dict(row) for row in rows]

    def compare_versions(
        self,
        guideline_id: str,
        *,
        from_version: int,
        to_version: int,
    ) -> dict | None:
        from_row = self._get_version_row(guideline_id, from_version)
        to_row = self._get_version_row(guideline_id, to_version)

        if from_row is None or to_row is None:
            return None

        from_dict = self._version_to_dict(from_row)
        to_dict = self._version_to_dict(to_row)

        fields = ["title", "description", "content", "category", "status"]
        changes = []

        for field in fields:
            before = from_dict.get(field)
            after = to_dict.get(field)

            if before != after:
                changes.append(
                    {
                        "field": field,
                        "from": before,
                        "to": after,
                    }
                )

        return {
            "guidelineId": str(guideline_id),
            "fromVersion": from_dict,
            "toVersion": to_dict,
            "changes": changes,
        }

    def restore_version(
        self,
        guideline_id: str,
        *,
        version: int,
        user_id: str | None,
    ) -> dict | None:
        target_version = self._get_version_row(guideline_id, version)
        row = AiAdminGuidelineModel.query.filter_by(id=UUID(str(guideline_id))).first()

        if target_version is None or row is None:
            return None

        row.title = target_version.title
        row.description = target_version.description
        row.content = target_version.content
        row.category = target_version.category
        row.environment = target_version.environment
        row.status = "draft"
        row.guideline_metadata = target_version.guideline_metadata or {}
        row.updated_by = user_id

        db.session.flush()
        self._create_version(row, event="restored", user_id=user_id)

        return self._to_dict(row)

    def _get_version_row(
        self,
        guideline_id: str,
        version: int,
    ) -> AiAdminGuidelineVersionModel | None:
        return (
            AiAdminGuidelineVersionModel.query
            .filter_by(
                guideline_id=UUID(str(guideline_id)),
                version=int(version),
            )
            .first()
        )

    def _create_version(
        self,
        row: AiAdminGuidelineModel,
        *,
        event: str,
        user_id: str | None,
    ) -> None:
        latest_version = (
            db.session.query(db.func.max(AiAdminGuidelineVersionModel.version))
            .filter(AiAdminGuidelineVersionModel.guideline_id == row.id)
            .scalar()
            or 0
        )

        db.session.add(
            AiAdminGuidelineVersionModel(
                guideline_id=row.id,
                version=int(latest_version) + 1,
                title=row.title,
                description=row.description,
                content=row.content,
                category=row.category,
                environment=row.environment,
                status=row.status,
                event=event,
                guideline_metadata=row.guideline_metadata or {},
                created_by=user_id,
            )
        )
        db.session.flush()

    def _version_to_dict(self, row: AiAdminGuidelineVersionModel) -> dict:
        return {
            "id": str(row.id),
            "guidelineId": str(row.guideline_id),
            "version": row.version,
            "title": row.title,
            "description": row.description,
            "content": row.content,
            "category": row.category,
            "environment": row.environment,
            "status": row.status,
            "event": row.event,
            "metadata": row.guideline_metadata or {},
            "createdBy": row.created_by,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        }

    def _normalize_environment(self, environment: str | None) -> str:
        normalized = str(environment or "global").strip().lower()

        if normalized in {"production", "prod"}:
            return "prod"

        if normalized in {"homolog", "homologation", "staging", "stage", "hml"}:
            return "homolog"

        if normalized in {"development", "dev", "local"}:
            return "dev"

        if normalized == "global":
            return "global"

        return "global"

    def _to_dict(self, row: AiAdminGuidelineModel) -> dict:
        return {
            "id": str(row.id),
            "title": row.title,
            "description": row.description,
            "content": row.content,
            "category": row.category,
            "environment": row.environment,
            "status": row.status,
            "metadata": row.guideline_metadata or {},
            "createdBy": row.created_by,
            "updatedBy": row.updated_by,
            "publishedAt": row.published_at.isoformat() if row.published_at else None,
            "archivedAt": row.archived_at.isoformat() if row.archived_at else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
