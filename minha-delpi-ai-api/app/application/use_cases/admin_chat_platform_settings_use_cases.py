from app.application.services.chat_admin_settings_bundle_service import (
    ChatAdminSettingsBundleService,
)
from app.infrastructure.config.chat_admin_settings_bundles import (
    CHAT_LEARNING_PIPELINE_BUNDLE,
    CHAT_RESPONSE_MODE_BUNDLE,
    CHAT_VISION_BUNDLE,
)


class _BundleGetUseCase:
    def __init__(self, service: ChatAdminSettingsBundleService):
        self.service = service

    def execute(self) -> dict:
        return self.service.to_dict()


class _BundleSaveUseCase:
    def __init__(self, service: ChatAdminSettingsBundleService):
        self.service = service

    def execute(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")

        return self.service.save(payload)


class GetAdminChatResponseModeSettingsUseCase(_BundleGetUseCase):
    pass


class SaveAdminChatResponseModeSettingsUseCase(_BundleSaveUseCase):
    pass


class GetAdminChatVisionSettingsUseCase(_BundleGetUseCase):
    pass


class SaveAdminChatVisionSettingsUseCase(_BundleSaveUseCase):
    pass


class GetAdminChatLearningPipelineSettingsUseCase(_BundleGetUseCase):
    def execute(self) -> dict:
        payload = dict(self.service.to_dict())
        from app.composition.fine_tuning_model_composer import make_fine_tuning_model_gateway

        gateway = make_fine_tuning_model_gateway()
        supports_local = bool(gateway.supports_local_deploy())
        payload["supportsLocalFineTuneDeploy"] = supports_local
        payload["fineTuningMode"] = "ollama" if supports_local else "export_only"
        return payload


class SaveAdminChatLearningPipelineSettingsUseCase(_BundleSaveUseCase):
    def execute(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")

        # Capability fields are read-only; strip if client echoes them.
        sanitized = {
            key: value
            for key, value in payload.items()
            if key not in {"supportsLocalFineTuneDeploy", "fineTuningMode", "source", "defaults"}
        }
        result = dict(self.service.save(sanitized))
        from app.composition.fine_tuning_model_composer import make_fine_tuning_model_gateway

        gateway = make_fine_tuning_model_gateway()
        supports_local = bool(gateway.supports_local_deploy())
        result["supportsLocalFineTuneDeploy"] = supports_local
        result["fineTuningMode"] = "ollama" if supports_local else "export_only"
        return result


def make_response_mode_settings_service() -> ChatAdminSettingsBundleService:
    from app.composition.repository_composer import make_admin_runtime_settings_repository

    return ChatAdminSettingsBundleService(
        CHAT_RESPONSE_MODE_BUNDLE,
        make_admin_runtime_settings_repository(),
    )


def make_vision_settings_service() -> ChatAdminSettingsBundleService:
    from app.composition.repository_composer import make_admin_runtime_settings_repository

    return ChatAdminSettingsBundleService(
        CHAT_VISION_BUNDLE,
        make_admin_runtime_settings_repository(),
    )


def make_learning_pipeline_settings_service() -> ChatAdminSettingsBundleService:
    from app.composition.repository_composer import make_admin_runtime_settings_repository

    return ChatAdminSettingsBundleService(
        CHAT_LEARNING_PIPELINE_BUNDLE,
        make_admin_runtime_settings_repository(),
    )
