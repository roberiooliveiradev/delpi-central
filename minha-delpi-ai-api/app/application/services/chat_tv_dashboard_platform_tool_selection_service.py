"""Seleção determinística da tool tv_dashboard_copilot via catálogo/suggest-ops BFF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_tv_dashboard_catalog_service import (
    ChatTvDashboardCatalogService,
)
from app.domain.services.chat_host_surface_context_service import (
    ChatHostSurfaceContextService,
)
from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    ChatTvDashboardCopilotIntentService,
)
from app.domain.services.chat_write_confirmation_service import (
    ChatWriteConfirmationService,
)


@dataclass(frozen=True)
class TvPlatformToolSelectionResult:
    tool_call: dict[str, Any] | None = None
    direct_answer: str | None = None
    catalog: dict[str, Any] | None = None
    has_suggested_ops: bool = False


class ChatTvDashboardPlatformToolSelectionService:
    """Application: confirmação do histórico OU suggest-ops do BFF — zero ops embutidas."""

    @classmethod
    def select(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
        access_token: str | None = None,
        catalog_service: ChatTvDashboardCatalogService | None = None,
    ) -> TvPlatformToolSelectionResult:
        if not ChatHostSurfaceContextService.allows_common_chat_platform_tools(
            workspace_context,
            message=message,
        ):
            return TvPlatformToolSelectionResult()

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host = workspace.get("tvDashboardHostContext") or workspace.get("hostContext")
        host_dict = host if isinstance(host, dict) else None

        if ChatWriteConfirmationService.user_confirmed(message):
            apply_call = ChatTvDashboardCopilotIntentService.build_apply_tool_call_from_history(
                previous_messages
            )
            if apply_call:
                merged = {
                    **apply_call,
                    "arguments": ChatHostSurfaceContextService.merge_tool_arguments(
                        "tv_dashboard_copilot",
                        apply_call.get("arguments")
                        if isinstance(apply_call.get("arguments"), dict)
                        else {},
                        workspace,
                    ),
                }
                return TvPlatformToolSelectionResult(
                    tool_call=merged,
                    has_suggested_ops=True,
                )

            if ChatTvDashboardCopilotIntentService.last_tool_call_in_history(
                previous_messages
            ):
                # Houve prévia no histórico, mas ela falhou / já foi aplicada:
                # responder de forma determinística em vez de deixar o LLM inventar.
                return TvPlatformToolSelectionResult(
                    direct_answer=(
                        ChatTvDashboardCopilotIntentService.no_pending_preview_message()
                        or None
                    ),
                )

        # Só consulta o BFF em turno de mutação / pedido TV — não em small talk no surface.
        needs_bff = ChatHostSurfaceContextService.is_tv_mutation_turn(
            message,
            host_dict,
            workspace_context=workspace,
        ) or ChatTvDashboardCopilotIntentService.matches(message)
        if not needs_bff:
            return TvPlatformToolSelectionResult()

        catalog_client = catalog_service or ChatTvDashboardCatalogService()
        catalog = catalog_client.get_catalog(access_token)
        if catalog is None:
            # AP1: sem fallback de ops — mensagem genérica do intent JSON.
            answer = ChatTvDashboardCopilotIntentService.catalog_unavailable_message()
            return TvPlatformToolSelectionResult(
                direct_answer=answer or None,
            )

        suggestion = catalog_client.suggest_ops(
            message=str(message or ""),
            host_context=host_dict,
            access_token=access_token,
        )
        if not isinstance(suggestion, dict):
            # BFF indisponível no suggest — mesma política do catálogo: resposta direta.
            answer = ChatTvDashboardCopilotIntentService.catalog_unavailable_message()
            return TvPlatformToolSelectionResult(
                catalog=catalog,
                direct_answer=answer or None,
            )

        ops = suggestion.get("ops")
        if not isinstance(ops, list) or not ops:
            # Match incompleto / clarificação: reason do BFF vira directAnswer (sem LLM inventar UI).
            bff_reason = str(suggestion.get("reason") or "").strip()
            answer = (
                bff_reason
                or ChatTvDashboardCopilotIntentService.catalog_unavailable_message()
            )
            return TvPlatformToolSelectionResult(
                catalog=catalog,
                direct_answer=answer or None,
            )

        reason = str(
            suggestion.get("reason")
            or ChatTvDashboardCopilotIntentService.selection_reason()
        ).strip()
        call = {
            "name": "tv_dashboard_copilot",
            "arguments": {
                "mode": "preview",
                "ops": list(ops),
            },
            "reason": reason,
        }
        merged = {
            **call,
            "arguments": ChatHostSurfaceContextService.merge_tool_arguments(
                "tv_dashboard_copilot",
                call["arguments"],
                workspace,
            ),
        }
        return TvPlatformToolSelectionResult(
            tool_call=merged,
            catalog=catalog,
            has_suggested_ops=True,
        )
