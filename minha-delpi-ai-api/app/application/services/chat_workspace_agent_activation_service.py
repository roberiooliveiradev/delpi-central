"""Ativação explícita de agente no chat — ponto único de verdade."""

from __future__ import annotations

from uuid import UUID


class ChatWorkspaceAgentActivationService:
    """
    O chat comum não herda agente de plataforma nem default de projeto.

    Agente só entra no workspace quando o usuário escolheu:
    - agent_id persistido na sessão, ou
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
