from uuid import UUID


class ChatKnowledgeScopeService:
    def build_filters(self, *, user_id: UUID, session, workspace_context: dict) -> dict:
        project = workspace_context.get("project") or {}
        project_id = project.get("id") or session.project_id

        return {
            "user_id": str(user_id),
            "session_id": str(session.id),
            "project_id": str(project_id) if project_id else None,
            "agent_key": workspace_context.get("agentKey"),
            "include_global": True,
        }
