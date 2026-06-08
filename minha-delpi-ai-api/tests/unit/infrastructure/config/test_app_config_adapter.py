from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.infrastructure.config.app_config_adapter import InfrastructureAppConfigAdapter


def test_adapter_exposes_direct_response_flags():
    ChatExternalActionDirectResponseService.configure(InfrastructureAppConfigAdapter())

    assert isinstance(ChatExternalActionDirectResponseService.is_enabled(), bool)
