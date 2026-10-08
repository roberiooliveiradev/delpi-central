from __future__ import annotations

from functools import lru_cache
from typing import Any

from production_control_app.config import settings
from production_control_app.application.services.machine_load_change_notifier import (
    notify_machine_load_changed,
)
from production_control_app.application.services.detectors.incomplete_order_sets_detector import (
    DETECTOR_ID as DETECTOR_INCOMPLETE_ORDER_SETS,
    IncompleteOrderSetsDetector,
)
from production_control_app.application.services.detectors.order_set_quantity_mismatches_detector import (
    DETECTOR_ID as DETECTOR_QUANTITY_MISMATCHES,
    OrderSetQuantityMismatchesDetector,
)
from production_control_app.application.services.detectors.uncovered_demand_detector import (
    DETECTOR_ID as DETECTOR_UNCOVERED_DEMAND,
    UncoveredDemandDetector,
)
from production_control_app.application.services.detectors.shared_structure_intermediates_detector import (
    DETECTOR_ID as DETECTOR_SHARED_STRUCTURE,
    SharedStructureIntermediatesDetector,
)
from production_control_app.application.services.delivery_map_drawing_service import (
    DeliveryMapDrawingService,
)
from production_control_app.application.services.delivery_map_service import DeliveryMapService
from production_control_app.application.services.demand_service import DemandService
from production_control_app.application.services.finished_product_shortage_service import (
    FinishedProductShortageService,
)
from production_control_app.application.services.line_feeder_service import LineFeederService
from production_control_app.application.services.materials_service import MaterialsService
from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.overview_service import OverviewService
from production_control_app.application.services.problem_analysis_service import ProblemAnalysisService
from production_control_app.application.services.problem_analysis_settings import detector_entry
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_delivery_map_access_service import (
    PublicDeliveryMapAccessService,
)
from production_control_app.application.services.public_machine_load_drawing_service import (
    PublicMachineLoadDrawingService,
)
from production_control_app.application.services.public_machine_load_product_model_service import (
    PublicMachineLoadProductModelService,
)
from production_control_app.application.services.public_operation_appointments_service import (
    PublicOperationAppointmentsService,
)
from production_control_app.application.services.public_operation_materials_service import (
    PublicOperationMaterialsService,
)
from production_control_app.application.services.public_operation_process_inspections_service import (
    PublicOperationProcessInspectionsService,
)
from production_control_app.application.services.public_work_center_performance_service import (
    PublicWorkCenterPerformanceService,
)
from production_control_app.application.services.public_work_center_downtime_items_service import (
    PublicWorkCenterDowntimeItemsService,
)
from production_control_app.application.services.reports_service import ReportsService
from production_control_app.application.services.subplugin_catalog_service import SubpluginCatalogService
from production_control_app.domain.ports.drawing_library import DrawingLibraryPort
from production_control_app.domain.ports.problem_detector import ProblemDetector
from production_control_app.domain.ports.delivery_map_snapshot_repository import (
    DeliveryMapSnapshotRepositoryPort,
)
from production_control_app.domain.ports.line_feeder_pick_plan_repository import (
    LineFeederPickPlanRepositoryPort,
)
from production_control_app.domain.ports.machine_load_publication_repository import (
    MachineLoadPublicationRepositoryPort,
)
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.infrastructure.gateways.api_delpi_drawing_library_client import (
    ApiDelpiDrawingLibraryClient,
)
from production_control_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionGateway
from production_control_app.infrastructure.persistence.postgres_delivery_map_snapshot_repository import (
    PostgresDeliveryMapSnapshotRepository,
)
from production_control_app.infrastructure.persistence.postgres_line_feeder_pick_plan_repository import (
    PostgresLineFeederPickPlanRepository,
)
from production_control_app.infrastructure.persistence.postgres_machine_load_publication_repository import (
    PostgresMachineLoadPublicationRepository,
)
from production_control_app.infrastructure.persistence.postgres_machine_load_snapshot_repository import (
    PostgresMachineLoadSnapshotRepository,
)
from production_control_app.infrastructure.storage.product_3d_model_storage import (
    Product3DModelFilesystemStorage,
)
from production_control_app.application.services.product_3d_model_service import (
    Product3DModelService,
)
from production_control_app.domain.ports.product_3d_model_repository import (
    Product3DModelRepositoryPort,
)
from production_control_app.domain.ports.product_3d_model_storage import Product3DModelStoragePort
from production_control_app.infrastructure.persistence.postgres_product_3d_model_repository import (
    PostgresProduct3DModelRepository,
)


