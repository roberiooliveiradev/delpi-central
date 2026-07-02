from __future__ import annotations

from app.application.services.quality_labels.quality_labels_audit_metadata_service import (
    QualityLabelsAuditMetadataService,
)
from app.application.services.quality_labels.quality_labels_certificate_service import (
    QualityLabelsCertificateService,
)
from app.application.services.quality_labels.quality_labels_certificate_storage import (
    QualityLabelsCertificateStorage,
)
from app.application.services.quality_labels.quality_labels_inspector_service import (
    QualityLabelsInspectorService,
)
from app.application.services.quality_labels.quality_labels_qr_service import (
    QualityLabelsQrService,
)
from app.application.services.quality_labels.quality_labels_signature_storage import (
    QualityLabelsSignatureStorage,
)
from app.application.use_cases.production.get_order_customer_by_op_use_case import (
    GetOrderCustomerByOpUseCase,
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
from app.infrastructure.pdf.quality_labels.quality_certificate_pdf_renderer import (
    QualityCertificatePdfRenderer,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_audit_repository import (
    PostgresQualityLabelsAuditRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_certificate_repository import (
    PostgresQualityLabelsCertificateRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_checklist_template_repository import (
    PostgresQualityLabelsChecklistTemplateRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_inspector_repository import (
    PostgresQualityLabelsInspectorRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_order_customer_repository import (
    ProductionOrderCustomerRepository,
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


def build_get_order_customer_by_op_use_case() -> GetOrderCustomerByOpUseCase:
    return GetOrderCustomerByOpUseCase(
        repository=ProductionOrderCustomerRepository(),
    )


def build_quality_labels_inspector_service() -> QualityLabelsInspectorService:
    return QualityLabelsInspectorService(
        repository=PostgresQualityLabelsInspectorRepository(),
        signature_storage=QualityLabelsSignatureStorage(),
    )


def build_quality_labels_certificate_service() -> QualityLabelsCertificateService:
    return QualityLabelsCertificateService(
        certificate_repository=PostgresQualityLabelsCertificateRepository(),
        label_repository=PostgresQualityLabelsRepository(),
        template_repository=PostgresQualityLabelsChecklistTemplateRepository(),
        inspector_repository=PostgresQualityLabelsInspectorRepository(),
        signature_storage=QualityLabelsSignatureStorage(),
        certificate_storage=QualityLabelsCertificateStorage(),
        pdf_renderer=QualityCertificatePdfRenderer(),
        order_customer_use_case=build_get_order_customer_by_op_use_case(),
        audit_repository=PostgresQualityLabelsAuditRepository(),
    )
