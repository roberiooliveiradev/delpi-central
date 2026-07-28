"""Regressão: grounding canônico e colunas entity-first após busca por PN."""

from __future__ import annotations

import json

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_entity_tracker_service import ChatEntityTrackerService
from app.domain.services.chat_presentation_field_normalization_service import (
    ChatPresentationFieldNormalizationService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_entity_tracker_does_not_store_supplier_part_number_as_product_code() -> None:
    snapshot = ChatEntityTrackerService.apply_to_snapshot(
        {},
        message="liste produto com part number do fornecedor 008700056",
    )
    focus = snapshot.get("operationalFocus") or {}
    assert focus.get("productCode") != "008700056"
    assert "productCode" not in focus or focus.get("productCode") != "008700056"


def test_post_turn_promotes_unique_product_code_across_multiple_supplier_rows() -> None:
    preview = {
        "success": True,
        "data": {
            "items": [
                {
                    "product_code": "10080160",
                    "product_description": "ITEM A",
                    "supplier_code": "000192",
                    "supplier_name": "MOLEX",
                    "supplier_part_number": "008700056",
                },
                {
                    "product_code": "10080160",
                    "product_description": "ITEM A",
                    "supplier_code": "000614",
                    "supplier_name": "AVNET",
                    "supplier_part_number": "008700056",
                },
            ],
            "total": 2,
        },
    }
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {
                "parameters": {"supplier_part_number": "008700056"},
            },
            "metadata": {
                "path": "/products/by-supplier-part-number",
                "promoteCanonicalProductFromResult": True,
                "responsePreview": json.dumps(preview),
            },
        }
    ]
    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="liste produto com part number do fornecedor 008700056",
        previous_messages=[],
        tool_calls=tool_calls,
        pre_snapshot={"operationalFocus": {"productCode": "008700056"}},
    )
    focus = snapshot.get("operationalFocus") or {}
    assert focus.get("productCode") == "10080160"


def test_post_turn_does_not_promote_when_distinct_product_codes() -> None:
    preview = {
        "success": True,
        "data": {
            "items": [
                {"product_code": "10080160", "supplier_part_number": "008700056"},
                {"product_code": "10080999", "supplier_part_number": "008700056"},
            ],
            "total": 2,
        },
    }
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {"parameters": {"supplier_part_number": "008700056"}},
            "metadata": {
                "responsePreview": json.dumps(preview),
                "promoteCanonicalProductFromResult": True,
            },
        }
    ]
    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="liste produto com part number do fornecedor 008700056",
        previous_messages=[],
        tool_calls=tool_calls,
        pre_snapshot={},
    )
    focus = snapshot.get("operationalFocus") or {}
    assert focus.get("productCode") not in {"008700056", "10080160", "10080999"}


def test_normalize_table_keeps_product_columns_for_entity() -> None:
    metadata = {
        "apiDelpiResponseMeta": {"entity": "product_by_supplier_part_number"},
        "tablePresentation": {
            "type": "table",
            "title": "Resultado",
            "columns": [
                {"key": "supplier_code", "label": "Cód. fornecedor"},
                {"key": "supplier_name", "label": "Fornecedor"},
            ],
            "rows": [
                {
                    "product_code": "10080160",
                    "product_description": "TERM. CRIMPAGEM",
                    "supplier_code": "000192",
                    "supplier_name": "MOLEX BRASIL LTDA.",
                    "supplier_part_number": "008700056",
                    "registered_lead_time_days": 0,
                }
            ],
        },
    }
    ChatPresentationFieldNormalizationService.normalize_metadata(
        metadata,
        path="/products/by-supplier-part-number",
    )
    table = metadata["tablePresentation"]
    keys = [column["key"] for column in table["columns"]]
    assert "product_code" in keys
    assert "product_description" in keys
    assert "supplier_name" in keys
    assert table["rows"][0].get("product_code") == "10080160"
