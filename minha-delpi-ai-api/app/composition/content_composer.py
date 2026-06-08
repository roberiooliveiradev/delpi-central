from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.infrastructure.config.app_config_adapter import InfrastructureAppConfigAdapter
from app.infrastructure.content.assistant_content_adapter import (
    InfrastructureAssistantContentAdapter,
)

_CONFIGURED = False


def configure_domain_infrastructure_ports() -> None:
    """Registra adapters de conteúdo/config no domain (composition root)."""
    global _CONFIGURED

    if _CONFIGURED:
        return

    ChatAssistantContentService.configure(InfrastructureAssistantContentAdapter())
    ChatExternalActionDirectResponseService.configure(InfrastructureAppConfigAdapter())
    _CONFIGURED = True
