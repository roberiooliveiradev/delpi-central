from __future__ import annotations

from decimal import Decimal

from app.domain.services.third_party_materials.third_party_materials_shipment_mapper import (
    flatten_export_rows,
    group_shipment_rows,
)


def _row(**overrides) -> dict:
    base = {
        "RECNO_REMESSA": 27062725,
        "FILIAL": "01",
        "ID_REMESSA": "UCVMKI",
        "NF_RECEBIMENTO": "004400278",
        "SERIE_RECEBIMENTO": "1",
        "EMISSAO_RECEBIMENTO": "2026-06-18",
        "DIGITACAO_RECEBIMENTO": "2026-06-22",
        "TES_RECEBIMENTO": "085",
        "PRODUTO": "10211413",
        "REFERENCIA_CLIENTE": "10018137",
        "DESCRICAO_PRODUTO": "VENTILADOR AXIAL",
        "UNIDADE_MEDIDA": "PC",
        "TIPO_PRODUTO": "MP",
        "GRUPO_PRODUTO": "1021",
        "PRODUTO_BLOQUEADO": "N",
        "TIPO_PARCEIRO": "C",
        "COD_PARCEIRO": "000001",
        "LOJA_PARCEIRO": "11",
        "NOME_PARCEIRO": "WEG DRIVES",
        "NOME_REDUZIDO_PARCEIRO": "WEG AUTOMACAO",
        "PARCEIRO_BLOQUEADO": "N",
        "QTD_RECEBIDA": Decimal("4800"),
        "QTD_DEVOLVIDA_TOTAL": Decimal("3181"),
        "SALDO_A_ENTREGAR": Decimal("1619"),
        "STATUS_REMESSA": "PARCIAL",
        "POSSUI_SALDO": "S",
        "IND_ATENDIDO": "",
        "QTD_RETORNOS_SOMADA": Decimal("3181"),
        "DIFERENCA_CONTROLE": Decimal("0"),
        "RECNO_RETORNO": None,
        "NF_RETORNO": None,
        "SERIE_RETORNO": None,
        "EMISSAO_RETORNO": None,
        "DIGITACAO_RETORNO": None,
        "TES_RETORNO": None,
        "QTD_RETORNO": None,
        "QTD_DEVOLVIDA_ACUMULADA": None,
        "SALDO_APOS_RETORNO": None,
        "TIPO_PARCEIRO_RETORNO": None,
        "COD_PARCEIRO_RETORNO": None,
        "LOJA_PARCEIRO_RETORNO": None,
    }
    base.update(overrides)
    return base


def test_groups_multiple_returns_and_keeps_partner_type_f() -> None:
    rows = [
        _row(
            RECNO_RETORNO=11,
            NF_RETORNO="102188",
            SERIE_RETORNO="1",
            EMISSAO_RETORNO="2026-07-01",
            TES_RETORNO="090",
            QTD_RETORNO=Decimal("100"),
            QTD_DEVOLVIDA_ACUMULADA=Decimal("100"),
            SALDO_APOS_RETORNO=Decimal("4700"),
            TIPO_PARCEIRO_RETORNO="C",
        ),
        _row(
            RECNO_RETORNO=12,
            NF_RETORNO="024133",
            SERIE_RETORNO="1",
            EMISSAO_RETORNO="2026-07-02",
            TES_RETORNO="090",
            QTD_RETORNO=Decimal("25"),
            QTD_DEVOLVIDA_ACUMULADA=Decimal("125"),
            SALDO_APOS_RETORNO=Decimal("4675"),
            TIPO_PARCEIRO_RETORNO="F",
        ),
        _row(
            RECNO_REMESSA=99,
            NF_RECEBIMENTO="004409700",
            STATUS_REMESSA="SEM RETORNO",
            QTD_RECEBIDA=Decimal("2000"),
            QTD_DEVOLVIDA_TOTAL=Decimal("0"),
            SALDO_A_ENTREGAR=Decimal("2000"),
            POSSUI_SALDO="S",
            QTD_RETORNOS_SOMADA=Decimal("0"),
        ),
        _row(
            RECNO_REMESSA=100,
            NF_RECEBIMENTO="004439675",
            STATUS_REMESSA="SEM RETORNO",
            QTD_RECEBIDA=Decimal("500"),
            QTD_DEVOLVIDA_TOTAL=Decimal("0"),
            SALDO_A_ENTREGAR=Decimal("500"),
            POSSUI_SALDO="S",
            QTD_RETORNOS_SOMADA=Decimal("0"),
        ),
    ]
    shipments = group_shipment_rows(rows)
    assert len(shipments) == 3
    partial = shipments[0]
    assert partial["product"]["customer_reference"] == "10018137"
    assert partial["status"] == "partial"
    assert partial["pending_balance"] == 1619
    assert len(partial["returns"]) == 2
    assert partial["returns"][1]["partner_type"] == "F"
    assert partial["returns"][1]["number"] == "024133"
    empty_nfs = {item["receipt_invoice"]["number"] for item in shipments[1:]}
    assert empty_nfs == {"004409700", "004439675"}
    assert all(item["status"] == "no_return" and item["returns"] == [] for item in shipments[1:])


def test_export_flatten_repeats_shipment_balance() -> None:
    shipments = group_shipment_rows(
        [
            _row(
                RECNO_RETORNO=11,
                NF_RETORNO="102188",
                QTD_RETORNO=Decimal("100"),
                TIPO_PARCEIRO_RETORNO="C",
            ),
            _row(
                RECNO_RETORNO=12,
                NF_RETORNO="102189",
                QTD_RETORNO=Decimal("50"),
                TIPO_PARCEIRO_RETORNO="C",
            ),
        ]
    )
    rows = flatten_export_rows(shipments)
    assert len(rows) == 2
    assert rows[0]["pending_balance"] == rows[1]["pending_balance"] == 1619
    assert rows[0]["shipment_recno"] == rows[1]["shipment_recno"] == 27062725
    assert rows[0]["customer_reference"] == "10018137"
