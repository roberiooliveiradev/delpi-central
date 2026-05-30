from uuid import UUID

from app.application.services.agent_specialization_service import (
    AgentSpecializationService,
)
from app.extensions.db import db
from app.infrastructure.db.models.chat_agent_model import AiChatAgentModel
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_agent_repository import (
    PostgresChatAgentRepository,
)


class ListAdminAgentSpecializationPresetsUseCase:
    def __init__(self, specialization_service: AgentSpecializationService | None = None):
        self.specialization_service = specialization_service or AgentSpecializationService()

    def execute(self) -> dict:
        return {"presets": self.specialization_service.list_presets()}


class ListAdminSpecializedAgentsUseCase:
    def __init__(
        self,
        agent_repository: PostgresChatAgentRepository | None = None,
        specialization_service: AgentSpecializationService | None = None,
    ):
        self.agent_repository = agent_repository or PostgresChatAgentRepository()
        self.specialization_service = specialization_service or AgentSpecializationService()

    def execute(self) -> dict:
        models = (
            AiChatAgentModel.query.filter(AiChatAgentModel.enabled.is_(True))
            .order_by(AiChatAgentModel.name.asc())
            .all()
        )

        items = []

        for model in models:
            agent = self.agent_repository._to_entity(model)
            metadata = agent.metadata or {}
            specialization = self.specialization_service.parse(metadata.get("specialization"))

            items.append(
                {
                    "id": str(agent.id),
                    "name": agent.name,
                    "description": agent.description,
                    "category": agent.category,
                    "visibility": agent.visibility,
                    "enabled": agent.enabled,
                    "specialization": specialization,
                    "hasSpecialization": specialization is not None,
                }
            )

        return {"items": items}


class GetAdminAgentSpecializationUseCase:
    def __init__(self, specialization_service: AgentSpecializationService | None = None):
        self.specialization_service = specialization_service or AgentSpecializationService()

    def execute(self, *, agent_id: str) -> dict:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == UUID(str(agent_id))).first()

        if not model:
            raise ValueError("agent not found")

        metadata = model.agent_metadata or {}
        specialization = self.specialization_service.parse(metadata.get("specialization"))

        return {
            "agentId": str(model.id),
            "agentName": model.name,
            "specialization": specialization,
            "enabled": specialization is not None,
        }


class SaveAdminAgentSpecializationUseCase:
    def __init__(
        self,
        specialization_service: AgentSpecializationService | None = None,
        audit_repository: PostgresAuditRepository | None = None,
    ):
        self.specialization_service = specialization_service or AgentSpecializationService()
        self.audit_repository = audit_repository

    def execute(
        self,
        *,
        agent_id: str,
        specialization_payload: dict | None,
        user_id: str,
    ) -> dict:
        model = AiChatAgentModel.query.filter(AiChatAgentModel.id == UUID(str(agent_id))).first()

        if not model:
            raise ValueError("agent not found")

        metadata = dict(model.agent_metadata or {})

        if specialization_payload is None or specialization_payload.get("enabled") is False:
            metadata.pop("specialization", None)
            saved_specialization = None
        else:
            saved_specialization = self.specialization_service.normalize_payload(
                specialization_payload,
            )
            metadata["specialization"] = saved_specialization

        model.agent_metadata = metadata
        db.session.flush()

        if self.audit_repository:
            self.audit_repository.log(
                user_id=UUID(str(user_id)),
                action="admin.agent.specialization.updated",
                context="admin",
                metadata={
                    "agent_id": str(model.id),
                    "enabled": saved_specialization is not None,
                    "domain": (saved_specialization or {}).get("domain"),
                    "preset_key": (saved_specialization or {}).get("presetKey"),
                },
            )

        return {
            "agentId": str(model.id),
            "agentName": model.name,
            "specialization": saved_specialization,
            "enabled": saved_specialization is not None,
        }
