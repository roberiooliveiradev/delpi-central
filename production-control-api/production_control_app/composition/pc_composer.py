from __future__ import annotations

from production_control_app.application.services.machine_load_change_notifier import (
    notify_machine_load_changed,
)
from production_control_app.application.services.detectors.incomplete_order_sets_detector import (
    DETECTOR_ID as DETECTOR_INCOMPLETE_ORDER_SETS,
    IncompleteOrderSetsDetector,
)
from production_control_app.application.services.delivery_map_drawing_service import (
    DeliveryMapDrawingService,
)
from production_control_app.application.services.delivery_map_service import DeliveryMapService
from production_control_app.application.services.demand_service import DemandService
from production_control_app.application.services.finished_product_shortage_service import (
    FinishedProductShortageService,
)
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
from production_control_app.application.services.subplugin_catalog_service import SubpluginCatalogService
from production_control_app.domain.ports.drawing_library import DrawingLibraryPort
from production_control_app.domain.ports.problem_detector import ProblemDetector
from production_control_app.domain.ports.delivery_map_snapshot_repository import (
    DeliveryMapSnapshotRepositoryPort,
)
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionGateway
from production_control_app.infrastructure.persistence.postgres_delivery_map_snapshot_repository import (
    PostgresDeliveryMapSnapshotRepository,
)
from production_control_app.infrastructure.persistence.postgres_machine_load_snapshot_repository import (
    PostgresMachineLoadSnapshotRepository,
)
from production_control_app.infrastructure.storage.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
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
) -> MachineLoadService:
    return MachineLoadService(
        gateway or DelpiProductionGateway(),
        snapshots=snapshots or build_machine_load_snapshot_repository(),
        branch_access=build_branch_access_service(),
        change_notifier=notify_machine_load_changed,
    )


def build_drawing_library_storage() -> DrawingLibraryPort:
    return DrawingPdfLibraryStorage(message=build_public_cockpit_access_service().message)


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
