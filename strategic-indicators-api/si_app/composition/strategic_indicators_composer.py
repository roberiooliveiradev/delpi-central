from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.application.use_cases.strategic_indicators.get_executive_summary_real_use_case import (
    GetStrategicIndicatorsExecutiveSummaryRealUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_settings_use_case import (
    GetStrategicIndicatorsSettingsUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_settings_audit_use_case import (
    ListStrategicIndicatorsSettingsAuditUseCase,
)
from si_app.application.use_cases.strategic_indicators.update_settings_use_case import (
    UpdateStrategicIndicatorsSettingsUseCase,
)
from si_app.application.use_cases.strategic_indicators.add_change_request_comment_use_case import (
    AddStrategicIndicatorsChangeRequestCommentUseCase,
)
from si_app.application.use_cases.strategic_indicators.create_change_request_use_case import (
    CreateStrategicIndicatorsChangeRequestUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_change_requests_use_case import (
    ListStrategicIndicatorsChangeRequestsUseCase,
)
from si_app.application.use_cases.strategic_indicators.submit_change_request_use_case import (
    SubmitStrategicIndicatorsChangeRequestUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_indicators_use_case import (
    GetStrategicIndicatorsUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_departments_real_use_case import (
    GetStrategicIndicatorsDepartmentsRealUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_department_details_real_use_case import (
    GetStrategicIndicatorsDepartmentDetailsRealUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_alerts_real_use_case import (
    GetStrategicIndicatorsAlertsRealUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_trends_real_use_case import (
    GetStrategicIndicatorsTrendsRealUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_goals_by_source_keys_use_case import (
    GetDashboardGoalsBySourceKeysUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_departments_tree_use_case import (
    GetStrategicIndicatorsDepartmentsTreeUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_indicator_goals_use_case import (
    ListStrategicIndicatorsIndicatorGoalsUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_indicator_goal_history_use_case import (
    ListStrategicIndicatorsIndicatorGoalHistoryUseCase,
)
from si_app.application.use_cases.strategic_indicators.create_indicator_goal_use_case import (
    CreateStrategicIndicatorsIndicatorGoalUseCase,
)
from si_app.application.use_cases.strategic_indicators.update_indicator_goal_use_case import (
    UpdateStrategicIndicatorsIndicatorGoalUseCase,
)
from si_app.application.use_cases.strategic_indicators.activate_indicator_goal_use_case import (
    ActivateStrategicIndicatorsIndicatorGoalUseCase,
)
from si_app.application.use_cases.strategic_indicators.delete_indicator_goal_use_case import (
    DeleteStrategicIndicatorsIndicatorGoalUseCase,
)
from si_app.application.use_cases.strategic_indicators.deactivate_indicator_goal_use_case import (
    DeactivateStrategicIndicatorsIndicatorGoalUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_admin_departments_use_case import (
    ListStrategicIndicatorsAdminDepartmentsUseCase,
)
from si_app.application.use_cases.strategic_indicators.create_admin_department_use_case import (
    CreateStrategicIndicatorsAdminDepartmentUseCase,
)
from si_app.application.use_cases.strategic_indicators.update_admin_department_use_case import (
    UpdateStrategicIndicatorsAdminDepartmentUseCase,
)
from si_app.application.use_cases.strategic_indicators.deactivate_admin_department_use_case import (
    DeactivateStrategicIndicatorsAdminDepartmentUseCase,
)
from si_app.application.use_cases.strategic_indicators.delete_admin_department_use_case import (
    DeleteStrategicIndicatorsAdminDepartmentUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_admin_department_indicators_use_case import (
    ListStrategicIndicatorsAdminDepartmentIndicatorsUseCase,
)
from si_app.application.use_cases.strategic_indicators.create_admin_department_indicator_use_case import (
    CreateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from si_app.application.use_cases.strategic_indicators.update_admin_department_indicator_use_case import (
    UpdateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from si_app.application.use_cases.strategic_indicators.deactivate_admin_department_indicator_use_case import (
    DeactivateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from si_app.application.use_cases.strategic_indicators.delete_admin_department_indicator_use_case import (
    DeleteStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from si_app.application.use_cases.strategic_indicators.bulk_create_indicator_goals_use_case import (
    BulkCreateStrategicIndicatorsIndicatorGoalsUseCase,
)
from si_app.application.use_cases.strategic_indicators.duplicate_indicator_goals_year_use_case import (
    DuplicateStrategicIndicatorsIndicatorGoalsYearUseCase,
)
from si_app.application.use_cases.strategic_indicators.fill_missing_indicator_goals_use_case import (
    FillMissingStrategicIndicatorsIndicatorGoalsUseCase,
)
from si_app.application.use_cases.strategic_indicators.list_goal_years_overview_use_case import (
    ListStrategicIndicatorsGoalYearsOverviewUseCase,
)
from si_app.application.use_cases.strategic_indicators.export_admin_config_use_case import (
    ExportStrategicIndicatorsAdminConfigUseCase,
)
from si_app.application.use_cases.strategic_indicators.import_admin_config_use_case import (
    ImportStrategicIndicatorsAdminConfigUseCase,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_config_bundle_repository import (
    PostgresStrategicIndicatorsAdminConfigBundleRepository,
)
from si_app.application.use_cases.strategic_indicators.activate_admin_department_use_case import (
    ActivateStrategicIndicatorsAdminDepartmentUseCase,
)
from si_app.application.use_cases.strategic_indicators.activate_admin_department_indicator_use_case import (
    ActivateStrategicIndicatorsAdminDepartmentIndicatorUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_presentation_use_case import (
    GetStrategicIndicatorsPresentationUseCase,
)

from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)

from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_repository import (
    PostgresStrategicIndicatorsSettingsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_change_request_repository import (
    PostgresStrategicIndicatorsChangeRequestRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
    PostgresStrategicIndicatorsSettingsAuditRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_catalog_repository import (
    PostgresStrategicIndicatorsCatalogRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_calculation_snapshots_repository import (
    PostgresStrategicIndicatorsCalculationSnapshotsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_period_scores_repository import (
    PostgresStrategicIndicatorsPeriodScoresRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_resolved_indicators_catalog_repository import (
    PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_departments_repository import (
    PostgresStrategicIndicatorsAdminDepartmentsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_department_indicators_repository import (
    PostgresStrategicIndicatorsDepartmentIndicatorsRepository,
)

from si_app.infrastructure.providers.strategic_indicators.calculated_alerts_summary_provider import (
    CalculatedStrategicIndicatorsAlertsSummaryProvider,
)
from si_app.infrastructure.providers.strategic_indicators.real_indicator_measurements_provider import (
    RealStrategicIndicatorsMeasurementsProvider,
)
from si_app.infrastructure.providers.strategic_indicators.production_indicators_snapshot_provider import (
    ProductionIndicatorsSnapshotProvider,
)
from si_app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
)


from si_app.composition.commercial_composer import (
    build_commercial_metrics_snapshot_service,
)
from si_app.composition.production_composer import (
    build_production_metrics_snapshot_service,
)
from si_app.composition.quality_composer import (
    build_get_quality_indicators_snapshot_port,
)
from si_app.composition.hr_composer import (
    build_get_hr_indicators_snapshot_port,
)
from si_app.composition.financial_composer import (
    build_get_financial_indicators_snapshot_port,
)
from si_app.composition.supplies_composer import (
    build_supplies_indicators_snapshot_provider,
)

from si_app.composition.engineering_composer import (
    build_engineering_indicators_snapshot_provider,
)

def build_get_engineering_indicators_snapshot_port():
    return build_engineering_indicators_snapshot_provider()


def build_get_production_indicators_snapshot_port():
    return ProductionIndicatorsSnapshotProvider(
        production_metrics_snapshot_service=build_production_metrics_snapshot_service(),
    )


def build_get_commercial_indicators_snapshot_port():
    return CommercialIndicatorsSnapshotProvider(
        commercial_metrics_snapshot_service=build_commercial_metrics_snapshot_service(),
    )


def build_get_supplies_indicators_snapshot_port():
    return build_supplies_indicators_snapshot_provider()


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


def build_strategic_indicators_period_scores_repository() -> (
    PostgresStrategicIndicatorsPeriodScoresRepository
):
    return PostgresStrategicIndicatorsPeriodScoresRepository()


def build_strategic_indicators_calculation_snapshots_repository() -> (
    PostgresStrategicIndicatorsCalculationSnapshotsRepository
):
    return PostgresStrategicIndicatorsCalculationSnapshotsRepository()


def build_strategic_indicators_snapshot_service() -> StrategicIndicatorsSnapshotService:
    structural_catalog_repository = PostgresStrategicIndicatorsCatalogRepository()
    resolved_catalog_repository = PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository()

    return StrategicIndicatorsSnapshotService(
        departments_catalog_repository=structural_catalog_repository,
        resolved_indicators_catalog_repository=resolved_catalog_repository,
        measurements_port=build_real_indicator_measurements_provider(),
        measurements_port_factory=build_real_indicator_measurements_provider,
        period_scores_repository=build_strategic_indicators_period_scores_repository(),
        calculation_snapshots_repository=build_strategic_indicators_calculation_snapshots_repository(),
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


def build_get_strategic_indicators_departments_tree_use_case():
    snapshot_service = build_strategic_indicators_snapshot_service()
    calculator = StrategicIndicatorsCalculator()
    return GetStrategicIndicatorsDepartmentsTreeUseCase(
        trends_use_case=GetStrategicIndicatorsTrendsRealUseCase(
            snapshot_service=snapshot_service,
        ),
        departments_use_case=GetStrategicIndicatorsDepartmentsRealUseCase(
            snapshot_service=snapshot_service,
            calculator=calculator,
        ),
        indicators_use_case=GetStrategicIndicatorsUseCase(
            snapshot_service=snapshot_service,
            calculator=calculator,
        ),
    )


def build_get_departments_tree_snapshot_use_case():
    from si_app.application.use_cases.strategic_indicators.get_departments_tree_snapshot_use_case import (
        GetDepartmentsTreeSnapshotUseCase,
    )

    tree_uc = build_get_strategic_indicators_departments_tree_use_case()
    return GetDepartmentsTreeSnapshotUseCase(
        tree_use_case=tree_uc,
        snapshot_service=build_strategic_indicators_snapshot_service(),
        alerts_summary_port=CalculatedStrategicIndicatorsAlertsSummaryProvider(),
    )


def build_get_departments_tree_trends_use_case():
    from si_app.application.use_cases.strategic_indicators.get_departments_tree_trends_use_case import (
        GetDepartmentsTreeTrendsUseCase,
    )

    tree_uc = build_get_strategic_indicators_departments_tree_use_case()
    return GetDepartmentsTreeTrendsUseCase(
        tree_use_case=tree_uc,
        trends_use_case=tree_uc._trends_use_case,
    )


def build_get_dashboard_goals_by_source_keys_use_case():
    return GetDashboardGoalsBySourceKeysUseCase(
        goals_repository=PostgresStrategicIndicatorsIndicatorGoalsRepository(),
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


def build_delete_strategic_indicators_indicator_goal_use_case():
    repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()
    return DeleteStrategicIndicatorsIndicatorGoalUseCase(repository)


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


def build_export_strategic_indicators_admin_config_use_case():
    repository = PostgresStrategicIndicatorsAdminConfigBundleRepository()
    return ExportStrategicIndicatorsAdminConfigUseCase(repository)


def build_import_strategic_indicators_admin_config_use_case():
    repository = PostgresStrategicIndicatorsAdminConfigBundleRepository()
    return ImportStrategicIndicatorsAdminConfigUseCase(repository)


def build_activate_strategic_indicators_admin_department_use_case():
    repository = PostgresStrategicIndicatorsAdminDepartmentsRepository()
    return ActivateStrategicIndicatorsAdminDepartmentUseCase(repository)


def build_activate_strategic_indicators_admin_department_indicator_use_case():
    repository = PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
    return ActivateStrategicIndicatorsAdminDepartmentIndicatorUseCase(repository)


def build_get_strategic_indicators_presentation_use_case():
    return GetStrategicIndicatorsPresentationUseCase(
        snapshot_service=build_strategic_indicators_snapshot_service(),
        alerts_summary_port=CalculatedStrategicIndicatorsAlertsSummaryProvider(),
        calculator=StrategicIndicatorsCalculator(),
    )