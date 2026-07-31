"""Testes — aliases canônicos de OP e mapper PCP."""

from __future__ import annotations

from app.domain.services.production.pcp_order_item_mapper import PcpOrderItemMapper
from app.domain.services.production.production_order_item_alias_service import (
    ProductionOrderItemAliasService,
)


def test_alias_adds_product_description_from_description() -> None:
    item = ProductionOrderItemAliasService.enrich_list_item(
        {"description": "CHICOTE", "planned_qty": 10, "produced_qty": 4}
    )
    assert item["product_description"] == "CHICOTE"
    assert item["description"] == "CHICOTE"
    assert item["pending_qty"] == 6


def test_alias_adds_otd_status_from_status() -> None:
    item = ProductionOrderItemAliasService.enrich_list_item(
        {"status": "late", "days_diff": 3}
    )
    assert item["otd_status"] == "late"
    assert item["status"] == "late"
    assert item["days_late"] == 3


def test_pcp_mapper_maps_view_flags() -> None:
    item = PcpOrderItemMapper.map_item(
        {
            "FILIAL": "01",
            "OP_CHAVE": "00160802001",
            "PRODUTO": "90300005",
            "DESC_PRODUTO": "RESISTOR",
            "PRODUTO_DESCRICAO": "90300005 - RESISTOR",
            "QTD_ORDEM": 10,
            "QTD_APONTADA": 3,
            "SALDO_OP": 7,
            "FL_OP_EM_ABERTO": 1,
            "FL_OP_MAE": 0,
            "FL_ATRASADA": "Sim",
            "FL_TEM_SALDO": "Sim",
            "DIAS_ATRASO": 5,
            "DT_ENTREGA": "2026-07-01",
        }
    )
    assert item["production_order"] == "00160802001"
    assert item["product_description"] == "90300005 - RESISTOR"
    assert item["description"] == item["product_description"]
    assert item["pending_qty"] == 7
    assert item["is_open"] is True
    assert item["is_mother"] is False
    assert item["is_delayed"] is True
    assert item["days_late"] == 5