def build_catalog_service() -> SubpluginCatalogService:
    return SubpluginCatalogService()


def build_branch_access_service() -> BranchAccessService:
    return BranchAccessService()


def build_public_cockpit_access_service() -> PublicCockpitAccessService:
    return PublicCockpitAccessService()


def build_public_delivery_map_access_service() -> PublicDeliveryMapAccessService:
    return PublicDeliveryMapAccessService()


def build_machine_load_snapshot_repository() -> MachineLoadSnapshotRepositoryPort:
    return PostgresMachineLoadSnapshotRepository()


def build_machine_load_publication_repository() -> MachineLoadPublicationRepositoryPort:
    return PostgresMachineLoadPublicationRepository()


def build_delivery_map_snapshot_repository() -> DeliveryMapSnapshotRepositoryPort:
    return PostgresDeliveryMapSnapshotRepository()


def build_problem_detectors(
    gateway: DelpiProductionGateway | None = None,
) -> dict[str, ProblemDetector]:
    """Registro de detectores. A ordem e os textos vêm do catálogo JSON."""
    resolved = gateway or DelpiProductionGateway()
    return {
        DETECTOR_INCOMPLETE_ORDER_SETS: IncompleteOrderSetsDetector(
            resolved,
            settings=detector_entry(DETECTOR_INCOMPLETE_ORDER_SETS) or {},
        ),
        DETECTOR_QUANTITY_MISMATCHES: OrderSetQuantityMismatchesDetector(
            resolved,
            settings=detector_entry(DETECTOR_QUANTITY_MISMATCHES) or {},
        ),
        DETECTOR_UNCOVERED_DEMAND: UncoveredDemandDetector(
            resolved,
            settings=detector_entry(DETECTOR_UNCOVERED_DEMAND) or {},
        ),
        DETECTOR_SHARED_STRUCTURE: SharedStructureIntermediatesDetector(
            resolved,
            settings=detector_entry(DETECTOR_SHARED_STRUCTURE) or {},
        ),
    }


def build_problem_analysis_service(
    gateway: DelpiProductionGateway | None = None,
) -> ProblemAnalysisService:
    return ProblemAnalysisService(
        build_problem_detectors(gateway),
        branch_access=build_branch_access_service(),
    )


def build_overview_service(
    gateway: DelpiProductionGateway | None = None,
) -> OverviewService:
    return OverviewService(
        gateway or DelpiProductionGateway(),
        branch_access=build_branch_access_service(),
    )


def build_demand_service(
    gateway: DelpiProductionGateway | None = None,
) -> DemandService:
    return DemandService(
        gateway or DelpiProductionGateway(),
        branch_access=build_branch_access_service(),
    )


def build_materials_service(
    gateway: DelpiProductionGateway | None = None,
) -> MaterialsService:
    return MaterialsService(
        gateway or DelpiProductionGateway(),
        branch_access=build_branch_access_service(),
    )


def build_reports_service(
    gateway: DelpiProductionGateway | None = None,
) -> ReportsService:
    return ReportsService(
        gateway or DelpiProductionGateway(),
        branch_access=build_branch_access_service(),
    )


def build_finished_product_shortage_service(
    gateway: DelpiProductionGateway | None = None,
) -> FinishedProductShortageService:
    return FinishedProductShortageService(
        gateway or DelpiProductionGateway(),
        branch_access=build_branch_access_service(),
    )


