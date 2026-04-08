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
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_departments_catalog_repository import (
    PostgresStrategicIndicatorsDepartmentsCatalogRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_catalog_repository import (
    PostgresStrategicIndicatorsCatalogRepository,
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
from app.application.use_cases.strategic_indicators.get_departments_real_use_case import (
    GetStrategicIndicatorsDepartmentsRealUseCase,
)
from app.application.use_cases.strategic_indicators.get_department_details_real_use_case import (
    GetStrategicIndicatorsDepartmentDetailsRealUseCase,
)
from app.application.use_cases.strategic_indicators.get_alerts_real_use_case import (
    GetStrategicIndicatorsAlertsRealUseCase,
)

from app.composition.lmp_composer import (
    build_list_lmp_dashboard_use_case,
)
from app.composition.transforma_mais_composer import (
    transforma_mais_get_process_summary_composer,
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
from app.composition.audit_5s_composer import (
    audit_5s_get_summary_composer,
)
from app.composition.kaizen_composer import (
    kaizen_get_summary_composer,
)
from app.composition.ppm_composer import (
    build_get_ppm_summary_use_case,
)


def build_get_engineering_indicators_snapshot_port():
    return EngineeringIndicatorsSnapshotProvider(
        lmp_dashboard_use_case=build_list_lmp_dashboard_use_case(),
        transforma_mais_summary_use_case=transforma_mais_get_process_summary_composer(),
    )


def build_get_production_indicators_snapshot_port():
    return ProductionIndicatorsSnapshotProvider(
        direct_labor_use_case=build_get_direct_labor_cost_pct_use_case(),
        production_cost_use_case=build_get_production_cost_pct_use_case(),
        depreciation_use_case=build_get_depreciation_pct_use_case(),
        oee_use_case=build_get_overall_equipment_effectiveness_pct_use_case(),
        otd_use_case=build_get_on_time_delivery_pct_use_case(),
    )


def build_get_commercial_indicators_snapshot_port():
    return CommercialIndicatorsSnapshotProvider(
        head_office_rol_target_use_case=build_get_head_office_rol_target_pct_use_case(),
        branch_rol_target_use_case=build_get_branch_rol_target_pct_use_case(),
        sales_conversion_rate_use_case=build_get_sales_conversion_rate_use_case(),
        new_clients_average_use_case=build_get_new_clients_average_use_case(),
        new_clients_rol_pct_use_case=build_get_new_clients_rol_pct_use_case(),
    )


def build_get_quality_indicators_snapshot_port():
    return QualityIndicatorsSnapshotProvider(
        internal_ppm_use_case=build_get_ppm_summary_use_case(),
        external_ppm_use_case=build_get_ppm_summary_use_case(),
        kaizen_summary_use_case=kaizen_get_summary_composer(),
        audit_5s_summary_use_case=audit_5s_get_summary_composer(),
    )


def build_get_strategic_indicators_executive_summary_use_case(
) -> GetStrategicIndicatorsExecutiveSummaryRealUseCase:
    catalog_repository = PostgresStrategicIndicatorsCatalogRepository()

    measurements_provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=build_get_engineering_indicators_snapshot_port(),
        production_snapshot_port=build_get_production_indicators_snapshot_port(),
        commercial_snapshot_port=build_get_commercial_indicators_snapshot_port(),
        quality_snapshot_port=build_get_quality_indicators_snapshot_port(),
    )

    return GetStrategicIndicatorsExecutiveSummaryRealUseCase(
        departments_catalog_repository=catalog_repository,
        indicators_catalog_repository=catalog_repository,
        measurements_port=measurements_provider,
        alerts_summary_port=CalculatedStrategicIndicatorsAlertsSummaryProvider(),
        calculator=StrategicIndicatorsCalculator(),
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


def build_get_strategic_indicators_departments_use_case() -> GetStrategicIndicatorsDepartmentsRealUseCase:
    catalog_repository = PostgresStrategicIndicatorsCatalogRepository()

    measurements_provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=build_get_engineering_indicators_snapshot_port(),
        production_snapshot_port=build_get_production_indicators_snapshot_port(),
        commercial_snapshot_port=build_get_commercial_indicators_snapshot_port(),
        quality_snapshot_port=build_get_quality_indicators_snapshot_port(),
    )

    return GetStrategicIndicatorsDepartmentsRealUseCase(
        departments_catalog_repository=catalog_repository,
        indicators_catalog_repository=catalog_repository,
        measurements_port=measurements_provider,
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_department_details_use_case(
) -> GetStrategicIndicatorsDepartmentDetailsRealUseCase:
    catalog_repository = PostgresStrategicIndicatorsCatalogRepository()

    measurements_provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=build_get_engineering_indicators_snapshot_port(),
        production_snapshot_port=build_get_production_indicators_snapshot_port(),
        commercial_snapshot_port=build_get_commercial_indicators_snapshot_port(),
        quality_snapshot_port=build_get_quality_indicators_snapshot_port(),
    )

    return GetStrategicIndicatorsDepartmentDetailsRealUseCase(
        departments_catalog_repository=catalog_repository,
        indicators_catalog_repository=catalog_repository,
        measurements_port=measurements_provider,
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_use_case() -> GetStrategicIndicatorsUseCase:
    catalog_repository = PostgresStrategicIndicatorsCatalogRepository()

    measurements_provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=build_get_engineering_indicators_snapshot_port(),
        production_snapshot_port=build_get_production_indicators_snapshot_port(),
        commercial_snapshot_port=build_get_commercial_indicators_snapshot_port(),
        quality_snapshot_port=build_get_quality_indicators_snapshot_port(),
    )

    return GetStrategicIndicatorsUseCase(
        departments_catalog_repository=catalog_repository,
        indicators_catalog_repository=catalog_repository,
        measurements_port=measurements_provider,
        calculator=StrategicIndicatorsCalculator(),
    )


def build_get_strategic_indicators_alerts_use_case() -> GetStrategicIndicatorsAlertsRealUseCase:
    catalog_repository = PostgresStrategicIndicatorsCatalogRepository()

    measurements_provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=build_get_engineering_indicators_snapshot_port(),
        production_snapshot_port=build_get_production_indicators_snapshot_port(),
        commercial_snapshot_port=build_get_commercial_indicators_snapshot_port(),
        quality_snapshot_port=build_get_quality_indicators_snapshot_port(),
    )

    return GetStrategicIndicatorsAlertsRealUseCase(
        departments_catalog_repository=catalog_repository,
        indicators_catalog_repository=catalog_repository,
        measurements_port=measurements_provider,
        alerts_summary_port=CalculatedStrategicIndicatorsAlertsSummaryProvider(),
        calculator=StrategicIndicatorsCalculator(),
    )