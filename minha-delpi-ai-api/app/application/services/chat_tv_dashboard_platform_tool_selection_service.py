"""Handoff TV Dashboard → especialista VISTA (sem tool de mutação no Chat)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_host_surface_context_service import (
    ChatHostSurfaceContextService,
)
from app.domain.services.chat_tv_dashboard_handoff_service import (
    ChatTvDashboardHandoffService,
)


@dataclass(frozen=True)
class TvPlatformToolSelectionResult:
    tool_call: dict[str, Any] | None = None
    direct_answer: str | None = None
    catalog: dict[str, Any] | None = None
    has_suggested_ops: bool = False
    selection_pending: dict[str, Any] | None = None
    platform_direct_answer: bool = False


class ChatTvDashboardPlatformToolSelectionService:
    """Detecta pedido TV e devolve direct answer de handoff — zero tool calls."""

    @classmethod
    def select(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
        access_token: str | None = None,
        catalog_service: Any = None,
    ) -> TvPlatformToolSelectionResult:
        del previous_messages, access_token, catalog_service
        if not ChatHostSurfaceContextService.allows_common_chat_platform_tools(
            workspace_context,
            message=message,
        ):
            return TvPlatformToolSelectionResult()

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host = workspace.get("tvDashboardHostContext") or workspace.get("hostContext")
        host_dict = host if isinstance(host, dict) else None

        wants_tv = ChatTvDashboardHandoffService.matches(message) or (
            ChatHostSurfaceContextService.is_tv_mutation_turn(
                message,
                host_dict,
                workspace_context=workspace,
            )
        )
        if not wants_tv:
            return TvPlatformToolSelectionResult()

        return TvPlatformToolSelectionResult(
            direct_answer=ChatTvDashboardHandoffService.redirect_to_vista_message(),
            platform_direct_answer=True,
        )
