from __future__ import annotations

from production_control_app.application.services.machine_load_change_notifier import (
    notify_machine_load_changed,
)
from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.overview_service import OverviewService
from production_control_app.application.services.problem_analysis_service import ProblemAnalysisService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_machine_load_drawing_service import (
    PublicMachineLoadDrawingService,
)
from production_control_app.application.services.subplugin_catalog_service import SubpluginCatalogService
from production_control_app.domain.ports.drawing_library import DrawingLibraryPort
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionGateway
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


def build_machine_load_snapshot_repository() -> MachineLoadSnapshotRepositoryPort:
    return PostgresMachineLoadSnapshotRepository()


def build_problem_analysis_service(
    gateway: DelpiProductionGateway | None = None,
) -> ProblemAnalysisService:
    return ProblemAnalysisService(
        gateway or DelpiProductionGateway(),
        branch_access=build_branch_access_service(),
    )


def build_overview_service(
    gateway: DelpiProductionGateway | None = None,
) -> OverviewService:
    return OverviewService(
        gateway or DelpiProductionGateway(),
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
