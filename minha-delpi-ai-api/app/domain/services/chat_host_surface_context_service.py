"""Contexto implícito de host embutido (ambient surface).

Padrão de mercado (VS Code Copilot / Agent Host, Notion AI, Figma):
o host declara surface + bindings; o modelo recebe isso em todo turno
sem o usuário repetir «estou no TV Dashboard».

Módulo canônico — não duplicar surface/skill/hostContext em use cases ou MFE.
"""

from __future__ import annotations

from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    TV_DASHBOARD_COPILOT_SKILL_FLAG,
    TV_DASHBOARD_SURFACE,
    ChatTvDashboardCopilotIntentService,
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
    """Contrato ambient: hostContext → skills, prompt, exclusão de text_task."""

    SURFACE_TV_DASHBOARD = TV_DASHBOARD_SURFACE

    @classmethod
    def normalize(cls, host_context: dict | None) -> dict | None:
        return ChatTvDashboardCopilotIntentService.normalize_host_context(host_context)

    @classmethod
    def surface_of(cls, host_context: dict | None) -> str | None:
        normalized = cls.normalize(host_context)
        if not normalized:
            return None
        surface = str(normalized.get("surface") or "").strip()
        return surface or None

    @classmethod
    def is_tv_dashboard(cls, host_context: dict | None) -> bool:
        return ChatTvDashboardCopilotIntentService.is_tv_surface(host_context)

    @classmethod
    def enrich_workspace(
        cls,
        workspace_context: dict | None,
        *,
        message: str | None,
        host_context: dict | None = None,
    ) -> dict:
        """Ativa capabilities do surface e grava hostContext no workspace do turno."""
        return ChatTvDashboardCopilotIntentService.enrich_workspace_skills(
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
        """Tools internas de surface no chat comum (sem agente OpenAPI).

        Espelha a exceção de ``web_search``: o embed TV declara surface e precisa
        chamar ``tv_dashboard_copilot`` sem ativar agente operacional.
        """
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        skills = workspace.get("skills") if isinstance(workspace.get("skills"), dict) else {}
        if skills.get(TV_DASHBOARD_COPILOT_SKILL_FLAG):
            return True

        host = workspace.get("tvDashboardHostContext") or workspace.get("hostContext")
        if cls.is_tv_dashboard(host if isinstance(host, dict) else None):
            return True

        return bool(message and ChatTvDashboardCopilotIntentService.matches(message))

    @classmethod
    def build_prompt_addon(cls, workspace_context: dict | None) -> str:
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host = workspace.get("tvDashboardHostContext") or workspace.get("hostContext")
        if not host and not (workspace.get("skills") or {}).get(TV_DASHBOARD_COPILOT_SKILL_FLAG):
            return ""
        return ChatTvDashboardCopilotIntentService.build_host_prompt_section(
            host if isinstance(host, dict) else None
        )

    @classmethod
    def suppresses_pure_text_task(
        cls,
        message: str | None,
        *,
        host_context: dict | None = None,
        category: str | None = None,
    ) -> bool:
        """No surface TV, imperativos de criação vão para tools — não para o especialista textual.

        O usuário já está no editor; «crie um slide» não é redação. E-mail/correção
        explícitos continuam text_task.
        """
        if ChatTvDashboardCopilotIntentService.matches(message):
            return True

        if not cls.is_tv_dashboard(host_context):
            return False

        if category and category in _LINGUISTIC_TEXT_CATEGORIES:
            return False

        # Ambient: no TV, «crie/monte/gere/adicione…» sem documento linguístico → copiloto.
        if category == "write":
            return True

        return ChatTvDashboardCopilotIntentService.matches(message)

    @classmethod
    def merge_tool_arguments(
        cls,
        tool_name: str,
        arguments: dict | None,
        workspace_context: dict | None,
    ) -> dict:
        if tool_name != "tv_dashboard_copilot":
            return dict(arguments or {})

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host = workspace.get("tvDashboardHostContext") or workspace.get("hostContext")
        return ChatTvDashboardCopilotIntentService.merge_target_into_arguments(
            arguments,
            host if isinstance(host, dict) else None,
        )

    @classmethod
    def build_platform_tool_call(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        """Seleção determinística da tool de surface (não depende do LLM)."""
        if not cls.allows_common_chat_platform_tools(
            workspace_context,
            message=message,
        ):
            return None

        call = ChatTvDashboardCopilotIntentService.build_create_slide_tool_call(message)
        if not call:
            from app.domain.services.chat_write_confirmation_service import (
                ChatWriteConfirmationService,
            )

            if ChatWriteConfirmationService.user_confirmed(message):
                call = ChatTvDashboardCopilotIntentService.build_apply_tool_call_from_history(
                    previous_messages
                )

        if not call:
            return None

        return {
            **call,
            "arguments": cls.merge_tool_arguments(
                "tv_dashboard_copilot",
                call.get("arguments") if isinstance(call.get("arguments"), dict) else {},
                workspace_context,
            ),
        }
