import ast
from pathlib import Path
from unittest.mock import Mock

from app.application.services.chat_capabilities_service import (
    ChatCapabilitiesService,
    configure_external_action_repository_loader,
)
from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.use_cases.admin_llm_cost_table_use_cases import (
    GetAdminLlmCostTableUseCase,
)
from app.application.use_cases.admin_security_use_cases import GetAdminSecuritySummaryUseCase
from app.application.use_cases.get_admin_metrics_summary_use_case import (
    GetAdminMetricsSummaryUseCase,
)
from app.application.use_cases.get_admin_feedback_summary_use_case import (
    GetAdminFeedbackSummaryUseCase,
)
from app.application.use_cases.get_admin_quality_unified_summary_use_case import (
    GetAdminQualityUnifiedSummaryUseCase,
)
from app.application.use_cases.get_admin_tools_health_use_case import GetAdminToolsHealthUseCase
from app.domain.ports.admin_metrics_repository_port import AdminMetricsRepositoryPort
from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.domain.ports.admin_system_check_repository_port import AdminSystemCheckRepositoryPort
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.infrastructure.config.settings import Settings

_ADMIN_METRICS_RUNTIME_EXTERNAL_MODULES = [
    "app/application/services/chat_capabilities_service.py",
    "app/application/services/chat_intelligence_settings_service.py",
    "app/application/services/llm_cost_estimator_service.py",
    "app/application/services/chat_assistant_catalog_service.py",
    "app/application/services/assistant_capabilities_catalog_generator.py",
    "app/application/use_cases/get_admin_quality_unified_summary_use_case.py",
    "app/application/use_cases/admin_security_use_cases.py",
    "app/application/use_cases/admin_llm_cost_table_use_cases.py",
    "app/application/use_cases/get_admin_tools_health_use_case.py",
    "app/application/use_cases/admin_chat_intelligence_use_cases.py",
]


def test_admin_metrics_runtime_external_modules_have_no_postgres_imports():
    for rel_path in _ADMIN_METRICS_RUNTIME_EXTERNAL_MODULES:
        tree = ast.parse(Path(rel_path).read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "postgres" in node.module:
                raise AssertionError(f"Postgres import in {rel_path}: {node.module}")


def test_get_admin_metrics_summary_delegates_to_port():
    repository = Mock(spec=AdminMetricsRepositoryPort)
    repository.get_summary.return_value = {"sessions": 1}

    payload = GetAdminMetricsSummaryUseCase(repository).execute(hours=24)

    repository.get_summary.assert_called_once_with(hours=24)
    assert payload["sessions"] == 1


def test_get_admin_security_summary_delegates_to_audit_port():
    repository = Mock()
    repository.get_security_summary.return_value = {"blockedCount": 2}

    payload = GetAdminSecuritySummaryUseCase(repository).execute(hours=24)

    repository.get_security_summary.assert_called_once_with(hours=24)
    assert payload["blockedCount"] == 2


def test_get_admin_llm_cost_table_delegates_to_runtime_settings_port():
    repository = Mock(spec=AdminRuntimeSettingsRepositoryPort)
    repository.get_llm_cost_table.return_value = [
        {
            "provider": "ollama",
            "model": "qwen2.5:3b",
            "promptCostPer1k": 0.0,
            "completionCostPer1k": 0.0,
            "currency": "BRL",
        }
    ]

    payload = GetAdminLlmCostTableUseCase(repository).execute()

    repository.get_llm_cost_table.assert_called_once()
    assert payload["source"] == "database"
    assert payload["entries"]


def test_get_admin_tools_health_uses_external_action_port():
    system_repository = Mock(spec=AdminSystemCheckRepositoryPort)
    external_repository = Mock(spec=ExternalActionRepositoryPort)
    system_repository.check.return_value = {
        "database": {"status": "ok"},
        "pgvector": {"status": "ok"},
        "tables": {"status": "ok", "missing": []},
        "llm": {"status": "ok", "provider": "ollama", "chatModel": {"name": "qwen2.5:3b"}},
    }
    external_repository.list_providers.return_value = [{"key": "api-delpi", "enabled": True}]
    external_repository.list_actions.return_value = [{"actionId": "stock"}]

    payload = GetAdminToolsHealthUseCase(
        system_check_repository=system_repository,
        external_action_repository=external_repository,
    ).execute()

    external_repository.list_providers.assert_called_once()
    external_repository.list_actions.assert_called_once()
    assert payload["status"] in {"ok", "warning", "error"}


def test_chat_capabilities_load_action_catalog_uses_configured_loader():
    repository = Mock(spec=ExternalActionRepositoryPort)
    repository.list_actions.return_value = [
        {"actionId": "stock_lookup"},
        {"actionId": "other"},
    ]

    configure_external_action_repository_loader(lambda: repository)
    catalog = ChatCapabilitiesService.load_action_catalog_for_agent(["stock_lookup"])

    repository.list_actions.assert_called_once()
    assert len(catalog) == 1
    assert catalog[0]["actionId"] == "stock_lookup"


def test_chat_intelligence_settings_service_sync_writes_env_to_runtime_port(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_ENABLED", False)

    repository = Mock(spec=AdminRuntimeSettingsRepositoryPort)
    service = ChatIntelligenceSettingsService(repository)

    service.sync_from_environment()

    repository.save_chat_intelligence_settings.assert_called_once()
    payload = repository.save_chat_intelligence_settings.call_args.args[0]
    assert payload["webSearchEnabled"] is False
    assert service.resolve().web_search_enabled is False


def test_get_admin_quality_unified_summary_delegates_to_injected_use_cases(monkeypatch):
    from app.domain.services.chat_quality_adoption_metrics_service import (
        ChatQualityAdoptionMetricsService,
    )

    monkeypatch.setattr(
        ChatQualityAdoptionMetricsService,
        "snapshot",
        classmethod(lambda cls, *, hours: {"windowHours": hours}),
    )

    metrics_repository = Mock(spec=AdminMetricsRepositoryPort)
    audit_repository = Mock()
    feedback_use_case = Mock(spec=GetAdminFeedbackSummaryUseCase)
    metrics_repository.get_summary.return_value = {"sessions": 3}
    audit_repository.get_security_summary.return_value = {"blockedCount": 0}
    feedback_use_case.execute.return_value = {"totalFeedback": 1}

    payload = GetAdminQualityUnifiedSummaryUseCase(
        feedback_use_case=feedback_use_case,
        metrics_use_case=GetAdminMetricsSummaryUseCase(metrics_repository),
        security_use_case=GetAdminSecuritySummaryUseCase(audit_repository),
    ).execute(hours=24)

    feedback_use_case.execute.assert_called_once()
    metrics_repository.get_summary.assert_called_once()
    audit_repository.get_security_summary.assert_called_once()
    assert "feedback" in payload
    assert payload["windowHours"] == 24
