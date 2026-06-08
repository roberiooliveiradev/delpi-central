"""Ativação explícita de agente no chat — ponto único de verdade."""

from __future__ import annotations

from uuid import UUID


class ChatWorkspaceAgentActivationService:
    """
    O chat comum não herda agente de plataforma nem default de projeto.

    Agente só entra no workspace quando o usuário escolheu:
    - agent_id persistido na sessão (modo agent), ou
    - agentId na requisição (composer / rota de agente).
    """

    @staticmethod
    def resolve_explicit_agent_id(
        *,
        session_agent_id: UUID | None,
        request_agent_id: UUID | None,
    ) -> UUID | None:
        return session_agent_id or request_agent_id

    @staticmethod
    def is_user_activated(
        *,
        session_agent_id: UUID | None,
        request_agent_id: UUID | None,
        actions_enabled: bool,
    ) -> bool:
        return bool(
            ChatWorkspaceAgentActivationService.resolve_explicit_agent_id(
                session_agent_id=session_agent_id,
                request_agent_id=request_agent_id,
            )
            and actions_enabled
        )

    @staticmethod
    def operational_tools_enabled(workspace_context: dict | None) -> bool:
        """Consultas OpenAPI / loop agentic só com agente ativo e actions habilitadas."""
        ctx = workspace_context or {}
        return bool(ctx.get("userActivatedAgent") and ctx.get("actionsEnabled"))

    @staticmethod
    def normalize_chat_mode(value: str | None) -> str | None:
        normalized = str(value or "").strip().lower()

        if normalized in {"common", "agent"}:
            return normalized

        return None

    @staticmethod
    def resolve_chat_mode_for_request(
        *,
        chat_mode: str | None,
        request_agent_id: str | None,
        session_agent_id: UUID | None = None,
    ) -> str:
        normalized = ChatWorkspaceAgentActivationService.normalize_chat_mode(chat_mode)

        if normalized:
            return normalized

        if str(request_agent_id or "").strip():
            return "agent"

        if session_agent_id:
            return "agent"

        return "common"

    @staticmethod
    def prepare_session_for_turn(
        *,
        session,
        request_agent_id: str | None,
        chat_mode: str | None,
        request_project_id: str | None = None,
        sync_project_binding: bool = False,
        update_session_agent_id,
        update_session_project_id=None,
    ) -> None:
        """Aplica modo explícito do turno antes de montar workspace (limpa agente legado no chat comum)."""
        mode = ChatWorkspaceAgentActivationService.resolve_chat_mode_for_request(
            chat_mode=chat_mode,
            request_agent_id=request_agent_id,
            session_agent_id=session.agent_id,
        )

        ChatWorkspaceAgentActivationService.sync_session_agent_binding(
            session=session,
            request_agent_id=request_agent_id,
            chat_mode=mode,
            update_session_agent_id=update_session_agent_id,
        )

        if sync_project_binding and update_session_project_id is not None:
            ChatWorkspaceAgentActivationService.sync_session_project_binding(
                session=session,
                request_project_id=request_project_id,
                update_session_project_id=update_session_project_id,
            )

    @staticmethod
    def sync_session_agent_binding(
        *,
        session,
        request_agent_id: str | None,
        chat_mode: str | None,
        update_session_agent_id,
    ) -> None:
        """
        Persiste ou remove agent_id conforme escolha explícita do usuário no turno.
        Evita sessões legadas com agente implícito no chat comum.
        """
        mode = ChatWorkspaceAgentActivationService.normalize_chat_mode(chat_mode)
        parsed_request_agent_id = ChatWorkspaceAgentActivationService._parse_uuid(
            request_agent_id
        )

        if mode == "common":
            if session.agent_id:
                update_session_agent_id(
                    session_id=session.id,
                    user_id=session.user_id,
                    agent_id=None,
                )
                object.__setattr__(session, "agent_id", None)
            return

        if parsed_request_agent_id and session.agent_id != parsed_request_agent_id:
            update_session_agent_id(
                session_id=session.id,
                user_id=session.user_id,
                agent_id=parsed_request_agent_id,
            )
            object.__setattr__(session, "agent_id", parsed_request_agent_id)

    @staticmethod
    def sync_session_project_binding(
        *,
        session,
        request_project_id: str | None,
        update_session_project_id,
    ) -> None:
        """Persiste project_id enviado pelo composer (permite combinar com agente no turno)."""
        parsed_request_project_id = ChatWorkspaceAgentActivationService._parse_uuid(
            request_project_id
        )

        if session.project_id == parsed_request_project_id:
            return

        update_session_project_id(
            session_id=session.id,
            user_id=session.user_id,
            project_id=parsed_request_project_id,
        )
        object.__setattr__(session, "project_id", parsed_request_project_id)

    @staticmethod
    def _parse_uuid(value: str | None) -> UUID | None:
        if not value:
            return None

        normalized = str(value).strip()

        if not normalized:
            return None

        try:
            return UUID(normalized)
        except ValueError:
            return None