def build_delivery_map_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: DeliveryMapSnapshotRepositoryPort | None = None,
) -> DeliveryMapService:
    return DeliveryMapService(
        gateway or DelpiProductionGateway(),
        snapshots=snapshots or build_delivery_map_snapshot_repository(),
        branch_access=build_branch_access_service(),
    )


def build_machine_load_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    publications: MachineLoadPublicationRepositoryPort | None = None,
) -> MachineLoadService:
    from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
        PostgresProductionRunRepository,
    )

    return MachineLoadService(
        gateway or DelpiProductionGateway(),
        snapshots=snapshots or build_machine_load_snapshot_repository(),
        publications=publications or build_machine_load_publication_repository(),
        branch_access=build_branch_access_service(),
        change_notifier=notify_machine_load_changed,
        list_open_runs=PostgresProductionRunRepository().list_open_runs_by_branch,
    )


def build_line_feeder_pick_plan_repository() -> LineFeederPickPlanRepositoryPort:
    return PostgresLineFeederPickPlanRepository()


def build_line_feeder_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    pick_plans: LineFeederPickPlanRepositoryPort | None = None,
) -> LineFeederService:
    return LineFeederService(
        gateway or DelpiProductionGateway(),
        snapshots=snapshots or build_machine_load_snapshot_repository(),
        pick_plans=pick_plans or build_line_feeder_pick_plan_repository(),
        branch_access=build_branch_access_service(),
    )


def build_drawing_library_storage() -> DrawingLibraryPort:
    """Canonical product drawing access is owned by api-delpi (not local FILESERVER)."""
    return ApiDelpiDrawingLibraryClient()


def build_product_3d_model_repository() -> Product3DModelRepositoryPort:
    return PostgresProduct3DModelRepository()


def build_product_3d_model_storage() -> Product3DModelStoragePort:
    return Product3DModelFilesystemStorage()


def build_product_3d_model_service(
    *,
    models: Product3DModelRepositoryPort | None = None,
    storage: Product3DModelStoragePort | None = None,
) -> Product3DModelService:
    return Product3DModelService(
        models=models or build_product_3d_model_repository(),
        storage=storage or build_product_3d_model_storage(),
    )


def build_public_machine_load_drawing_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    drawings: DrawingLibraryPort | None = None,
) -> PublicMachineLoadDrawingService:
    return PublicMachineLoadDrawingService(
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(gateway, snapshots=snapshots),
        drawings=drawings or build_drawing_library_storage(),
    )


def build_public_machine_load_product_model_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    models: Product3DModelService | None = None,
) -> PublicMachineLoadProductModelService:
    return PublicMachineLoadProductModelService(
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(gateway, snapshots=snapshots),
        models=models or build_product_3d_model_service(),
    )


def build_public_work_center_performance_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
) -> PublicWorkCenterPerformanceService:
    resolved = gateway or DelpiProductionGateway()
    return PublicWorkCenterPerformanceService(
        resolved,
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(resolved, snapshots=snapshots),
        branch_access=build_branch_access_service(),
    )


def build_public_work_center_downtime_items_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
) -> PublicWorkCenterDowntimeItemsService:
    resolved = gateway or DelpiProductionGateway()
    return PublicWorkCenterDowntimeItemsService(
        resolved,
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(resolved, snapshots=snapshots),
        branch_access=build_branch_access_service(),
    )


def build_public_operation_appointments_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
) -> PublicOperationAppointmentsService:
    resolved = gateway or DelpiProductionGateway()
    return PublicOperationAppointmentsService(
        resolved,
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(resolved, snapshots=snapshots),
        branch_access=build_branch_access_service(),
    )


def build_public_operation_materials_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
) -> PublicOperationMaterialsService:
    resolved = gateway or DelpiProductionGateway()
    return PublicOperationMaterialsService(
        resolved,
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(resolved, snapshots=snapshots),
        branch_access=build_branch_access_service(),
    )


