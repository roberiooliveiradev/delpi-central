"""Expõe confirmação de ação sensível no metadata (Playbook 08) para chips no MFE."""

from __future__ import annotations

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatActionConfirmationMetadataService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        tool_calls: list | None,
        user_message: str,
    ) -> None:
        pending = cls._extract_pending(tool_calls, user_message=user_message)

        if pending:
            metadata["actionConfirmation"] = pending

    @classmethod
    def _extract_pending(
        cls,
        tool_calls: list | None,
        *,
        user_message: str,
    ) -> dict | None:
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            if call.get("name") != "execute_external_action":
                continue

            call_meta = call.get("metadata") or {}

            if call_meta.get("blockReason") != "confirmation_required":
                continue

            arguments = call.get("arguments") or {}
            action_id = str(
                arguments.get("actionId")
                or arguments.get("action_id")
                or call_meta.get("actionId")
                or ""
            ).strip()

            if not action_id:
                continue

            original = str(user_message or "").strip()
            confirm_query = "confirmo"

            if original:
                confirm_query = f"confirmo. {original}"

            labels = ExternalActionResponseContentService.get_mapping(
                "security",
                "confirmationChips",
            )

            return {
                "actionId": action_id,
                "path": str(call_meta.get("path") or ""),
                "sensitivity": str(call_meta.get("sensitivity") or ""),
                "summary": str(call_meta.get("summary") or call_meta.get("path") or action_id),
                "confirmLabel": labels.get("confirm", "Confirmar"),
                "cancelLabel": labels.get("cancel", "Cancelar"),
                "confirmQuery": confirm_query,
                "cancelQuery": labels.get("cancelQuery", "cancelar esta ação"),
            }

        return None
