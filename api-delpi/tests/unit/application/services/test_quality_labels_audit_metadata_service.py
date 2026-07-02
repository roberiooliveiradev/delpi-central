from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.quality_labels.quality_labels_audit_metadata_service import (
    QualityLabelsAuditMetadataService,
)


def test_build_audit_metadata_includes_op_product_and_sources():
    production_uc = MagicMock()
    production_uc.execute.return_value = {
        "order": {
            "production_order": "10278501001",
            "branch": "02",
            "product_code": "90263901",
        },
        "linked_orders": [{"production_order": "10278501002"}],
        "link_summary": {"total_pi_orders": 1},
    }
    structure_uc = MagicMock()
    structure_uc.execute.return_value = {"root": {"code": "90263901"}, "items": []}
    guide_uc = MagicMock()
    guide_uc.execute.return_value = {"items": [{"operation": "10"}]}
    inspection_uc = MagicMock()
    inspection_uc.execute.return_value = {"items": [{"has_inspection": True}]}

    service = QualityLabelsAuditMetadataService(
        production_order_use_case=production_uc,
        structure_use_case=structure_uc,
        guide_use_case=guide_uc,
        inspection_use_case=inspection_uc,
        max_depth=6,
    )

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["snapshotVersion"] == 1
    assert payload["productionOrder"]["order"]["product_code"] == "90263901"
    assert payload["product"]["structure"]["root"]["code"] == "90263901"
    assert payload["product"]["routing"]["items"][0]["operation"] == "10"
    assert payload["product"]["inspection"]["items"][0]["has_inspection"] is True
    assert len(payload["sources"]) == 4
    assert payload["errors"] == []
