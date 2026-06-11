from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.domain.services.chat_runtime_intelligence_settings_service import (
    ChatRuntimeIntelligenceSettingsService,
)
from app.infrastructure.config.app_config_adapter import InfrastructureAppConfigAdapter
from app.infrastructure.config.chat_runtime_intelligence_settings_adapter import (
    InfrastructureChatRuntimeIntelligenceSettingsAdapter,
)
from app.infrastructure.content.assistant_content_adapter import (
    InfrastructureAssistantContentAdapter,
)

_CONFIGURED = False


def _configure_typo_correction_rules() -> None:
    from app.domain.services.chat_message_normalization_service import (
        ChatMessageNormalizationService,
    )
    from app.domain.services.chat_typing_correction_fuzzy_lexicon_service import (
        ChatTypingCorrectionFuzzyLexiconService,
    )
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.content.content_service import ContentService

    payload = ContentService.load_json("assistant/typing_correction_rules")
    rules = payload.get("rules")

    if isinstance(rules, list):
        ChatMessageNormalizationService.configure_static_rules(rules)

    lexicon_payload = ContentService.load_json("assistant/typing_correction_lexicon")
    ChatTypingCorrectionFuzzyLexiconService.configure(
        lexicon_payload,
        enabled=Settings.CHAT_TYPING_CORRECTION_FUZZY_ENABLED,
    )


def configure_domain_infrastructure_ports() -> None:
    """Registra adapters de conteúdo/config no domain (composition root)."""
    global _CONFIGURED

    if _CONFIGURED:
        return

    config = InfrastructureAppConfigAdapter()

    ChatAssistantContentService.configure(InfrastructureAssistantContentAdapter())
    ChatDomainConfigService.configure(config)
    ChatExternalActionDirectResponseService.configure(config)
    ChatRuntimeIntelligenceSettingsService.configure(
        InfrastructureChatRuntimeIntelligenceSettingsAdapter()
    )
    _configure_typo_correction_rules()
    _CONFIGURED = True


def configure_domain_infrastructure_ports_with_persistence() -> None:
    """Composition root completo (conteúdo + persistência) — uso em runtime da API."""
    from app.composition.persistence_composer import configure_domain_persistence_ports

    configure_domain_infrastructure_ports()
    configure_domain_persistence_ports()
