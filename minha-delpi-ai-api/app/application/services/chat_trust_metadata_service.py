"""Anexa sinais de confiança (Playbook 08) ao metadata do assistente."""

from __future__ import annotations

from app.domain.services.chat_trust_signals_service import ChatTrustSignalsService


class ChatTrustMetadataService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        answer: str,
        tool_calls: list | None,
        sources: list | None,
        workspace_context: dict | None = None,
        direct_response: bool = False,
    ) -> None:
        signals = ChatTrustSignalsService.build(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            sources=sources,
            workspace_context=workspace_context,
            direct_response=direct_response,
        )

        if signals:
            metadata["trustSignals"] = signals
