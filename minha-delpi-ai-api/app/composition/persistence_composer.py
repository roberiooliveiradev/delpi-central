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
    ChatProjectConversationContextService.configure(
        PostgresChatProjectPeerContextRepository()
    )
    ChatQualityAdoptionMetricsService.configure(PostgresChatAdoptionMetricsRepository())
    ChatRuntimeIntelligenceSettingsService.configure(
        InfrastructureChatRuntimeIntelligenceSettingsAdapter(
            PostgresAdminRuntimeSettingsRepository()
        )
    )
    _PERSISTENCE_CONFIGURED = True
