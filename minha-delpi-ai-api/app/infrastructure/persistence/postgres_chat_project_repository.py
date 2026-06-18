from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_

from app.domain.entities.chat_project import ChatProject
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_project_model import AiChatProjectModel
from app.infrastructure.db.models.chat_project_share_model import AiChatProjectShareModel


class PostgresChatProjectRepository(ChatProjectRepositoryPort):
    def list_accessible(
        self,
        user_id: UUID,
        archived: bool = False,
    ) -> list[tuple[ChatProject, str]]:
        shared_project_ids = (
            db.session.query(AiChatProjectShareModel.project_id)
            .filter(AiChatProjectShareModel.target_user_id == user_id)
        )

        query = (
            AiChatProjectModel.query
            .filter(
                or_(
                    AiChatProjectModel.visibility == "public",
                    AiChatProjectModel.user_id == user_id,
                    AiChatProjectModel.id.in_(shared_project_ids),
                )
            )
        )

        if archived:
            query = query.filter(AiChatProjectModel.archived_at.isnot(None))
        else:
            query = query.filter(AiChatProjectModel.archived_at.is_(None))

        models = query.order_by(AiChatProjectModel.updated_at.desc()).all()

        return [(self._to_entity(model), self._access_role(model, user_id)) for model in models]

    def get_accessible_by_id(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> tuple[ChatProject, str] | None:
        model = AiChatProjectModel.query.filter(AiChatProjectModel.id == project_id).first()

        if not model or not self._can_access(model, user_id):
            return None

        return self._to_entity(model), self._access_role(model, user_id)

    def create(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
        instructions: str | None = None,
        default_agent_id: UUID | None = None,
        visibility: str = "private",
        icon: str | None = None,
        color: str | None = None,
        metadata: dict | None = None,
    ) -> ChatProject:
        model = AiChatProjectModel(
            user_id=user_id,
            name=name,
            description=description,
            instructions=instructions,
            default_agent_id=default_agent_id,
            visibility=visibility,
            icon=icon,
            color=color,
            project_metadata=metadata,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_entity(model)

    def update(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        apply_null: frozenset[str] | None = None,
        **fields,
    ) -> ChatProject | None:
        model = AiChatProjectModel.query.filter(AiChatProjectModel.id == project_id).first()

        if not model or not self._can_edit(model, user_id):
            return None

        nullable_fields = apply_null or frozenset()
        archived = fields.pop("archived", None)

        if archived is True:
            model.archived_at = datetime.now(timezone.utc)
        elif archived is False:
            model.archived_at = None

        for key, value in fields.items():
            if value is None and key not in nullable_fields:
                continue

            if hasattr(model, key):
                setattr(model, key, value)

        db.session.flush()

        return self._to_entity(model)

    def delete(self, project_id: UUID, user_id: UUID) -> bool:
        model = AiChatProjectModel.query.filter(AiChatProjectModel.id == project_id).first()

        if not model or model.user_id != user_id:
            return False

        db.session.delete(model)
        db.session.flush()

        return True

    def share(
        self,
        project_id: UUID,
        user_id: UUID,
        target_user_id: UUID,
        role: str,
    ) -> bool:
        model = AiChatProjectModel.query.filter(AiChatProjectModel.id == project_id).first()

        if not model or model.user_id != user_id:
            return False

        share = (
            AiChatProjectShareModel.query
            .filter(AiChatProjectShareModel.project_id == project_id)
            .filter(AiChatProjectShareModel.target_user_id == target_user_id)
            .first()
        )

        if share:
            share.role = role
        else:
            db.session.add(
                AiChatProjectShareModel(
                    project_id=project_id,
                    target_user_id=target_user_id,
                    role=role,
                )
            )

        db.session.flush()

        return True

    def list_shares(self, project_id: UUID, user_id: UUID) -> list[dict]:
        model = AiChatProjectModel.query.filter(AiChatProjectModel.id == project_id).first()

        if not model or model.user_id != user_id:
            return []

        rows = (
            AiChatProjectShareModel.query
            .filter(AiChatProjectShareModel.project_id == project_id)
            .order_by(AiChatProjectShareModel.created_at.asc())
            .all()
        )

        return [
            {
                "id": str(row.id),
                "target_user_id": str(row.target_user_id),
                "role": row.role,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

    def revoke_share(self, project_id: UUID, user_id: UUID, target_user_id: UUID) -> bool:
        model = AiChatProjectModel.query.filter(AiChatProjectModel.id == project_id).first()

        if not model or model.user_id != user_id:
            return False

        deleted = (
            AiChatProjectShareModel.query
            .filter(AiChatProjectShareModel.project_id == project_id)
            .filter(AiChatProjectShareModel.target_user_id == target_user_id)
            .delete()
        )

        db.session.flush()

        return bool(deleted)

    def _can_access(self, model: AiChatProjectModel, user_id: UUID) -> bool:
        if model.visibility == "public":
            return True

        if model.user_id == user_id:
            return True

        return (
            AiChatProjectShareModel.query
            .filter(AiChatProjectShareModel.project_id == model.id)
            .filter(AiChatProjectShareModel.target_user_id == user_id)
            .first()
            is not None
        )

    def _can_edit(self, model: AiChatProjectModel, user_id: UUID) -> bool:
        if model.user_id == user_id:
            return True

        share = (
            AiChatProjectShareModel.query
            .filter(AiChatProjectShareModel.project_id == model.id)
            .filter(AiChatProjectShareModel.target_user_id == user_id)
            .first()
        )

        return bool(share and share.role == "editor")

    def _access_role(self, model: AiChatProjectModel, user_id: UUID) -> str:
        if model.user_id == user_id:
            return "owner"

        share = (
            AiChatProjectShareModel.query
            .filter(AiChatProjectShareModel.project_id == model.id)
            .filter(AiChatProjectShareModel.target_user_id == user_id)
            .first()
        )

        if share:
            return share.role

        return "viewer"

    def _to_entity(self, model: AiChatProjectModel) -> ChatProject:
        return ChatProject(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            instructions=model.instructions,
            default_agent_id=model.default_agent_id,
            visibility=model.visibility,
            icon=model.icon,
            color=model.color,
            archived_at=model.archived_at,
            metadata=model.project_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
