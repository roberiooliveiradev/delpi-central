from unittest.mock import Mock, patch

from app.domain.services.chat_fine_tuning_deploy_resolver_service import (
    ChatFineTuningDeployResolverService,
)
from app.infrastructure.config.settings import Settings


def test_resolve_returns_deployed_model_when_active(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_FINE_TUNING_ENABLED", True, raising=False)

    repo = Mock()
    repo.get_active_deployed_chat_model.return_value = "delpi-ft-d1-r2"

    with patch(
        "app.domain.services.chat_domain_config_service.ChatDomainConfigService.llm_provider",
        return_value="ollama",
    ):
        with patch(
            "app.domain.services.chat_domain_config_service.ChatDomainConfigService.learning_pipeline_flag",
            return_value=True,
        ):
            with patch(
                "app.composition.repository_composer.make_fine_tuning_repository",
                return_value=repo,
            ):
                resolved = ChatFineTuningDeployResolverService.resolve("qwen2.5:3b")

    assert resolved == "delpi-ft-d1-r2"


def test_resolve_skips_deploy_with_external_llm_provider(monkeypatch):
    with patch(
        "app.domain.services.chat_domain_config_service.ChatDomainConfigService.llm_provider",
        return_value="openai_compatible",
    ):
        resolved = ChatFineTuningDeployResolverService.resolve("qwen2.5:3b")

    assert resolved == "qwen2.5:3b"


def test_resolve_falls_back_to_base_model(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_FINE_TUNING_ENABLED", False, raising=False)

    with patch(
        "app.domain.services.chat_domain_config_service.ChatDomainConfigService.llm_provider",
        return_value="ollama",
    ):
        with patch(
            "app.domain.services.chat_domain_config_service.ChatDomainConfigService.learning_pipeline_flag",
            return_value=False,
        ):
            resolved = ChatFineTuningDeployResolverService.resolve("qwen2.5:3b")

    assert resolved == "qwen2.5:3b"
