from app.application.use_cases.third_party_materials.export_returns_use_case import (
    ExportThirdPartyMaterialsReturnsUseCase,
)
from app.application.use_cases.third_party_materials.get_shipment_use_case import (
    GetThirdPartyMaterialsShipmentUseCase,
)
from app.application.use_cases.third_party_materials.get_summary_use_case import (
    GetThirdPartyMaterialsSummaryUseCase,
)
from app.application.use_cases.third_party_materials.list_shipments_use_case import (
    ListThirdPartyMaterialsShipmentsUseCase,
)
from app.infrastructure.persistence.totvs.third_party_materials.third_party_materials_query_repository import (
    ThirdPartyMaterialsQueryRepository,
)


def _repository() -> ThirdPartyMaterialsQueryRepository:
    return ThirdPartyMaterialsQueryRepository()


def build_list_third_party_materials_shipments_use_case() -> (
    ListThirdPartyMaterialsShipmentsUseCase
):
    return ListThirdPartyMaterialsShipmentsUseCase(repository=_repository())


def build_get_third_party_materials_shipment_use_case() -> (
    GetThirdPartyMaterialsShipmentUseCase
):
    return GetThirdPartyMaterialsShipmentUseCase(repository=_repository())


def build_get_third_party_materials_summary_use_case() -> (
    GetThirdPartyMaterialsSummaryUseCase
):
    return GetThirdPartyMaterialsSummaryUseCase(repository=_repository())


def build_export_third_party_materials_returns_use_case() -> (
    ExportThirdPartyMaterialsReturnsUseCase
):
    return ExportThirdPartyMaterialsReturnsUseCase(repository=_repository())
