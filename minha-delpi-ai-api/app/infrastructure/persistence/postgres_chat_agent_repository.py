from uuid import UUID

from sqlalchemy import or_

from app.domain.entities.chat_agent import ChatAgent
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_agent_action_model import AiChatAgentActionModel
from app.infrastructure.db.models.chat_agent_model import AiChatAgentModel
from app.infrastructure.db.models.chat_agent_share_model import AiChatAgentShareModel


class PostgresChatAgentRepository(ChatAgentRepositoryPort):
    def list_accessible(self, user_id: UUID) -> list[tuple[ChatAgent, str]]:
        shared_agent_ids = (
            db.session.query(AiChatAgentShareModel.agent_id)
            .filter(AiChatAgentShareModel.target_user_id == user_id)
        )

        models = (
            AiChatAgentModel.query
            .filter(AiChatAgentModel.enabled.is_(True))
            .filter(
                or_(
                    AiChatAgentModel.visibility == "system",
                    AiChatAgentModel.visibility == "public",
                    AiChatAgentModel.owner_user_id == user_id,
                    AiChatAgentModel.id.in_(shared_agent_ids),
                )
            )
            .order_by(AiChatAgentModel.name.asc())
            .all()
        )

        result: list[tuple[ChatAgent, str]] = []

        for model in models:
            result.append((self._to_entity(model), self._access_role(model, user_id)))

        return result

    def get_accessible_by_id(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> tuple[ChatAgent, str] | None:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_access(model, user_id):
            return None

        return self._to_entity(model), self._access_role(model, user_id)

    def get_enabled_by_key(self, key: str, user_id: UUID | None = None) -> ChatAgent | None:
        query = (
            AiChatAgentModel.query
            .filter(AiChatAgentModel.key == key)
            .filter(AiChatAgentModel.enabled.is_(True))
        )

        model = query.first()

        if not model:
            return None

        if user_id and not self._can_access(model, user_id):
            return None

        return self._to_entity(model)

    def create(
        self,
        owner_user_id: UUID,
        key: str,
        name: str,
        description: str | None,
        system_prompt: str | None,
        visibility: str,
        category: str | None,
        icon: str | None,
        response_style: str | None,
        metadata: dict | None,
    ) -> ChatAgent:
        model = AiChatAgentModel(
            owner_user_id=owner_user_id,
            key=key,
            name=name,
            description=description,
            system_prompt=system_prompt,
            visibility=visibility,
            category=category,
            icon=icon,
            response_style=response_style,
            agent_metadata=metadata,
            enabled=True,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_entity(model)

    def update(
        self,
        agent_id: UUID,
        user_id: UUID,
        **fields,
    ) -> ChatAgent | None:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(model, user_id):
            return None

        for key, value in fields.items():
            if value is not None and hasattr(model, key):
                setattr(model, key, value)

        db.session.flush()

        return self._to_entity(model)

    def delete(self, agent_id: UUID, user_id: UUID) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or model.owner_user_id != user_id:
            return False

        db.session.delete(model)
        db.session.flush()

        return True

    def share(
        self,
        agent_id: UUID,
        user_id: UUID,
        target_user_id: UUID,
        role: str,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or model.owner_user_id != user_id:
            return False

        share = (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == agent_id)
            .filter(AiChatAgentShareModel.target_user_id == target_user_id)
            .first()
        )

        if share:
            share.role = role
        else:
            db.session.add(
                AiChatAgentShareModel(
                    agent_id=agent_id,
                    target_user_id=target_user_id,
                    role=role,
                )
            )

        db.session.flush()

        return True

    def upsert_action(
        self,
        agent_id: UUID,
        user_id: UUID,
        provider_key: str,
        action_id: str,
        sensitivity: str,
        requires_confirmation: bool,
        enabled: bool,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(model, user_id):
            return False

        action = (
            AiChatAgentActionModel.query
            .filter(AiChatAgentActionModel.agent_id == agent_id)
            .filter(AiChatAgentActionModel.provider_key == provider_key)
            .filter(AiChatAgentActionModel.action_id == action_id)
            .first()
        )

        if action:
            action.enabled = enabled
            action.sensitivity = sensitivity
            action.requires_confirmation = requires_confirmation
        else:
            db.session.add(
                AiChatAgentActionModel(
                    agent_id=agent_id,
                    provider_key=provider_key,
                    action_id=action_id,
                    sensitivity=sensitivity,
                    requires_confirmation=requires_confirmation,
                    enabled=enabled,
                )
            )

        db.session.flush()

        return True

    def _can_access(self, model: AiChatAgentModel, user_id: UUID) -> bool:
        if model.visibility in {"system", "public"}:
            return True

        if model.owner_user_id == user_id:
            return True

        return (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == model.id)
            .filter(AiChatAgentShareModel.target_user_id == user_id)
            .first()
            is not None
        )

    def _can_edit(self, model: AiChatAgentModel, user_id: UUID) -> bool:
        if model.owner_user_id == user_id:
            return True

        share = (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == model.id)
            .filter(AiChatAgentShareModel.target_user_id == user_id)
            .first()
        )

        return bool(share and share.role == "editor")

    def _access_role(self, model: AiChatAgentModel, user_id: UUID) -> str:
        if model.visibility == "system":
            return "system"

        if model.owner_user_id == user_id:
            return "owner"

        share = (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == model.id)
            .filter(AiChatAgentShareModel.target_user_id == user_id)
            .first()
        )

        if share:
            return share.role

        return "viewer"

    def _to_entity(self, model: AiChatAgentModel) -> ChatAgent:
        return ChatAgent(
            id=model.id,
            key=model.key,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            enabled=model.enabled,
            metadata=model.agent_metadata,
            owner_user_id=model.owner_user_id,
            visibility=model.visibility,
            category=model.category,
            icon=model.icon,
            response_style=model.response_style,
            max_tool_calls=model.max_tool_calls,
            requires_confirmation_for_write=model.requires_confirmation_for_write,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
