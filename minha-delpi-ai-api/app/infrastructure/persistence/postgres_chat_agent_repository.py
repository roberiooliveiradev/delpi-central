from uuid import UUID

from sqlalchemy import or_

from app.domain.entities.chat_agent import ChatAgent
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_agent_action_model import AiChatAgentActionModel
from app.infrastructure.db.models.chat_agent_action_provider_model import AiChatAgentActionProviderModel
from app.infrastructure.db.models.external_action_model import ExternalActionModel
from app.infrastructure.db.models.external_action_provider_model import ExternalActionProviderModel
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


    def exists_by_id(self, agent_id: UUID) -> bool:
        return (
            db.session.query(AiChatAgentModel.id)
            .filter(AiChatAgentModel.id == agent_id)
            .first()
            is not None
        )

    def can_edit(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model:
            return False

        return self._can_edit(model, user_id)

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



    def list_action_providers(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[dict]:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_access(model, user_id):
            return []

        rows = (
            db.session.query(
                AiChatAgentActionProviderModel,
                ExternalActionProviderModel,
                db.func.count(ExternalActionModel.id).label("action_count"),
            )
            .outerjoin(
                ExternalActionProviderModel,
                ExternalActionProviderModel.provider_key == AiChatAgentActionProviderModel.provider_key,
            )
            .outerjoin(
                ExternalActionModel,
                ExternalActionModel.provider_id == ExternalActionProviderModel.id,
            )
            .filter(AiChatAgentActionProviderModel.agent_id == agent_id)
            .group_by(AiChatAgentActionProviderModel.id, ExternalActionProviderModel.id)
            .order_by(AiChatAgentActionProviderModel.provider_key.asc())
            .all()
        )

        return [
            self._provider_link_to_dict(link, provider, int(action_count or 0))
            for link, provider, action_count in rows
        ]

    def upsert_action_provider(
        self,
        agent_id: UUID,
        user_id: UUID,
        provider_key: str,
        enabled: bool,
        allow_read: bool,
        allow_write: bool,
        allow_admin: bool,
        requires_confirmation_for_write: bool,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(model, user_id):
            return False

        provider = ExternalActionProviderModel.query.filter(
            ExternalActionProviderModel.provider_key == provider_key
        ).first()

        if not provider:
            return False

        link = (
            AiChatAgentActionProviderModel.query
            .filter(AiChatAgentActionProviderModel.agent_id == agent_id)
            .filter(AiChatAgentActionProviderModel.provider_key == provider_key)
            .first()
        )

        if link:
            link.enabled = enabled
            link.allow_read = allow_read
            link.allow_write = allow_write
            link.allow_admin = allow_admin
            link.requires_confirmation_for_write = requires_confirmation_for_write
        else:
            db.session.add(
                AiChatAgentActionProviderModel(
                    agent_id=agent_id,
                    provider_key=provider_key,
                    enabled=enabled,
                    allow_read=allow_read,
                    allow_write=allow_write,
                    allow_admin=allow_admin,
                    requires_confirmation_for_write=requires_confirmation_for_write,
                )
            )

        db.session.flush()

        return True

    def list_enabled_provider_keys(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[str]:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_access(model, user_id):
            return []

        rows = (
            AiChatAgentActionProviderModel.query
            .filter(AiChatAgentActionProviderModel.agent_id == agent_id)
            .filter(AiChatAgentActionProviderModel.enabled.is_(True))
            .order_by(AiChatAgentActionProviderModel.provider_key.asc())
            .all()
        )

        return [row.provider_key for row in rows]

    def list_actions(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[dict]:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_access(model, user_id):
            return []

        actions = (
            AiChatAgentActionModel.query
            .filter(AiChatAgentActionModel.agent_id == agent_id)
            .order_by(
                AiChatAgentActionModel.provider_key.asc(),
                AiChatAgentActionModel.action_id.asc(),
            )
            .all()
        )

        return [self._action_to_dict(action) for action in actions]

    def list_enabled_action_ids(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[str]:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_access(model, user_id):
            return []

        provider_links = (
            AiChatAgentActionProviderModel.query
            .filter(AiChatAgentActionProviderModel.agent_id == agent_id)
            .filter(AiChatAgentActionProviderModel.enabled.is_(True))
            .all()
        )

        provider_action_ids: list[str] = []

        for link in provider_links:
            sensitivity_allowed = ["read"]

            if link.allow_write:
                sensitivity_allowed.append("write")

            if link.allow_admin:
                sensitivity_allowed.append("admin")

            rows = (
                db.session.query(ExternalActionModel.action_id)
                .join(ExternalActionProviderModel)
                .filter(ExternalActionProviderModel.provider_key == link.provider_key)
                .filter(ExternalActionProviderModel.enabled.is_(True))
                .filter(ExternalActionModel.enabled.is_(True))
                .filter(ExternalActionModel.deprecated.is_(False))
                .filter(ExternalActionModel.sensitivity.in_(sensitivity_allowed))
                .all()
            )

            provider_action_ids.extend([row.action_id for row in rows])

        explicit_rows = (
            AiChatAgentActionModel.query
            .filter(AiChatAgentActionModel.agent_id == agent_id)
            .filter(AiChatAgentActionModel.enabled.is_(True))
            .order_by(AiChatAgentActionModel.action_id.asc())
            .all()
        )

        explicit_action_ids = [row.action_id for row in explicit_rows]

        return sorted({*provider_action_ids, *explicit_action_ids})

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

    def _provider_link_to_dict(
        self,
        link: AiChatAgentActionProviderModel,
        provider: ExternalActionProviderModel | None,
        action_count: int,
    ) -> dict:
        return {
            "id": str(link.id),
            "agentId": str(link.agent_id),
            "providerKey": link.provider_key,
            "providerName": provider.name if provider else link.provider_key,
            "providerType": provider.provider_type if provider else None,
            "baseUrl": provider.base_url if provider else None,
            "openApiUrl": provider.openapi_url if provider else None,
            "enabled": link.enabled,
            "allowRead": link.allow_read,
            "allowWrite": link.allow_write,
            "allowAdmin": link.allow_admin,
            "requiresConfirmationForWrite": link.requires_confirmation_for_write,
            "actionCount": action_count,
            "createdAt": link.created_at.isoformat(),
            "updatedAt": link.updated_at.isoformat(),
        }

    def _action_to_dict(self, action: AiChatAgentActionModel) -> dict:
        return {
            "id": str(action.id),
            "agentId": str(action.agent_id),
            "providerKey": action.provider_key,
            "actionId": action.action_id,
            "enabled": action.enabled,
            "sensitivity": action.sensitivity,
            "requiresConfirmation": action.requires_confirmation,
            "createdAt": action.created_at.isoformat(),
            "updatedAt": action.updated_at.isoformat(),
        }

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
