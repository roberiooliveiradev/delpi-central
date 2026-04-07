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

from app.application.use_cases.strategic_indicators.get_department_details_use_case import (
    GetStrategicIndicatorsDepartmentDetailsUseCase,
)
from app.application.use_cases.strategic_indicators.get_departments_use_case import (
    GetStrategicIndicatorsDepartmentsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_departments_catalog_repository import (
    PostgresStrategicIndicatorsDepartmentsCatalogRepository,
)
from app.infrastructure.providers.strategic_indicators.static_department_details_snapshot_provider import (
    StaticStrategicIndicatorsDepartmentDetailsSnapshotProvider,
)
from app.infrastructure.providers.strategic_indicators.static_departments_snapshot_provider import (
    StaticStrategicIndicatorsDepartmentsSnapshotProvider,
)

from app.application.use_cases.strategic_indicators.get_indicators_use_case import (
    GetStrategicIndicatorsUseCase,
)
from app.infrastructure.providers.strategic_indicators.engineering_indicators_snapshot_provider import (
    EngineeringIndicatorsSnapshotProvider,
)

from app.composition.lmp_composer import (
    build_list_lmp_dashboard_use_case,
)
from app.composition.transforma_mais_composer import (
    transforma_mais_get_process_summary_composer,
)


from app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)
from app.infrastructure.providers.strategic_indicators.production_indicators_snapshot_provider import (
    ProductionIndicatorsSnapshotProvider,
)

from app.composition.production_composer import (
    build_get_depreciation_pct_use_case,
    build_get_direct_labor_cost_pct_use_case,
    build_get_on_time_delivery_pct_use_case,
    build_get_overall_equipment_effectiveness_pct_use_case,
    build_get_production_cost_pct_use_case,
)


from app.composition.commercial_composer import (
    build_get_branch_rol_target_pct_use_case,
    build_get_head_office_rol_target_pct_use_case,
    build_get_new_clients_average_use_case,
    build_get_new_clients_rol_pct_use_case,
    build_get_sales_conversion_rate_use_case,
)
from app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)
from app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
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


def build_get_strategic_indicators_departments_use_case() -> GetStrategicIndicatorsDepartmentsUseCase:
    catalog_port = PostgresStrategicIndicatorsDepartmentsCatalogRepository()
    snapshot_port = StaticStrategicIndicatorsDepartmentsSnapshotProvider()

    return GetStrategicIndicatorsDepartmentsUseCase(
        catalog_port=catalog_port,
        snapshot_port=snapshot_port,
    )


def build_get_strategic_indicators_department_details_use_case() -> GetStrategicIndicatorsDepartmentDetailsUseCase:
    catalog_port = PostgresStrategicIndicatorsDepartmentsCatalogRepository()
    details_snapshot_port = StaticStrategicIndicatorsDepartmentDetailsSnapshotProvider()

    return GetStrategicIndicatorsDepartmentDetailsUseCase(
        catalog_port=catalog_port,
        details_snapshot_port=details_snapshot_port,
    )


def build_get_strategic_indicators_use_case() -> GetStrategicIndicatorsUseCase:
    engineering_snapshot_port = EngineeringIndicatorsSnapshotProvider(
        lmp_dashboard_use_case=build_list_lmp_dashboard_use_case(),
        transforma_mais_summary_use_case=transforma_mais_get_process_summary_composer(),
    )

    production_snapshot_port = ProductionIndicatorsSnapshotProvider(
        direct_labor_use_case=build_get_direct_labor_cost_pct_use_case(),
        production_cost_use_case=build_get_production_cost_pct_use_case(),
        depreciation_use_case=build_get_depreciation_pct_use_case(),
        oee_use_case=build_get_overall_equipment_effectiveness_pct_use_case(),
        otd_use_case=build_get_on_time_delivery_pct_use_case(),
    )

    commercial_snapshot_port = CommercialIndicatorsSnapshotProvider(
        head_office_rol_target_use_case=build_get_head_office_rol_target_pct_use_case(),
        branch_rol_target_use_case=build_get_branch_rol_target_pct_use_case(),
        sales_conversion_rate_use_case=build_get_sales_conversion_rate_use_case(),
        new_clients_average_use_case=build_get_new_clients_average_use_case(),
        new_clients_rol_pct_use_case=build_get_new_clients_rol_pct_use_case(),
    )

    return GetStrategicIndicatorsUseCase(
        engineering_snapshot_port=engineering_snapshot_port,
        production_snapshot_port=production_snapshot_port,
        commercial_snapshot_port=commercial_snapshot_port,
    )