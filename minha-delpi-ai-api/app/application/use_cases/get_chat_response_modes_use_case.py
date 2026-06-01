from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.infrastructure.config.settings import Settings


class GetChatResponseModesUseCase:
    def execute(self) -> dict:
        return {
            "enabled": ChatResponseModeService.is_enabled(),
            "defaultMode": "normal",
            "provider": Settings.LLM_PROVIDER,
            "modes": ChatResponseModeService.list_modes(),
        }