def build_public_operation_process_inspections_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
) -> PublicOperationProcessInspectionsService:
    resolved = gateway or DelpiProductionGateway()
    return PublicOperationProcessInspectionsService(
        resolved,
        access=build_public_cockpit_access_service(),
        machine_load=build_machine_load_service(resolved, snapshots=snapshots),
        branch_access=build_branch_access_service(),
    )


def build_delivery_map_drawing_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: DeliveryMapSnapshotRepositoryPort | None = None,
    drawings: DrawingLibraryPort | None = None,
) -> DeliveryMapDrawingService:
    return DeliveryMapDrawingService(
        delivery_map=build_delivery_map_service(gateway, snapshots=snapshots),
        branch_access=build_branch_access_service(),
        access=build_public_delivery_map_access_service(),
        drawings=drawings or build_drawing_library_storage(),
    )


@lru_cache(maxsize=1)
def build_production_pulse_gateway() -> Any:
    from production_control_app.infrastructure.gateways.production_pulse_gateway import (
        ProductionPulseGateway,
    )

    return ProductionPulseGateway()


def close_production_pulse_gateway() -> None:
    if build_production_pulse_gateway.cache_info().currsize:
        build_production_pulse_gateway().close()
        build_production_pulse_gateway.cache_clear()


@lru_cache(maxsize=1)
def build_portal_rh_operator_directory_gateway() -> Any:
    from production_control_app.infrastructure.gateways.portal_rh_operator_directory_gateway import (  # noqa: E501
        PortalRhOperatorDirectoryGateway,
    )

    return PortalRhOperatorDirectoryGateway()


def close_portal_rh_operator_directory_gateway() -> None:
    if build_portal_rh_operator_directory_gateway.cache_info().currsize:
        build_portal_rh_operator_directory_gateway().close()
        build_portal_rh_operator_directory_gateway.cache_clear()


@lru_cache(maxsize=1)
def build_operator_directory_service() -> Any:
    """Diretório oficial de colaboradores (C2) — ainda sem consumidor.

    C3 injetará no fluxo de identificação do cockpit; hoje apenas
    infraestrutura composta.
    """
    from production_control_app.application.services.operator_directory_service import (  # noqa: E501
        OperatorDirectoryService,
    )

    return OperatorDirectoryService(build_portal_rh_operator_directory_gateway())


def build_production_run_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    pulse_gateway: Any | None = None,
) -> Any:
    from production_control_app.application.services.mes_run_lifecycle_service import (
        MesRunLifecycleService,
    )
    from production_control_app.application.services.production_run_service import (
        ProductionRunService,
    )
    from production_control_app.infrastructure.persistence.postgres_mes_repository import (
        PostgresDowntimeEventRepository,
        PostgresDowntimeReasonRepository,
        PostgresMesAuditRepository,
        PostgresWorkCenterStateRepository,
    )
    from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
        PostgresProductionRunRepository,
    )

    resolved_gateway = gateway or DelpiProductionGateway()
    machine_load = build_machine_load_service(resolved_gateway, snapshots=snapshots)

    def _queue_lookup(
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
    ):
        try:
            return machine_load.public_operation_run_context(
                branch=branch,
                production_order=production_order,
                operation_code=operation_code,
            )
        except Exception:  # noqa: BLE001
            return None

    return ProductionRunService(
        pulse_gateway=pulse_gateway or build_production_pulse_gateway(),
        operator_directory=build_operator_directory_service(),
        queue_lookup=_queue_lookup,
        standard_time_lookup=resolved_gateway.fetch_operation_standard_time,
        mes_lifecycle=MesRunLifecycleService(
            states=PostgresWorkCenterStateRepository(),
            downtimes=PostgresDowntimeEventRepository(),
            reasons=PostgresDowntimeReasonRepository(),
            run_lookup=PostgresProductionRunRepository().get_run,
        ),
        audit=PostgresMesAuditRepository(),
    )


