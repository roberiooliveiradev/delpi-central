from app.application.use_cases.strategic_indicators.get_executive_summary_use_case import (
    GetStrategicIndicatorsExecutiveSummaryUseCase,
)
from app.application.use_cases.strategic_indicators.get_settings_use_case import (
    GetStrategicIndicatorsSettingsUseCase,
)
from app.application.use_cases.strategic_indicators.list_settings_audit_use_case import (
    ListStrategicIndicatorsSettingsAuditUseCase,
)
from app.application.use_cases.strategic_indicators.update_settings_use_case import (
    UpdateStrategicIndicatorsSettingsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_repository import (
    PostgresStrategicIndicatorsSettingsRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_summary_settings_repository import (
    PostgresStrategicIndicatorsSummarySettingsRepository,
)

from app.application.use_cases.strategic_indicators.add_change_request_comment_use_case import (
    AddStrategicIndicatorsChangeRequestCommentUseCase,
)
from app.application.use_cases.strategic_indicators.create_change_request_use_case import (
    CreateStrategicIndicatorsChangeRequestUseCase,
)
from app.application.use_cases.strategic_indicators.list_change_requests_use_case import (
    ListStrategicIndicatorsChangeRequestsUseCase,
)
from app.application.use_cases.strategic_indicators.submit_change_request_use_case import (
    SubmitStrategicIndicatorsChangeRequestUseCase,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_change_request_repository import (
    PostgresStrategicIndicatorsChangeRequestRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
    PostgresStrategicIndicatorsSettingsAuditRepository,
)
from app.infrastructure.providers.strategic_indicators.static_alerts_summary_provider import (
    StaticStrategicIndicatorsAlertsSummaryProvider,
)
from app.infrastructure.providers.strategic_indicators.static_department_snapshot_provider import (
    StaticStrategicIndicatorsDepartmentSnapshotProvider,
)
from app.infrastructure.providers.strategic_indicators.static_igd_snapshot_provider import (
    StaticStrategicIndicatorsIgdSnapshotProvider,
)


def build_get_strategic_indicators_executive_summary_use_case() -> GetStrategicIndicatorsExecutiveSummaryUseCase:
    settings_port = PostgresStrategicIndicatorsSummarySettingsRepository()
    department_snapshot_port = StaticStrategicIndicatorsDepartmentSnapshotProvider()
    igd_snapshot_port = StaticStrategicIndicatorsIgdSnapshotProvider()
    alerts_summary_port = StaticStrategicIndicatorsAlertsSummaryProvider()

    return GetStrategicIndicatorsExecutiveSummaryUseCase(
        settings_port=settings_port,
        department_snapshot_port=department_snapshot_port,
        igd_snapshot_port=igd_snapshot_port,
        alerts_summary_port=alerts_summary_port,
    )


def build_get_strategic_indicators_settings_use_case() -> GetStrategicIndicatorsSettingsUseCase:
    repository = PostgresStrategicIndicatorsSettingsRepository()
    return GetStrategicIndicatorsSettingsUseCase(repository)


def build_list_strategic_indicators_settings_audit_use_case() -> ListStrategicIndicatorsSettingsAuditUseCase:
    repository = PostgresStrategicIndicatorsSettingsAuditRepository()
    return ListStrategicIndicatorsSettingsAuditUseCase(repository)


def build_update_strategic_indicators_settings_use_case() -> UpdateStrategicIndicatorsSettingsUseCase:
    repository = PostgresStrategicIndicatorsSettingsRepository()
    return UpdateStrategicIndicatorsSettingsUseCase(repository)


def build_list_strategic_indicators_change_requests_use_case():
    repository = PostgresStrategicIndicatorsChangeRequestRepository()
    return ListStrategicIndicatorsChangeRequestsUseCase(repository)


def build_create_strategic_indicators_change_request_use_case():
    repository = PostgresStrategicIndicatorsChangeRequestRepository()
    return CreateStrategicIndicatorsChangeRequestUseCase(repository)


def build_add_strategic_indicators_change_request_comment_use_case():
    repository = PostgresStrategicIndicatorsChangeRequestRepository()
    return AddStrategicIndicatorsChangeRequestCommentUseCase(repository)


def build_submit_strategic_indicators_change_request_use_case():
    repository = PostgresStrategicIndicatorsChangeRequestRepository()
    return SubmitStrategicIndicatorsChangeRequestUseCase(repository)