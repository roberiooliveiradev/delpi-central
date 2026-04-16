from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from app.application.use_cases.strategic_indicators.get_executive_summary_real_use_case import (
    GetStrategicIndicatorsExecutiveSummaryRealUseCase,
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
from app.application.use_cases.strategic_indicators.get_indicators_use_case import (
    GetStrategicIndicatorsUseCase,
)
from app.application.use_cases.strategic_indicators.get_departments_real_use_case import (
    GetStrategicIndicatorsDepartmentsRealUseCase,
)
from app.application.use_cases.strategic_indicators.get_department_details_real_use_case import (
    GetStrategicIndicatorsDepartmentDetailsRealUseCase,
)
from app.application.use_cases.strategic_indicators.get_alerts_real_use_case import (
    GetStrategicIndicatorsAlertsRealUseCase,
)
from app.application.use_cases.strategic_indicators.get_trends_real_use_case import (
    GetStrategicIndicatorsTrendsRealUseCase,
)
from app.application.use_cases.strategic_indicators.list_indicator_goals_use_case import (
    ListStrategicIndicatorsIndicatorGoalsUseCase,
)
from app.application.use_cases.strategic_indicators.list_indicator_goal_history_use_case import (
    ListStrategicIndicatorsIndicatorGoalHistoryUseCase,
)
from app.application.use_cases.strategic_indicators.create_indicator_goal_use_case import (
    CreateStrategicIndicatorsIndicatorGoalUseCase,
)
from app.application.use_cases.strategic_indicators.update_indicator_goal_use_case import (
    UpdateStrategicIndicatorsIndicatorGoalUseCase,
)
from app.application.use_cases.strategic_indicators.activate_indicator_goal_use_case import (
    ActivateStrategicIndicatorsIndicatorGoalUseCase,
)
from app.application.use_cases.strategic_indicators.deactivate_indicator_goal_use_case import (
    DeactivateStrategicIndicatorsIndicatorGoalUseCase,
)
from app.application.use_cases.strategic_indicators.list_admin_departments_use_case import (
    ListStrategicIndicatorsAdminDepartmentsUseCase,
)
from app.application.use_cases.strategic_indicators.create_admin_department_use_case import (
    CreateStrategicIndicatorsAdminDepartmentUseCase,
)
from app.application.use_cases.strategic_indicators.update_admin_department_use_case import (
    UpdateStrategicIndicatorsAdminDepartmentUseCase,
)
from app.application.use_cases.strategic_indicators.deactivate_admin_department_use_case import (
    DeactivateStrategicIndicatorsAdminDepartmentUseCase,
)
from app.application.use_cases.strategic_indicators.delete_admin_department_use_case import (
    DeleteStrategicIndicatorsAdminDepartmentUseCase,
)
from app.application.use_cases.strategic_indicators.list_admin_department_indicators_use_case import (
    ListStrategicIndicatorsAdminDepartmentIndicatorsUseCase,
)
from app.application.use_cases.strategic_indicators.create_admin_department_indicator_use_case import (
    CreateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from app.application.use_cases.strategic_indicators.update_admin_department_indicator_use_case import (
    UpdateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from app.application.use_cases.strategic_indicators.deactivate_admin_department_indicator_use_case import (
    DeactivateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from app.application.use_cases.strategic_indicators.delete_admin_department_indicator_use_case import (
    DeleteStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from app.application.use_cases.strategic_indicators.bulk_create_indicator_goals_use_case import (
    BulkCreateStrategicIndicatorsIndicatorGoalsUseCase,
)
from app.application.use_cases.strategic_indicators.duplicate_indicator_goals_year_use_case import (
    DuplicateStrategicIndicatorsIndicatorGoalsYearUseCase,
)
from app.application.use_cases.strategic_indicators.fill_missing_indicator_goals_use_case import (
    FillMissingStrategicIndicatorsIndicatorGoalsUseCase,
)
from app.application.use_cases.strategic_indicators.list_goal_years_overview_use_case import (
    ListStrategicIndicatorsGoalYearsOverviewUseCase,
)

from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)

from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_repository import (
    PostgresStrategicIndicatorsSettingsRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_change_request_repository import (
    PostgresStrategicIndicatorsChangeRequestRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
    PostgresStrategicIndicatorsSettingsAuditRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_catalog_repository import (
    PostgresStrategicIndicatorsCatalogRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_resolved_indicators_catalog_repository import (
    PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_departments_repository import (
    PostgresStrategicIndicatorsAdminDepartmentsRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_department_indicators_repository import (
    PostgresStrategicIndicatorsDepartmentIndicatorsRepository,
)

from app.infrastructure.providers.strategic_indicators.calculated_alerts_summary_provider import (
    CalculatedStrategicIndicatorsAlertsSummaryProvider,
)
from app.infrastructure.providers.strategic_indicators.real_indicator_measurements_provider import (
    RealStrategicIndicatorsMeasurementsProvider,
)
from app.infrastructure.providers.strategic_indicators.engineering_indicators_snapshot_provider import (
    EngineeringIndicatorsSnapshotProvider,
)
from app.infrastructure.providers.strategic_indicators.production_indicators_snapshot_provider import (
    ProductionIndicatorsSnapshotProvider,
)
from app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
)
from app.infrastructure.providers.strategic_indicators.quality_indicators_snapshot_provider import (
    QualityIndicatorsSnapshotProvider,
)

from app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
)

from app.application.use_cases.strategic_indicators.activate_admin_department_use_case import (
    ActivateStrategicIndicatorsAdminDepartmentUseCase,
)

from app.infrastructure.providers.strategic_indicators.supplies_indicators_snapshot_provider import (
    SuppliesIndicatorsSnapshotProvider,
)

from app.application.use_cases.strategic_indicators.activate_admin_department_indicator_use_case import (
    ActivateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)

from app.composition.commercial_composer import (
    build_commercial_metrics_snapshot_service,
)
from app.composition.production_composer import (
    build_production_metrics_snapshot_service,
)
from app.composition.lmp_composer import (
    build_list_lmp_dashboard_use_case,
)
from app.composition.transforma_mais_composer import (
    transforma_mais_get_process_summary_composer,
)
from app.composition.audit_5s_composer import (
    audit_5s_get_summary_composer,
)
from app.composition.kaizen_composer import (
    kaizen_get_summary_composer,
)
from app.composition.ppm_composer import (
    build_get_ppm_summary_use_case,
)
from app.composition.hr_composer import (
    build_get_hr_indicators_snapshot_port,
)
from app.composition.financial_composer import (
    build_get_financial_indicators_snapshot_port,
)

from app.composition.supplies_composer import (
    build_get_cpv_use_case,
    build_get_inventory_turnover_use_case,
    build_get_otd_use_case,
    build_get_stock_value_use_case,
)

def build_get_engineering_indicators_snapshot_port():
    return EngineeringIndicatorsSnapshotProvider(
        engineering_metrics_snapshot_service=EngineeringMetricsSnapshotService(
            lmp_dashboard_use_case=build_list_lmp_dashboard_use_case(),
            transforma_mais_summary_use_case=transforma_mais_get_process_summary_composer(),
        ),
    )


def build_get_production_indicators_snapshot_port():
    return ProductionIndicatorsSnapshotProvider(
        production_metrics_snapshot_service=build_production_metrics_snapshot_service(),
    )


def build_get_commercial_indicators_snapshot_port():
    return CommercialIndicatorsSnapshotProvider(
        commercial_metrics_snapshot_service=build_commercial_metrics_snapshot_service(),
    )


def build_get_quality_indicators_snapshot_port():
    return QualityIndicatorsSnapshotProvider(
        internal_ppm_use_case=build_get_ppm_summary_use_case(),
        external_ppm_use_case=build_get_ppm_summary_use_case(),
        kaizen_summary_use_case=kaizen_get_summary_composer(),
        audit_5s_summary_use_case=audit_5s_get_summary_composer(),
    )


def build_real_indicator_measurements_provider():
    return RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=build_get_engineering_indicators_snapshot_port(),
        production_snapshot_port=build_get_production_indicators_snapshot_port(),
        commercial_snapshot_port=build_get_commercial_indicators_snapshot_port(),
        quality_snapshot_port=build_get_quality_indicators_snapshot_port(),
        hr_snapshot_port=build_get_hr_indicators_snapshot_port(),
        financial_snapshot_port=build_get_financial_indicators_snapshot_port(),
        supplies_snapshot_port=build_get_supplies_indicators_snapshot_port(),
    )


def build_strategic_indicators_snapshot_service() -> StrategicIndicatorsSnapshotService:
    structural_catalog_repository = PostgresStrategicIndicatorsCatalogRepository()
    resolved_catalog_repository = PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository()

    return StrategicIndicatorsSnapshotService(
        departments_catalog_repository=structural_catalog_repository,
        resolved_indicators_catalog_repository=resolved_catalog_repository,
        measurements_port=build_real_indicator_measurements_provider(),
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_executive_summary_use_case():
    return GetStrategicIndicatorsExecutiveSummaryRealUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
        alerts_summary_port=CalculatedStrategicIndicatorsAlertsSummaryProvider(),
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_settings_use_case():
    repository = PostgresStrategicIndicatorsSettingsRepository()
    return GetStrategicIndicatorsSettingsUseCase(repository)


def build_list_strategic_indicators_settings_audit_use_case():
    repository = PostgresStrategicIndicatorsSettingsAuditRepository()
    return ListStrategicIndicatorsSettingsAuditUseCase(repository)


def build_update_strategic_indicators_settings_use_case():
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


def build_get_strategic_indicators_departments_use_case():
    return GetStrategicIndicatorsDepartmentsRealUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_department_details_use_case():
    return GetStrategicIndicatorsDepartmentDetailsRealUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_use_case():
    return GetStrategicIndicatorsUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
    )


def build_get_strategic_indicators_alerts_use_case():
    return GetStrategicIndicatorsAlertsRealUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
        alerts_summary_port=CalculatedStrategicIndicatorsAlertsSummaryProvider(),
    )


def build_get_strategic_indicators_trends_use_case():
    return GetStrategicIndicatorsTrendsRealUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
    )


def build_list_strategic_indicators_indicator_goals_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return ListStrategicIndicatorsIndicatorGoalsUseCase(repository)


def build_list_strategic_indicators_indicator_goal_history_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return ListStrategicIndicatorsIndicatorGoalHistoryUseCase(repository)


def build_create_strategic_indicators_indicator_goal_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return CreateStrategicIndicatorsIndicatorGoalUseCase(repository)


def build_update_strategic_indicators_indicator_goal_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return UpdateStrategicIndicatorsIndicatorGoalUseCase(repository)


def build_activate_strategic_indicators_indicator_goal_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return ActivateStrategicIndicatorsIndicatorGoalUseCase(repository)


def build_deactivate_strategic_indicators_indicator_goal_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return DeactivateStrategicIndicatorsIndicatorGoalUseCase(repository)


def build_list_strategic_indicators_admin_departments_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return ListStrategicIndicatorsAdminDepartmentsUseCase(repository)


def build_create_strategic_indicators_admin_department_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return CreateStrategicIndicatorsAdminDepartmentUseCase(repository)


def build_update_strategic_indicators_admin_department_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return UpdateStrategicIndicatorsAdminDepartmentUseCase(repository)


def build_deactivate_strategic_indicators_admin_department_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return DeactivateStrategicIndicatorsAdminDepartmentUseCase(repository)


def build_delete_strategic_indicators_admin_department_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return DeleteStrategicIndicatorsAdminDepartmentUseCase(repository)


def build_list_strategic_indicators_admin_department_indicators_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return ListStrategicIndicatorsAdminDepartmentIndicatorsUseCase(repository)


def build_create_strategic_indicators_admin_department_indicator_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return CreateStrategicIndicatorsAdminDepartmentIndicatorUseCase(repository)


def build_update_strategic_indicators_admin_department_indicator_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return UpdateStrategicIndicatorsAdminDepartmentIndicatorUseCase(repository)


def build_deactivate_strategic_indicators_admin_department_indicator_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return DeactivateStrategicIndicatorsAdminDepartmentIndicatorUseCase(repository)


def build_delete_strategic_indicators_admin_department_indicator_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return DeleteStrategicIndicatorsAdminDepartmentIndicatorUseCase(repository)


def build_bulk_create_strategic_indicators_indicator_goals_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return BulkCreateStrategicIndicatorsIndicatorGoalsUseCase(repository)


def build_duplicate_strategic_indicators_indicator_goals_year_use_case():
    goals_repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    indicators_repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return DuplicateStrategicIndicatorsIndicatorGoalsYearUseCase(
        goals_repository=goals_repository,
        indicators_repository=indicators_repository,
    )


def build_fill_missing_strategic_indicators_indicator_goals_use_case():
    goals_repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    indicators_repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return FillMissingStrategicIndicatorsIndicatorGoalsUseCase(
        goals_repository=goals_repository,
        indicators_repository=indicators_repository,
    )


def build_list_strategic_indicators_goal_years_overview_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return ListStrategicIndicatorsGoalYearsOverviewUseCase(repository)


def build_activate_strategic_indicators_admin_department_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return ActivateStrategicIndicatorsAdminDepartmentUseCase(repository)


def build_get_supplies_indicators_snapshot_port():
    return SuppliesIndicatorsSnapshotProvider(
        get_cpv_use_case=build_get_cpv_use_case(),
        get_inventory_turnover_use_case=build_get_inventory_turnover_use_case(),
        get_otd_use_case=build_get_otd_use_case(),
        get_stock_value_use_case=build_get_stock_value_use_case(),
    )


def build_activate_strategic_indicators_admin_department_indicator_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return ActivateStrategicIndicatorsAdminDepartmentIndicatorUseCase(repository)