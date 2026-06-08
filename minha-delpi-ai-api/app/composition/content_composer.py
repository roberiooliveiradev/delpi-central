from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
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

    config = InfrastructureAppConfigAdapter()

    ChatAssistantContentService.configure(InfrastructureAssistantContentAdapter())
    ChatDomainConfigService.configure(config)
    ChatExternalActionDirectResponseService.configure(config)
    _CONFIGURED = True


def configure_domain_infrastructure_ports_with_persistence() -> None:
    """Composition root completo (conteúdo + persistência) — uso em runtime da API."""
    from app.composition.persistence_composer import configure_domain_persistence_ports

    configure_domain_infrastructure_ports()
    configure_domain_persistence_ports()
