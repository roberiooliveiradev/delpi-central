"""Pipeline de metadata de apresentação — Playbook 22 (as-delivered)."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationMetadataPipelineService:
    """Delega ao caminho schema-first / as-delivered (único ativo)."""

    @classmethod
    def build(
        cls,
        *,
        action: dict,
        sanitized_data,
        resolved_path: str,
        request_parameters: dict,
        presenter: ExternalActionResultPresenter,
        extract_response_meta: Callable[[Any], dict | None],
    ) -> dict:
        from app.application.services.chat_presentation_api_delivered_metadata_service import (
            ChatPresentationApiDeliveredMetadataService,
        )

        return ChatPresentationApiDeliveredMetadataService.build(
            action=action,
            sanitized_data=sanitized_data,
            resolved_path=resolved_path,
            request_parameters=request_parameters,
            presenter=presenter,
            extract_response_meta=extract_response_meta,
        )
