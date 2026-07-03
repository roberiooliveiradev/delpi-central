from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.infrastructure.llm.llm_request_context import get_active_config, get_active_llm_provider


class ChatLlmMetadataService:
    @staticmethod
    def resolve_generation_config(request: SendChatMessageRequest):
        return ChatResponseModeService.resolve(request.response_mode)

    @staticmethod
    def build_assistant_llm_fields() -> dict[str, object]:
        active = get_active_config()

        return {
            "provider": get_active_llm_provider(),
            "model": active.model,
            "responseMode": active.response_mode,
            "llm": {
                "maxTokens": active.max_tokens,
                "numCtx": active.num_ctx,
                "temperature": active.temperature,
            },
        }

    @staticmethod
    def user_message_response_mode(request: SendChatMessageRequest) -> dict[str, str]:
        mode = ChatResponseModeService.normalize(request.response_mode)

        return {"responseMode": mode}

    @staticmethod
    def user_message_typing_correction(request: SendChatMessageRequest) -> dict[str, object]:
        if not request.typing_correction:
            return {}

        return {"typingCorrection": request.typing_correction}