def build_mes_integration_read_service() -> Any:
    from production_control_app.application.services.mes_integration_read_service import (
        MesIntegrationReadService,
    )
    from production_control_app.infrastructure.persistence.postgres_mes_monitoring_read_repository import (
        PostgresMesMonitoringReadRepository,
    )

    return MesIntegrationReadService(
        repository=PostgresMesMonitoringReadRepository(),
        branch_access=build_branch_access_service(),
    )


def build_mes_run_performance_service() -> Any:
    from production_control_app.application.services.mes_run_performance_service import (  # noqa: E501
        MesRunPerformanceService,
    )
    from production_control_app.infrastructure.persistence.postgres_mes_monitoring_read_repository import (  # noqa: E501
        PostgresMesMonitoringReadRepository,
    )

    return MesRunPerformanceService(
        repository=PostgresMesMonitoringReadRepository(),
    )


def build_mes_run_timeline_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    pulse_gateway: Any | None = None,
) -> Any:
    from production_control_app.application.services.mes_run_timeline_service import (  # noqa: E501
        MesRunTimelineService,
    )
    from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
        PostgresDowntimeEventRepository,
        PostgresDowntimeReasonRepository,
        PostgresWorkCenterStateRepository,
    )

    return MesRunTimelineService(
        run_service=build_production_run_service(
            gateway, snapshots=snapshots, pulse_gateway=pulse_gateway
        ),
        states=PostgresWorkCenterStateRepository(),
        downtimes=PostgresDowntimeEventRepository(),
        reasons=PostgresDowntimeReasonRepository(),
    )


def build_mes_downtime_classification_service(
    gateway: DelpiProductionGateway | None = None,
    *,
    snapshots: MachineLoadSnapshotRepositoryPort | None = None,
    pulse_gateway: Any | None = None,
) -> Any:
    from production_control_app.application.services.mes_downtime_classification_service import (  # noqa: E501
        MesDowntimeClassificationService,
    )
    from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
        PostgresDowntimeEventRepository,
        PostgresDowntimeReasonRepository,
        PostgresMesAuditRepository,
    )

    return MesDowntimeClassificationService(
        run_service=build_production_run_service(
            gateway, snapshots=snapshots, pulse_gateway=pulse_gateway
        ),
        downtimes=PostgresDowntimeEventRepository(),
        reasons=PostgresDowntimeReasonRepository(),
        audit=PostgresMesAuditRepository(),
    )


def build_mes_downtime_reason_admin_service() -> Any:
    from production_control_app.application.services.mes_downtime_reason_admin_service import (  # noqa: E501
        MesDowntimeReasonAdminService,
    )
    from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
        PostgresDowntimeReasonRepository,
    )

    return MesDowntimeReasonAdminService(reasons=PostgresDowntimeReasonRepository())


def build_operator_feedback_service() -> Any:
    """Canal de feedback/impedimentos do chão de fábrica (C1 — fundação).

    Sem consumidores HTTP ainda: o builder existe para a C2 ligar o adapter do
    cockpit e a C3 o adapter do PCP sem redescobrir wiring.
    """
    from production_control_app.application.services.operator_feedback_service import (  # noqa: E501
        OperatorFeedbackService,
    )
    from production_control_app.infrastructure.persistence.postgres_operator_feedback_repository import (  # noqa: E501
        PostgresOperatorFeedbackRepository,
    )

    return OperatorFeedbackService(feedbacks=PostgresOperatorFeedbackRepository())


