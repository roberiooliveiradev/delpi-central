from datetime import datetime, timedelta, timezone
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
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel


class PostgresChatAgentRepository(ChatAgentRepositoryPort):
    def list_accessible(
        self,
        user_id: UUID,
        *,
        include_disabled: bool = False,
    ) -> list[tuple[ChatAgent, str]]:
        shared_agent_ids = (
            db.session.query(AiChatAgentShareModel.agent_id)
            .filter(AiChatAgentShareModel.target_user_id == user_id)
        )

        query = AiChatAgentModel.query

        if not include_disabled:
            query = query.filter(AiChatAgentModel.enabled.is_(True))

        models = (
            query
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
        can_manage_official_agents: bool = False,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model:
            return False

        return self._can_edit(
            model,
            user_id,
            can_manage_official_agents=can_manage_official_agents,
        )

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
        owner_user_id: UUID | None,
        key: str,
        name: str,
        description: str | None,
        system_prompt: str | None,
        visibility: str,
        category: str | None,
        icon: str | None,
        response_style: str | None,
        metadata: dict | None,
        *,
        max_tool_calls: int | None = None,
        requires_confirmation_for_write: bool | None = None,
        enabled: bool | None = None,
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
            enabled=True if enabled is None else enabled,
            max_tool_calls=5 if max_tool_calls is None else max_tool_calls,
            requires_confirmation_for_write=(
                True
                if requires_confirmation_for_write is None
                else requires_confirmation_for_write
            ),
        )

        db.session.add(model)
        db.session.flush()

        return self._to_entity(model)

    def duplicate(
        self,
        agent_id: UUID,
        user_id: UUID,
        *,
        can_manage_official_agents: bool = False,
        copy_actions: bool = False,
    ) -> ChatAgent | None:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(
            model,
            user_id,
            can_manage_official_agents=can_manage_official_agents,
        ):
            return None

        duplicate_name = model.name.strip()

        if not duplicate_name.endswith("(cópia)"):
            duplicate_name = f"{duplicate_name} (cópia)"[:120]

        created = self.create(
            owner_user_id=user_id,
            key=self._generate_duplicate_key(model.key),
            name=duplicate_name,
            description=model.description,
            system_prompt=model.system_prompt,
            visibility="private",
            category=model.category,
            icon=model.icon,
            response_style=model.response_style,
            metadata=model.agent_metadata,
            max_tool_calls=model.max_tool_calls,
            requires_confirmation_for_write=model.requires_confirmation_for_write,
            enabled=model.enabled,
        )

        if copy_actions:
            self._copy_action_configuration(agent_id, created.id)

        return created

    def get_usage_stats(
        self,
        agent_id: UUID,
        user_id: UUID,
        *,
        hours: int = 168,
    ) -> dict | None:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_access(model, user_id):
            return None

        safe_hours = max(1, min(int(hours), 24 * 90))
        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)
        agent_key = model.key

        sessions_in_window = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.agent_key == agent_key)
            .filter(AiChatSessionModel.created_at >= since)
            .count()
        )

        messages_in_window = (
            db.session.query(AiChatMessageModel)
            .join(AiChatSessionModel, AiChatMessageModel.session_id == AiChatSessionModel.id)
            .filter(AiChatSessionModel.agent_key == agent_key)
            .filter(AiChatMessageModel.created_at >= since)
            .count()
        )

        total_sessions = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.agent_key == agent_key)
            .count()
        )

        action_providers = (
            AiChatAgentActionProviderModel.query
            .filter(AiChatAgentActionProviderModel.agent_id == agent_id)
            .count()
        )

        shares_count = (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == agent_id)
            .count()
            if model.owner_user_id == user_id
            else 0
        )

        return {
            "agentKey": agent_key,
            "windowHours": safe_hours,
            "sessionsInWindow": sessions_in_window,
            "messagesInWindow": messages_in_window,
            "totalSessions": total_sessions,
            "actionProvidersCount": action_providers,
            "sharesCount": shares_count,
        }

    def _copy_action_configuration(self, source_agent_id: UUID, target_agent_id: UUID) -> None:
        provider_rows = (
            AiChatAgentActionProviderModel.query
            .filter(AiChatAgentActionProviderModel.agent_id == source_agent_id)
            .all()
        )

        for row in provider_rows:
            db.session.add(
                AiChatAgentActionProviderModel(
                    agent_id=target_agent_id,
                    provider_key=row.provider_key,
                    enabled=row.enabled,
                    allow_read=row.allow_read,
                    allow_write=row.allow_write,
                    allow_admin=row.allow_admin,
                    requires_confirmation_for_write=row.requires_confirmation_for_write,
                )
            )

        action_rows = (
            AiChatAgentActionModel.query
            .filter(AiChatAgentActionModel.agent_id == source_agent_id)
            .all()
        )

        for row in action_rows:
            db.session.add(
                AiChatAgentActionModel(
                    agent_id=target_agent_id,
                    provider_key=row.provider_key,
                    action_id=row.action_id,
                    enabled=row.enabled,
                    sensitivity=row.sensitivity,
                    requires_confirmation=row.requires_confirmation,
                )
            )

        db.session.flush()

    def _generate_duplicate_key(self, base_key: str) -> str:
        normalized = (base_key or "agente").strip() or "agente"
        candidate = f"{normalized}-copia"[:80]
        suffix = 2

        while self._key_exists(candidate):
            suffix_label = f"-{suffix}"
            candidate = f"{normalized[: 80 - len(suffix_label)]}{suffix_label}"
            suffix += 1

        return candidate

    def _key_exists(self, key: str) -> bool:
        return (
            AiChatAgentModel.query.filter(AiChatAgentModel.key == key).first() is not None
        )

    def update(
        self,
        agent_id: UUID,
        user_id: UUID,
        can_manage_official_agents: bool = False,
        **fields,
    ) -> ChatAgent | None:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(
            model,
            user_id,
            can_manage_official_agents=can_manage_official_agents,
        ):
            return None

        for key, value in fields.items():
            if value is not None and hasattr(model, key):
                setattr(model, key, value)

        db.session.flush()

        return self._to_entity(model)

    def delete(
        self,
        agent_id: UUID,
        user_id: UUID,
        can_manage_official_agents: bool = False,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model:
            return False

        is_owner = model.owner_user_id == user_id
        is_official_agent = model.visibility == "system" or model.owner_user_id is None

        if not is_owner and not (can_manage_official_agents and is_official_agent):
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

    def list_shares(self, agent_id: UUID, user_id: UUID) -> list[dict]:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or model.owner_user_id != user_id:
            return []

        rows = (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == agent_id)
            .order_by(AiChatAgentShareModel.created_at.asc())
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

    def revoke_share(self, agent_id: UUID, user_id: UUID, target_user_id: UUID) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or model.owner_user_id != user_id:
            return False

        deleted = (
            AiChatAgentShareModel.query
            .filter(AiChatAgentShareModel.agent_id == agent_id)
            .filter(AiChatAgentShareModel.target_user_id == target_user_id)
            .delete()
        )

        db.session.flush()

        return bool(deleted)

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
                db.func.count(db.distinct(ExternalActionModel.id)).label("action_count"),
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
        can_manage_official_agents: bool = False,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(
            model,
            user_id,
            can_manage_official_agents=can_manage_official_agents,
        ):
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
            sensitivity_allowed = ["read", "sql", "export"]

            if link.allow_write:
                sensitivity_allowed.append("write")
                sensitivity_allowed.append("destructive")

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
            .order_by(AiChatAgentActionModel.action_id.asc())
            .all()
        )

        enabled_overrides = {
            row.action_id
            for row in explicit_rows
            if row.enabled
        }

        disabled_overrides = {
            row.action_id
            for row in explicit_rows
            if not row.enabled
        }

        allowed_action_ids = set(provider_action_ids)
        allowed_action_ids.update(enabled_overrides)
        allowed_action_ids.difference_update(disabled_overrides)

        return sorted(allowed_action_ids)

    def upsert_action(
        self,
        agent_id: UUID,
        user_id: UUID,
        provider_key: str,
        action_id: str,
        sensitivity: str,
        requires_confirmation: bool,
        enabled: bool,
        can_manage_official_agents: bool = False,
    ) -> bool:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == agent_id).first()

        if not model or not self._can_edit(
            model,
            user_id,
            can_manage_official_agents=can_manage_official_agents,
        ):
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

    def _safe_isoformat(self, value) -> str | None:
        return value.isoformat() if value else None

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
            "createdAt": self._safe_isoformat(link.created_at),
            "updatedAt": self._safe_isoformat(link.updated_at),
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
            "createdAt": self._safe_isoformat(action.created_at),
            "updatedAt": self._safe_isoformat(action.updated_at),
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

    def _can_edit(
        self,
        model: AiChatAgentModel,
        user_id: UUID,
        can_manage_official_agents: bool = False,
    ) -> bool:
        if can_manage_official_agents and (
            model.visibility == "system" or model.owner_user_id is None
        ):
            return True

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
