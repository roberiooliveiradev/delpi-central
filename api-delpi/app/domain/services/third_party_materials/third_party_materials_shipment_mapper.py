"""Agrupa linhas da view (1 por retorno) em remessas únicas."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.domain.totvs.protheus_third_party_materials import VIEW_TO_API_SHIPMENT_STATUS


def as_quantity(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, Decimal):
        return float(format(value.normalize(), "f"))
    text = str(value).strip().replace(",", ".")
    if not text:
        return 0.0
    return float(format(Decimal(text).normalize(), "f"))


def as_iso_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text or None


def as_bool_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().upper()
    return text in {"S", "1", "TRUE", "SIM"}


def map_status(value: Any) -> str:
    token = str(value or "").strip().upper()
    return VIEW_TO_API_SHIPMENT_STATUS.get(token, token.lower() or "completed")


def map_return_row(row: dict) -> dict | None:
    recno = row.get("RECNO_RETORNO")
    if recno in (None, ""):
        return None
    return {
        "return_recno": int(recno),
        "number": str(row.get("NF_RETORNO") or "").strip() or None,
        "series": str(row.get("SERIE_RETORNO") or "").strip() or None,
        "issued_on": as_iso_date(row.get("EMISSAO_RETORNO")),
        "posted_on": as_iso_date(row.get("DIGITACAO_RETORNO")),
        "tes": str(row.get("TES_RETORNO") or "").strip() or None,
        "quantity": as_quantity(row.get("QTD_RETORNO")),
        "accumulated_returned_quantity": as_quantity(row.get("QTD_DEVOLVIDA_ACUMULADA")),
        "balance_after_return": as_quantity(row.get("SALDO_APOS_RETORNO")),
        "partner_type": str(row.get("TIPO_PARCEIRO_RETORNO") or "").strip() or None,
        # Homolog: só TIPO_PARCEIRO_RETORNO na view; code/loja ficam None.
        "partner_code": str(row.get("COD_PARCEIRO_RETORNO") or "").strip() or None,
        "partner_store": str(row.get("LOJA_PARCEIRO_RETORNO") or "").strip() or None,
    }


def map_shipment_header(row: dict) -> dict:
    return {
        "shipment_recno": int(row.get("RECNO_REMESSA") or 0),
        "branch": str(row.get("FILIAL") or "").strip(),
        "shipment_id": str(row.get("ID_REMESSA") or "").strip(),
        "product": {
            "code": str(row.get("PRODUTO") or "").strip(),
            "customer_reference": str(row.get("REFERENCIA_CLIENTE") or "").strip() or None,
            "description": str(row.get("DESCRICAO_PRODUTO") or "").strip() or None,
            "unit": str(row.get("UNIDADE_MEDIDA") or "").strip() or None,
            "type": str(row.get("TIPO_PRODUTO") or "").strip() or None,
            "group": str(row.get("GRUPO_PRODUTO") or "").strip() or None,
            "blocked": as_bool_flag(row.get("PRODUTO_BLOQUEADO")),
        },
        "partner": {
            "type": str(row.get("TIPO_PARCEIRO") or "").strip() or None,
            "code": str(row.get("COD_PARCEIRO") or "").strip() or None,
            "store": str(row.get("LOJA_PARCEIRO") or "").strip() or None,
            "name": str(row.get("NOME_PARCEIRO") or "").strip() or None,
            "short_name": str(row.get("NOME_REDUZIDO_PARCEIRO") or "").strip() or None,
            "blocked": as_bool_flag(row.get("PARCEIRO_BLOQUEADO")),
        },
        "receipt_invoice": {
            "number": str(row.get("NF_RECEBIMENTO") or "").strip() or None,
            "series": str(row.get("SERIE_RECEBIMENTO") or "").strip() or None,
            "issued_on": as_iso_date(row.get("EMISSAO_RECEBIMENTO")),
            "posted_on": as_iso_date(row.get("DIGITACAO_RECEBIMENTO")),
            "tes": str(row.get("TES_RECEBIMENTO") or "").strip() or None,
        },
        "received_quantity": as_quantity(row.get("QTD_RECEBIDA")),
        "returned_quantity": as_quantity(row.get("QTD_DEVOLVIDA_TOTAL")),
        "pending_balance": as_quantity(row.get("SALDO_A_ENTREGAR")),
        "status": map_status(row.get("STATUS_REMESSA")),
        "has_balance": as_bool_flag(row.get("POSSUI_SALDO")),
        "attended_indicator": str(row.get("IND_ATENDIDO") or "").strip() or None,
        "summed_return_quantity": as_quantity(row.get("QTD_RETORNOS_SOMADA")),
        "control_difference": as_quantity(row.get("DIFERENCA_CONTROLE")),
        "returns": [],
    }


def group_shipment_rows(rows: list[dict]) -> list[dict]:
    by_recno: dict[int, dict] = {}
    order: list[int] = []
    for row in rows:
        recno = int(row.get("RECNO_REMESSA") or 0)
        if recno not in by_recno:
            by_recno[recno] = map_shipment_header(row)
            order.append(recno)
        mapped_return = map_return_row(row)
        if mapped_return is not None:
            by_recno[recno]["returns"].append(mapped_return)
    return [by_recno[recno] for recno in order]


def flatten_export_rows(shipments: list[dict]) -> list[dict]:
    flattened: list[dict] = []
    for shipment in shipments:
        base = {
            "shipment_recno": shipment["shipment_recno"],
            "shipment_id": shipment["shipment_id"],
            "branch": shipment["branch"],
            "product_code": shipment["product"]["code"],
            "customer_reference": shipment["product"]["customer_reference"],
            "product_description": shipment["product"]["description"],
            "partner_code": shipment["partner"]["code"],
            "partner_store": shipment["partner"]["store"],
            "partner_name": shipment["partner"]["name"],
            "receipt_number": shipment["receipt_invoice"]["number"],
            "receipt_series": shipment["receipt_invoice"]["series"],
            "receipt_issued_on": shipment["receipt_invoice"]["issued_on"],
            "received_quantity": shipment["received_quantity"],
            "returned_quantity": shipment["returned_quantity"],
            "pending_balance": shipment["pending_balance"],
            "status": shipment["status"],
            "control_difference": shipment["control_difference"],
        }
        returns = shipment.get("returns") or []
        if not returns:
            flattened.append({**base, "return_recno": None, "return_number": None,
                              "return_series": None, "return_issued_on": None,
                              "return_tes": None, "return_quantity": None,
                              "return_partner_type": None})
            continue
        for item in returns:
            flattened.append(
                {
                    **base,
                    "return_recno": item["return_recno"],
                    "return_number": item["number"],
                    "return_series": item["series"],
                    "return_issued_on": item["issued_on"],
                    "return_tes": item["tes"],
                    "return_quantity": item["quantity"],
                    "return_partner_type": item["partner_type"],
                }
            )
    return flattened
