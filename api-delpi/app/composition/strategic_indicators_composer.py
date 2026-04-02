from app.application.use_cases.strategic_indicators.get_settings_use_case import (
    GetStrategicIndicatorsSettingsUseCase,
)
from app.application.use_cases.strategic_indicators.update_settings_use_case import (
    UpdateStrategicIndicatorsSettingsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_repository import (
    PostgresStrategicIndicatorsSettingsRepository,
)


def build_get_strategic_indicators_settings_use_case() -> GetStrategicIndicatorsSettingsUseCase:
    repository = PostgresStrategicIndicatorsSettingsRepository()
    return GetStrategicIndicatorsSettingsUseCase(repository)


def build_update_strategic_indicators_settings_use_case() -> UpdateStrategicIndicatorsSettingsUseCase:
    repository = PostgresStrategicIndicatorsSettingsRepository()
    return UpdateStrategicIndicatorsSettingsUseCase(repository)