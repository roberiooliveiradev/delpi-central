from uuid import UUID

from app.application.services.agent_specialization_service import (
    AgentSpecializationService,
)
from app.domain.services.chat_project_settings_service import ChatProjectSettingsService
from app.domain.services.chat_project_sources_intent_service import (
    ChatProjectSourcesIntentService,
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
        message: str | None = None,
    ) -> dict:
        project = workspace_context.get("project") or {}
        project_id = project.get("id") or session.project_id

        skills = workspace_context.get("skills") or {}
        include_global = bool(skills.get("companyKnowledge", True))

        if message and ChatProjectSourcesIntentService.should_restrict_to_project_sources(
            message
        ):
            include_global = False

        project_meta = project if isinstance(project, dict) else {}
        share_context = bool(
            project_meta.get("shareConversationContext")
        ) or ChatProjectSettingsService.share_conversation_context_enabled(
            project_meta.get("metadata")
        )
        peer_session_ids = [
            str(item)
            for item in (workspace_context.get("projectPeerSessionIds") or [])
            if item
        ]

        filters = {
            "user_id": str(user_id),
            "project_id": str(project_id) if project_id else None,
            "agent_id": workspace_context.get("agentId"),
            "include_global": include_global,
        }

        if share_context and peer_session_ids:
            filters["shared_session_ids"] = [
                str(session.id),
                *peer_session_ids,
            ]
        else:
            filters["session_id"] = str(session.id)

        cleaned_attachment_ids = [
            str(item)
            for item in (attachment_ids or [])
            if item
        ]

        if cleaned_attachment_ids:
            filters["attachment_ids"] = cleaned_attachment_ids

        if project_id:
            filters["scope_priority"] = "project_source"

        specialization = workspace_context.get("specialization")

        return self.specialization_service.build_rag_filters(specialization, filters)
