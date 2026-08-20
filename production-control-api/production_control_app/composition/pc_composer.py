from __future__ import annotations

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.overview_service import OverviewService
from production_control_app.application.services.problem_analysis_service import ProblemAnalysisService
from production_control_app.application.services.subplugin_catalog_service import SubpluginCatalogService
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionGateway
from production_control_app.infrastructure.persistence.postgres_machine_load_snapshot_repository import (
    PostgresMachineLoadSnapshotRepository,
)


def build_catalog_service() -> SubpluginCatalogService:
    return SubpluginCatalogService()


def build_branch_access_service() -> BranchAccessService:
    return BranchAccessService()


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
    )
