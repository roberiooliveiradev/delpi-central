from app.application.services.chat_platform_runtime_access import response_modes_enabled
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.infrastructure.config.llm_text_config import resolve_llm_provider_name


class GetChatResponseModesUseCase:
    def execute(self) -> dict:
        return {
            "enabled": response_modes_enabled(),
            "defaultMode": "normal",
            "provider": resolve_llm_provider_name(),
            "modes": ChatResponseModeService.list_modes(),
        }
