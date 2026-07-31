"""Mapper — row da view PCP → item canônico EN snake_case."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.domain.production.pcp_orders_view_scope import FLAG_YES_TEXT


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iso_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text[:10]


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _flag_bit(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, (int, float)):
        return int(value) == 1
    text = str(value).strip().lower()
    return text in {"1", "true", "s", "sim", "yes"}


def _flag_sim_nao(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, (int, float)):
        return int(value) == 1
    return str(value).strip() == FLAG_YES_TEXT


class PcpOrderItemMapper:
    """Converte linha da VW_PCP_ORDENS_PRODUCAO em item de API."""

    @classmethod
    def map_item(cls, row: dict[str, Any]) -> dict[str, Any]:
        planned = _as_float(row.get("qtd_ordem") if "qtd_ordem" in row else row.get("QTD_ORDEM"))
        produced = _as_float(
            row.get("qtd_apontada") if "qtd_apontada" in row else row.get("QTD_APONTADA")
        )
        pending = row.get("saldo_op") if "saldo_op" in row else row.get("SALDO_OP")
        if pending is None or pending == "":
            pending_qty = round(planned - produced, 6)
        else:
            pending_qty = round(_as_float(pending), 6)

        product_code = _clean(row.get("produto") or row.get("PRODUTO"))
        desc = _clean(row.get("desc_produto") or row.get("DESC_PRODUTO"))
        product_description = _clean(
            row.get("produto_descricao") or row.get("PRODUTO_DESCRICAO")
        ) or desc

        op_key = _clean(row.get("op_chave") or row.get("OP_CHAVE"))
        is_open = _flag_bit(row.get("fl_op_em_aberto") or row.get("FL_OP_EM_ABERTO"))
        is_mother = _flag_bit(row.get("fl_op_mae") or row.get("FL_OP_MAE"))
        is_delayed = _flag_sim_nao(row.get("fl_atrasada") or row.get("FL_ATRASADA"))
        has_balance = _flag_sim_nao(row.get("fl_tem_saldo") or row.get("FL_TEM_SALDO"))

        return {
            "branch": _clean(row.get("filial") or row.get("FILIAL")),
            "production_order": op_key,
            "op_key": op_key,
            "order_number": _clean(row.get("op_num") or row.get("OP_NUM")),
            "order_item": _clean(row.get("op_item") or row.get("OP_ITEM")),
            "order_sequence": _clean(row.get("op_sequen") or row.get("OP_SEQUEN")),
            "parent_op_key": _clean(row.get("op_pai_chave") or row.get("OP_PAI_CHAVE"))
            or None,
            "product_code": product_code,
            "product_description": product_description,
            "description": product_description,
            "warehouse": _clean(row.get("armazem") or row.get("ARMAZEM")) or None,
            "observation": _clean(row.get("observacoes") or row.get("OBSERVACOES"))
            or None,
            "planned_qty": round(planned, 6),
            "produced_qty": round(produced, 6),
            "pending_qty": pending_qty,
            "loss_qty": round(
                _as_float(row.get("qtd_perda") or row.get("QTD_PERDA")), 6
            ),
            "issue_date": _iso_date(row.get("dt_emissao") or row.get("DT_EMISSAO")),
            "planned_start_date": _iso_date(
                row.get("dt_inicio") or row.get("DT_INICIO")
            ),
            "due_date": _iso_date(row.get("dt_entrega") or row.get("DT_ENTREGA")),
            "finish_date": _iso_date(row.get("dt_real_fim") or row.get("DT_REAL_FIM")),
            "days_late": _as_int(row.get("dias_atraso") or row.get("DIAS_ATRASO")),
            "is_open": is_open,
            "is_mother": is_mother,
            "is_delayed": is_delayed,
            "has_balance": has_balance,
            "production_status": _clean(
                row.get("situacao_producao") or row.get("SITUACAO_PRODUCAO")
            )
            or None,
            "order_type": _clean(row.get("tipo_op") or row.get("TIPO_OP")) or None,
            "order_type_code": _clean(row.get("tipo_op_cod") or row.get("TIPO_OP_COD"))
            or None,
        }

    @classmethod
    def map_items(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.map_item(row) for row in rows]