def build_public_operator_feedback_service() -> Any:
    """Orquestrador do Operator Feedback no cockpit público (C2).

    Compõe: resolver oficial da bench session, fila PUBLISHED via
    MachineLoadService, service de domínio da C1, lookup leve de run ativo
    (repositório direto — sem Pulse) e notifier realtime best-effort.
    """
    from production_control_app.application.services.operator_feedback_change_notifier import (  # noqa: E501
        notify_operator_feedback_changed,
    )
    from production_control_app.application.services.public_operator_feedback_service import (  # noqa: E501
        PublicOperatorFeedbackService,
    )
    from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
        PostgresProductionRunRepository,
    )

    return PublicOperatorFeedbackService(
        run_service=build_production_run_service(),
        machine_load=build_machine_load_service(),
        feedbacks=build_operator_feedback_service(),
        run_lookup=PostgresProductionRunRepository().get_active_run,
        notify=notify_operator_feedback_changed,
        operation_materials=build_public_operation_materials_service(),
        feedback_materials=build_operator_feedback_material_service(),
        notifications=build_operator_feedback_notification_service(),
    )


def build_operator_feedback_notification_service() -> Any:
    """Notificações Minha DELPI do Operator Feedback (C6).

    Sem token configurado o gateway nem é instanciado — o dispatch vira
    no-op (o impedimento segue sendo criado normalmente).
    """
    from production_control_app.application.services.operator_feedback_notification_service import (  # noqa: E501
        OperatorFeedbackNotificationService,
    )

    gateway = None
    if (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        from production_control_app.infrastructure.gateways.core_api_notification_gateway import (  # noqa: E501
            CoreApiNotificationGateway,
        )

        gateway = CoreApiNotificationGateway()
    return OperatorFeedbackNotificationService(gateway=gateway)


def build_pcp_operator_feedback_service() -> Any:
    """Inbox e tratativa do Operator Feedback no Portal PCP (C4).

    Autorizacao reutiliza o gate da Carga Maquina (acesso + filial +
    machine-load.view); lifecycle permanece no service de dominio da C1;
    realtime e o notifier best-effort compartilhado.
    """
    from production_control_app.application.services.operator_feedback_change_notifier import (  # noqa: E501
        notify_operator_feedback_changed,
    )
    from production_control_app.application.services.pcp_operator_feedback_service import (  # noqa: E501
        PcpOperatorFeedbackService,
    )

    return PcpOperatorFeedbackService(
        branch_access=build_branch_access_service(),
        feedbacks=build_operator_feedback_service(),
        notify=notify_operator_feedback_changed,
        materials=build_operator_feedback_material_service(),
    )


def build_operator_feedback_material_service() -> Any:
    """Lifecycle dos materiais estruturados do feedback (C5)."""
    from production_control_app.application.services.operator_feedback_material_service import (  # noqa: E501
        OperatorFeedbackMaterialService,
    )
    from production_control_app.infrastructure.persistence.postgres_operator_feedback_material_repository import (  # noqa: E501
        PostgresOperatorFeedbackMaterialRepository,
    )

    return OperatorFeedbackMaterialService(
        materials=PostgresOperatorFeedbackMaterialRepository()
    )


def build_line_feeder_urgent_requests_service() -> Any:
    """Fila urgente do Alimentador de Linha — materiais faltantes vindos do
    Operator Feedback (C5). Separada das pick lists planejadas por corte."""
    from production_control_app.application.services.line_feeder_urgent_requests_service import (  # noqa: E501
        LineFeederUrgentRequestsService,
    )
    from production_control_app.application.services.operator_feedback_change_notifier import (  # noqa: E501
        notify_operator_feedback_changed,
    )
    from production_control_app.infrastructure.persistence.postgres_operator_feedback_material_repository import (  # noqa: E501
        PostgresOperatorFeedbackMaterialRepository,
    )

    materials_repo = PostgresOperatorFeedbackMaterialRepository()
    from production_control_app.application.services.operator_feedback_material_service import (  # noqa: E501
        OperatorFeedbackMaterialService,
    )

    return LineFeederUrgentRequestsService(
        branch_access=build_branch_access_service(),
        materials=materials_repo,
        lifecycle=OperatorFeedbackMaterialService(materials=materials_repo),
        snapshots=build_machine_load_snapshot_repository(),
        notify=notify_operator_feedback_changed,
    )
