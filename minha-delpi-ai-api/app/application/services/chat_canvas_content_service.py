from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService


@dataclass(frozen=True)
class ChatCanvasOpenPayload:
    title: str
    markdown: str
    source_message_id: str | None


@dataclass(frozen=True)
class ChatCanvasAction:
    answer: str
    open_payload: ChatCanvasOpenPayload | None


class ChatCanvasContentService:
    """Resolve pedido de lousa: confirmação + markdown da última resposta do assistente."""

    @classmethod
    def resolve(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        workspace_context: dict | None,
    ) -> ChatCanvasAction | None:
        if not ChatCanvasIntentService.is_canvas_placement_request(message):
            return None

        if not cls._canvas_enabled(workspace_context):
            return ChatCanvasAction(
                answer=(
                    "A lousa não está habilitada neste agente. "
                    "Ative a capacidade «Permitir lousa (canvas)» no builder do agente."
                ),
                open_payload=None,
            )

        source = cls._find_last_assistant_message(previous_messages)
        if not source:
            return ChatCanvasAction(
                answer=(
                    "Ainda não há uma resposta minha nesta conversa para colocar na lousa. "
                    "Faça uma pergunta primeiro e depois peça para enviar o conteúdo à lousa."
                ),
                open_payload=None,
            )

        markdown = str(source.get("content") or "").strip()
        if not markdown:
            return ChatCanvasAction(
                answer=(
                    "A última resposta do assistente está vazia. "
                    "Peça algo novo no chat e tente novamente."
                ),
                open_payload=None,
            )

        title = cls._derive_title(markdown)
        source_id = source.get("id")
        source_message_id = str(source_id) if source_id is not None else None

        return ChatCanvasAction(
            answer=(
                f"Coloquei «{title}» na lousa ao lado. "
                "Você pode editar, visualizar e salvar o conteúdo quando quiser."
            ),
            open_payload=ChatCanvasOpenPayload(
                title=title,
                markdown=markdown,
                source_message_id=source_message_id,
            ),
        )

    @classmethod
    def _canvas_enabled(cls, workspace_context: dict | None) -> bool:
        capabilities = (workspace_context or {}).get("capabilities") or {}
        canvas = capabilities.get("canvas")

        if isinstance(canvas, bool):
            return canvas

        return True

    @classmethod
    def _find_last_assistant_message(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        if not previous_messages:
            return None

        for message in reversed(previous_messages):
            role = getattr(message, "role", None) or (
                message.get("role") if isinstance(message, dict) else None
            )
            if str(role or "").lower() != "assistant":
                continue

            content = getattr(message, "content", None)
            if content is None and isinstance(message, dict):
                content = message.get("content")

            text = str(content or "").strip()
            if not text:
                continue

            message_id = getattr(message, "id", None)
            if message_id is None and isinstance(message, dict):
                message_id = message.get("id")

            return {"id": message_id, "content": text}

        return None

    @classmethod
    def _derive_title(cls, markdown: str) -> str:
        for line in markdown.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()[:80] or "Conteúdo do chat"

            plain = stripped.replace("**", "").replace("*", "").strip()
            if plain:
                return plain[:80]

        return "Conteúdo do chat"
