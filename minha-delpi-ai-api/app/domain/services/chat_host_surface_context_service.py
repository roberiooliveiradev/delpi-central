"""Contexto implícito de host embutido (ambient surface).

O host declara surface + bindings; o modelo recebe isso em todo turno
sem o usuário repetir «estou no TV Dashboard».

Módulo canônico — não duplicar surface/hostContext em use cases ou MFE.
"""

from __future__ import annotations

from app.domain.services.chat_tv_dashboard_handoff_service import (
    TV_DASHBOARD_SURFACE,
    ChatTvDashboardHandoffService,
)

# Categorias de redação explícita que permanecem text_task mesmo no surface TV.
_LINGUISTIC_TEXT_CATEGORIES = frozenset(
    {
        "correct",
        "review",
        "rewrite",
        "translate",
        "summarize",
        "simplify",
        "email",
        "letter",
        "memorandum",
        "minutes",
        "announcement",
        "documentation",
        "explain",
        "eli5",
        "tone_adjust",
        "message",
        "document",
        "report",
        "conversation_transform",
        "adapt_audience",
    }
)


class ChatHostSurfaceContextService:
    """Contrato ambient: hostContext → prompt, exclusão de text_task, handoff TV."""

    SURFACE_TV_DASHBOARD = TV_DASHBOARD_SURFACE

    @classmethod
    def normalize_host_context(cls, host_context: dict | None) -> dict | None:
        return ChatTvDashboardHandoffService.normalize_host_context(host_context)

    @classmethod
    def host_from_workspace(cls, workspace_context: dict | None) -> dict | None:
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host = workspace.get("tvDashboardHostContext") or workspace.get("hostContext")
        return host if isinstance(host, dict) else None

    @classmethod
    def is_tv_dashboard(cls, host_context: dict | None) -> bool:
        return ChatTvDashboardHandoffService.is_tv_surface(host_context)

    @classmethod
    def enrich_workspace(
        cls,
        workspace_context: dict | None,
        *,
        message: str | None,
        host_context: dict | None = None,
    ) -> dict:
        """Grava hostContext no workspace do turno (handoff-only)."""
        return ChatTvDashboardHandoffService.enrich_workspace(
            workspace_context,
            message=message,
            host_context=host_context,
        )

    @classmethod
    def allows_common_chat_platform_tools(
        cls,
        workspace_context: dict | None,
        *,
        message: str | None = None,
    ) -> bool:
        """Pedidos TV no chat comum ativam handoff VISTA (direct answer), não tool."""
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        if cls.is_tv_dashboard(cls.host_from_workspace(workspace)):
            return True
        return bool(message and ChatTvDashboardHandoffService.matches(message))

    @classmethod
    def build_prompt_addon(
        cls,
        workspace_context: dict | None,
        *,
        catalog: dict | None = None,
    ) -> str:
        del catalog
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host = cls.host_from_workspace(workspace)
        if not host:
            return ""
        return ChatTvDashboardHandoffService.build_host_prompt_section(host)

    @classmethod
    def suppresses_pure_text_task(
        cls,
        message: str | None,
        *,
        host_context: dict | None = None,
        category: str | None = None,
    ) -> bool:
        """No surface TV, imperativos de criação vão para handoff — não especialista textual."""
        if ChatTvDashboardHandoffService.matches(message):
            return True

        if not cls.is_tv_dashboard(host_context):
            return False

        if category and category in _LINGUISTIC_TEXT_CATEGORIES:
            return False

        if category == "write":
            return True

        if ChatTvDashboardHandoffService.is_tv_mutation_turn(message, host_context):
            return True

        return ChatTvDashboardHandoffService.matches(message)

    @classmethod
    def is_tv_mutation_turn(
        cls,
        message: str | None,
        host_context: dict | None = None,
        *,
        has_suggested_ops: bool = False,
        workspace_context: dict | None = None,
    ) -> bool:
        host = host_context
        if host is None and workspace_context is not None:
            host = cls.host_from_workspace(workspace_context)
        return ChatTvDashboardHandoffService.is_tv_mutation_turn(
            message,
            host,
            has_suggested_ops=has_suggested_ops,
        )

    @classmethod
    def merge_tool_arguments(
        cls,
        tool_name: str,
        arguments: dict | None,
        workspace_context: dict | None,
    ) -> dict:
        del tool_name, workspace_context
        return dict(arguments or {})

    @classmethod
    def build_platform_tool_call(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        """Tool TV removida — nunca mintar platform tool call."""
        del message, workspace_context, previous_messages
        return None
