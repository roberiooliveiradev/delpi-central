from uuid import UUID

from app.application.services.agent_specialization_service import (
    AgentSpecializationService,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort


class ListAdminAgentSpecializationPresetsUseCase:
    def __init__(self, specialization_service: AgentSpecializationService | None = None):
        self.specialization_service = specialization_service or AgentSpecializationService()

    def execute(self) -> dict:
        return {"presets": self.specialization_service.list_presets()}


class ListAdminSpecializedAgentsUseCase:
    def __init__(
        self,
        agent_repository: ChatAgentRepositoryPort,
        specialization_service: AgentSpecializationService | None = None,
    ):
        self.agent_repository = agent_repository
        self.specialization_service = specialization_service or AgentSpecializationService()

    def execute(self) -> dict:
        items = []

        for agent in self.agent_repository.list_enabled_ordered():
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
    def __init__(
        self,
        agent_repository: ChatAgentRepositoryPort,
        specialization_service: AgentSpecializationService | None = None,
    ):
        self.agent_repository = agent_repository
        self.specialization_service = specialization_service or AgentSpecializationService()

    def execute(self, *, agent_id: str) -> dict:
        try:
            parsed_agent_id = UUID(str(agent_id))
        except ValueError as exc:
            raise ValueError("agent not found") from exc

        agent = self.agent_repository.get_by_id(parsed_agent_id)

        if not agent:
            raise ValueError("agent not found")

        metadata = agent.metadata or {}
        specialization = self.specialization_service.parse(metadata.get("specialization"))

        return {
            "agentId": str(agent.id),
            "agentName": agent.name,
            "specialization": specialization,
            "enabled": specialization is not None,
        }


class SaveAdminAgentSpecializationUseCase:
    def __init__(
        self,
        agent_repository: ChatAgentRepositoryPort,
        specialization_service: AgentSpecializationService | None = None,
        audit_repository: AuditRepositoryPort | None = None,
    ):
        self.agent_repository = agent_repository
        self.specialization_service = specialization_service or AgentSpecializationService()
        self.audit_repository = audit_repository

    def execute(
        self,
        *,
        agent_id: str,
        specialization_payload: dict | None,
        user_id: str,
    ) -> dict:
        try:
            parsed_agent_id = UUID(str(agent_id))
        except ValueError as exc:
            raise ValueError("agent not found") from exc

        agent = self.agent_repository.get_by_id(parsed_agent_id)

        if not agent:
            raise ValueError("agent not found")

        metadata = dict(agent.metadata or {})

        if specialization_payload is None or specialization_payload.get("enabled") is False:
            metadata.pop("specialization", None)
            saved_specialization = None
        else:
            saved_specialization = self.specialization_service.normalize_payload(
                specialization_payload,
            )
            metadata["specialization"] = saved_specialization

        updated = self.agent_repository.update_metadata(parsed_agent_id, metadata)

        if not updated:
            raise ValueError("agent not found")

        if self.audit_repository:
            self.audit_repository.log(
                user_id=UUID(str(user_id)),
                action="admin.agent.specialization.updated",
                context="admin",
                metadata={
                    "agent_id": str(updated.id),
                    "enabled": saved_specialization is not None,
                    "domain": (saved_specialization or {}).get("domain"),
                    "preset_key": (saved_specialization or {}).get("presetKey"),
                },
            )

        return {
            "agentId": str(updated.id),
            "agentName": updated.name,
            "specialization": saved_specialization,
            "enabled": saved_specialization is not None,
        }
