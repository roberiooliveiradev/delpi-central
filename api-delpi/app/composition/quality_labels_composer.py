from __future__ import annotations

from app.application.services.quality_labels.quality_labels_audit_metadata_service import (
    QualityLabelsAuditMetadataService,
)
from app.application.services.quality_labels.quality_labels_qr_service import (
    QualityLabelsQrService,
)
from app.application.use_cases.quality_labels.quality_labels_service import (
    QualityLabelsService,
)
from app.composition.product_composer import (
    build_list_product_guide_use_case,
    build_list_product_inspection_use_case,
    build_list_structure_use_case,
)
from app.composition.production_operational_composer import (
    build_get_production_order_by_op_use_case,
    build_search_production_orders_by_op_use_case,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_audit_repository import (
    PostgresQualityLabelsAuditRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
)


def build_quality_labels_audit_metadata_service() -> QualityLabelsAuditMetadataService:
    return QualityLabelsAuditMetadataService(
        production_order_use_case=build_get_production_order_by_op_use_case(),
        structure_use_case=build_list_structure_use_case(),
        guide_use_case=build_list_product_guide_use_case(),
        inspection_use_case=build_list_product_inspection_use_case(),
    )


def build_quality_labels_service() -> QualityLabelsService:
    return QualityLabelsService(
        repository=PostgresQualityLabelsRepository(),
        qr_service=QualityLabelsQrService(),
        production_order_use_case=build_get_production_order_by_op_use_case(),
        search_orders_use_case=build_search_production_orders_by_op_use_case(),
        audit_metadata_service=build_quality_labels_audit_metadata_service(),
        audit_repository=PostgresQualityLabelsAuditRepository(),
    )
