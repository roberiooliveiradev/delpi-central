from app.application.use_cases.admin_chat_platform_settings_use_cases import (
    GetAdminChatLearningPipelineSettingsUseCase,
    SaveAdminChatLearningPipelineSettingsUseCase,
)
from app.infrastructure.config.chat_admin_settings_bundles import CHAT_LEARNING_PIPELINE_BUNDLE


class _FakeBundleService:
    def __init__(self):
        self.spec = CHAT_LEARNING_PIPELINE_BUNDLE
        self._payload = {
            field.json_key: field.default() for field in CHAT_LEARNING_PIPELINE_BUNDLE.fields
        }

    def to_dict(self) -> dict:
        return {
            **self._payload,
            "source": "defaults",
            "defaults": dict(self._payload),
        }

    def save(self, payload: dict) -> dict:
        self._payload.update(
            {key: value for key, value in payload.items() if key in self._payload}
        )
        return self.to_dict()


def test_get_learning_pipeline_settings_exposes_fine_tune_mode(monkeypatch):
    class _Gateway:
        def supports_local_deploy(self) -> bool:
            return False

    monkeypatch.setattr(
        "app.composition.fine_tuning_model_composer.make_fine_tuning_model_gateway",
        lambda: _Gateway(),
    )

    result = GetAdminChatLearningPipelineSettingsUseCase(_FakeBundleService()).execute()

    assert result["supportsLocalFineTuneDeploy"] is False
    assert result["fineTuningMode"] == "export_only"
    assert "learningFineTuningEnabled" in result


def test_get_learning_pipeline_settings_ollama_mode(monkeypatch):
    class _Gateway:
        def supports_local_deploy(self) -> bool:
            return True

    monkeypatch.setattr(
        "app.composition.fine_tuning_model_composer.make_fine_tuning_model_gateway",
        lambda: _Gateway(),
    )

    result = GetAdminChatLearningPipelineSettingsUseCase(_FakeBundleService()).execute()

    assert result["supportsLocalFineTuneDeploy"] is True
    assert result["fineTuningMode"] == "ollama"


def test_save_learning_pipeline_settings_strips_capability_echo(monkeypatch):
    class _Gateway:
        def supports_local_deploy(self) -> bool:
            return False

    monkeypatch.setattr(
        "app.composition.fine_tuning_model_composer.make_fine_tuning_model_gateway",
        lambda: _Gateway(),
    )

    service = _FakeBundleService()
    result = SaveAdminChatLearningPipelineSettingsUseCase(service).execute(
        {
            "learningFineTuningEnabled": False,
            "supportsLocalFineTuneDeploy": True,
            "fineTuningMode": "ollama",
        }
    )

    assert service._payload["learningFineTuningEnabled"] is False
    assert result["supportsLocalFineTuneDeploy"] is False
    assert result["fineTuningMode"] == "export_only"
