from __future__ import annotations


def _repository():
    from app.composition.repository_composer import make_admin_runtime_settings_repository

    return make_admin_runtime_settings_repository()


def response_modes_enabled() -> bool:
    from app.domain.services.chat_domain_config_service import ChatDomainConfigService

    return ChatDomainConfigService.chat_response_modes_enabled()


def vision_settings() -> dict:
    from app.infrastructure.config.chat_admin_settings_runtime_reader import (
        read_vision_settings,
    )

    return read_vision_settings(_repository())


def learning_pipeline_settings() -> dict:
    from app.infrastructure.config.chat_admin_settings_runtime_reader import (
        read_learning_pipeline_settings,
    )

    return read_learning_pipeline_settings(_repository())


def learning_flag(key: str) -> bool:
    from app.domain.services.chat_domain_config_service import ChatDomainConfigService

    return ChatDomainConfigService.learning_pipeline_flag(key)
