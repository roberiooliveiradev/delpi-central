from __future__ import annotations

from app.application.services.quality_labels.quality_labels_qr_service import (
    QualityLabelsQrService,
)
from app.application.use_cases.quality_labels.quality_labels_service import (
    QualityLabelsService,
)
from app.composition.production_operational_composer import (
    build_get_production_order_by_op_use_case,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
)


def build_quality_labels_service() -> QualityLabelsService:
    return QualityLabelsService(
        repository=PostgresQualityLabelsRepository(),
        qr_service=QualityLabelsQrService(),
        production_order_use_case=build_get_production_order_by_op_use_case(),
    )
