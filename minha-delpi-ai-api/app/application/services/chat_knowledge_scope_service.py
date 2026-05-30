from uuid import UUID

from app.application.services.agent_specialization_service import (
    AgentSpecializationService,
)


class ChatKnowledgeScopeService:
    def __init__(self, specialization_service: AgentSpecializationService | None = None):
        self.specialization_service = specialization_service or AgentSpecializationService()

    def build_filters(
        self,
        *,
        user_id: UUID,
        session,
        workspace_context: dict,
        attachment_ids: list[str] | None = None,
    ) -> dict:
        project = workspace_context.get("project") or {}
        project_id = project.get("id") or session.project_id

        skills = workspace_context.get("skills") or {}
        include_global = bool(skills.get("companyKnowledge", True))

        filters = {
            "user_id": str(user_id),
            "session_id": str(session.id),
            "project_id": str(project_id) if project_id else None,
            "agent_id": workspace_context.get("agentId"),
            "include_global": include_global,
        }

        cleaned_attachment_ids = [
            str(item)
            for item in (attachment_ids or [])
            if item
        ]

        if cleaned_attachment_ids:
            filters["attachment_ids"] = cleaned_attachment_ids

        specialization = workspace_context.get("specialization")

        return self.specialization_service.build_rag_filters(specialization, filters)
