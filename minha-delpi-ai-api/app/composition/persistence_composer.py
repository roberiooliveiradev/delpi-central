from __future__ import annotations

from app.domain.services.chat_feedback_issue_service import ChatFeedbackIssueService
from app.domain.services.chat_project_conversation_context_service import (
    ChatProjectConversationContextService,
)
from app.domain.services.chat_quality_adoption_metrics_service import (
    ChatQualityAdoptionMetricsService,
)
from app.domain.services.chat_runtime_intelligence_settings_service import (
    ChatRuntimeIntelligenceSettingsService,
)
from app.domain.services.chat_quality_action_plans_access_service import (
    ChatQualityActionPlansAccessService,
)
from app.domain.skills.chat_skill_registry import ChatSkillRegistry
from app.infrastructure.persistence.postgres_chat_adoption_metrics_repository import (
    PostgresChatAdoptionMetricsRepository,
)
from app.infrastructure.persistence.postgres_chat_project_peer_context_repository import (
    PostgresChatProjectPeerContextRepository,
)
from app.infrastructure.persistence.postgres_chat_quality_issue_repository import (
    PostgresChatQualityIssueRepository,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.infrastructure.config.app_config_adapter import InfrastructureAppConfigAdapter
from app.infrastructure.config.chat_runtime_intelligence_settings_adapter import (
    InfrastructureChatRuntimeIntelligenceSettingsAdapter,
)
from app.infrastructure.persistence.postgres_admin_runtime_settings_repository import (
    PostgresAdminRuntimeSettingsRepository,
)
from app.infrastructure.persistence.postgres_chat_skill_repository import (
    PostgresChatSkillRepository,
)

_PERSISTENCE_CONFIGURED = False


def configure_domain_persistence_ports() -> None:
    """Registra repositórios de persistência usados pelo domain."""
    global _PERSISTENCE_CONFIGURED

    if _PERSISTENCE_CONFIGURED:
        return

    from app.infrastructure.persistence.postgres_external_action_repository import (
        PostgresExternalActionRepository,
    )

    ChatFeedbackIssueService.configure(PostgresChatQualityIssueRepository())
    ChatSkillRegistry.configure(
        skill_repository=PostgresChatSkillRepository(),
        external_action_repository=PostgresExternalActionRepository(),
    )
    ChatQualityActionPlansAccessService.configure_external_action_repository(
        PostgresExternalActionRepository(),
    )
    ChatProjectConversationContextService.configure(
        PostgresChatProjectPeerContextRepository()
    )
    ChatQualityAdoptionMetricsService.configure(PostgresChatAdoptionMetricsRepository())
    admin_runtime_repository = PostgresAdminRuntimeSettingsRepository()
    ChatDomainConfigService.configure(
        InfrastructureAppConfigAdapter(admin_runtime_repository)
    )
    ChatRuntimeIntelligenceSettingsService.configure(
        InfrastructureChatRuntimeIntelligenceSettingsAdapter(admin_runtime_repository)
    )
    from app.application.services.chat_capabilities_service import (
        configure_external_action_repository_loader,
    )
    from app.composition.repository_composer import make_external_action_repository

    configure_external_action_repository_loader(make_external_action_repository)
    _PERSISTENCE_CONFIGURED = True
