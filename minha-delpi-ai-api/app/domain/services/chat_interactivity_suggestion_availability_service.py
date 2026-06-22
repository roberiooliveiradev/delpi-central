"""Disponibilidade canônica de chips de interatividade — o que exibir no chat."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_interactivity_content_service import (
    ChatInteractivityContentService,
)


class ChatInteractivitySuggestionAvailabilityService:
    @classmethod
    def resolve_disabled_reason(
        cls,
        label: str,
        *,
        workspace_context: dict | None,
    ) -> str | None:
        normalized_label = str(label or "").strip()

        if not normalized_label:
            return None

        capabilities = (workspace_context or {}).get("capabilities") or {}
        operational_labels = ChatInteractivityContentService.label_set(
            "operationalAgentRequiredLabels",
        )
        sql_labels = ChatInteractivityContentService.label_set("sqlAgentRequiredLabels")

        if normalized_label == "Colocar na lousa" and capabilities.get("canvas") is False:
            return ChatInteractivityContentService.disabled_reason(
                "canvasDisabled",
                default="A lousa não está habilitada neste agente.",
            )

        if normalized_label in operational_labels:
            if not (workspace_context or {}).get("userActivatedAgent") and not (
                workspace_context or {}
            ).get("actionsEnabled"):
                return ChatInteractivityContentService.disabled_reason(
                    "operationalAgentRequired",
                    default=(
                        "Ative um agente com consultas operacionais para usar esta ação."
                    ),
                )

        if normalized_label in sql_labels and not (workspace_context or {}).get(
            "actionsEnabled",
        ):
            return ChatInteractivityContentService.disabled_reason(
                "sqlAgentRequired",
                default=(
                    "Ative um agente com actions SQL/schema para consultar ou executar "
                    "no banco."
                ),
            )

        return None

    @classmethod
    def omit_unavailable(
        cls,
        items: list[dict[str, Any]],
        *,
        workspace_context: dict | None,
    ) -> list[dict[str, Any]]:
        if not ChatInteractivityContentService.hide_unavailable_suggestions():
            return items

        visible: list[dict[str, Any]] = []

        for item in items:
            label = str(item.get("label") or "").strip()
            disabled = str(item.get("disabledReason") or "").strip() or cls.resolve_disabled_reason(
                label,
                workspace_context=workspace_context,
            )

            if disabled:
                continue

            visible.append(item)

        return visible
