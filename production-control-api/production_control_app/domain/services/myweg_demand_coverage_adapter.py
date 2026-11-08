"""Adaptador puro MyWEG → entradas do DemandCoverageService (prévia E2).

EXISTING_EQUIVALENT: YES (DemandCoverageService + UN_TO_MI_DIVISOR + projeção E1)
REUSE_DECISION: EXTEND — menor adaptador; sem segundo motor de cobertura.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping, Sequence

from production_control_app.domain.myweg_demand_source_contract import (
    DISPLAY_ORDER_MYWEG,
    SOURCE_MYWEG,
    WEG_LINHARES_CUSTOMER_CODE,
    WEG_LINHARES_CUSTOMER_STORE,
)
from production_control_app.domain.myweg_needs_contract import (
    UN_TO_MI_DIVISOR,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_demand_projection import (
    MyWegDemandProjectionLine,
)

ZERO = Decimal("0")
_QTY_QUANTIZE = Decimal("0.001")
COVERAGE_UNIT_MI = "MI"
SOURCE_PROTHEUS = "protheus"
OVERLAP_PENDING = "overlap_pending"
RECONCILIATION_BLOCKED = "reconciliation_blocked"
STOCK_WAREHOUSE_DEFAULT = "01"


def un_to_mi(quantity_un: Decimal | str | int | float) -> Decimal:
    """Conversão canônica UN → MI (divisor 1000)."""
    if isinstance(quantity_un, Decimal):
        qty = quantity_un
    else:
        qty = Decimal(str(quantity_un))
    return qty / UN_TO_MI_DIVISOR


def mi_to_float_for_coverage(quantity_mi: Decimal) -> float:
    """Fronteira Decimal → float do motor atual (3 casas, half-up)."""
    quantized = quantity_mi.quantize(_QTY_QUANTIZE, rounding=ROUND_HALF_UP)
    return float(quantized)


def is_linhares_open_order(item: Mapping[str, Any]) -> bool:
    code = str(item.get("codigo_cadastro") or item.get("codigo_cliente") or "").strip()
    store = str(item.get("loja_cadastro") or "").strip()
    return code == WEG_LINHARES_CUSTOMER_CODE and store == WEG_LINHARES_CUSTOMER_STORE


def order_unit(item: Mapping[str, Any]) -> str:
    return str(item.get("unidade") or "").strip().upper()


def is_unit_compatible_with_mi(unit: str) -> bool:
    """MI compatível; vazio herda comportamento legado da Demanda (sem unidade)."""
    if not unit:
        return True
    return unit == COVERAGE_UNIT_MI


def projection_to_coverage_input(
    line: MyWegDemandProjectionLine,
    *,
    product_stock_mi: float,
) -> dict[str, Any]:
    """Monta dict no shape esperado por DemandCoverageService._build_lines."""
    qty_mi = un_to_mi(line.open_quantity)
    saldo = mi_to_float_for_coverage(qty_mi)
    # Pedido exibido = MyWEG; chave técnica usa prefixo + record_id (não colide com SC5).
    return {
        "filial": line.branch,
        "pedido": DISPLAY_ORDER_MYWEG,
        "linha": line.record_id,
        "nome_cliente": line.customer_name,
        "codigo_cadastro": line.customer_code,
        "loja_cadastro": line.customer_store,
        "pedido_cliente": line.batch_id,
        "tipo_pedido": SOURCE_MYWEG,
        "tipo_entidade": "CLIENTE",
        "produto": line.product_code or "",
        "quantidade": saldo,
        "entregue": 0.0,
        "saldo": saldo,
        "data_entrega": line.due_date.isoformat(),
        "data_despacho": None,
        "no_estoque": float(product_stock_mi),
        "unidade": COVERAGE_UNIT_MI,
        # Metadados de auditoria (ignorados pelo motor; propagados na prévia).
        "_preview_source": SOURCE_MYWEG,
        "_preview_id": line.id,
        "_preview_batch_id": line.batch_id,
        "_preview_record_id": line.record_id,
        "_preview_quantity_un": decimal_to_canonical_str(line.open_quantity),
        "_preview_quantity_mi": decimal_to_canonical_str(qty_mi),
        "_preview_coverage_unit": COVERAGE_UNIT_MI,
    }


def classify_consolidation(
    *,
    protheus_items: Sequence[Mapping[str, Any]],
    myweg_eligible_products: set[str],
) -> dict[str, Any]:
    """Classifica linhas Protheus vs MyWEG sem somar sobreposições.

    - Demais clientes/lojas: entram no consolidado.
    - WEG Linhares (000001/09): se houver pedido aberto, marca overlap_pending e
      NÃO entra no consolidado definitivo (MyWEG é a previsão principal).
    - Unidade incompatível (ex.: PC): reconciliation_blocked para aquela linha.
    """
    keep: list[dict[str, Any]] = []
    overlap: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for raw in protheus_items:
        item = dict(raw)
        unit = order_unit(item)
        if not is_unit_compatible_with_mi(unit):
            item["_preview_source"] = RECONCILIATION_BLOCKED
            item["_preview_block_reason"] = f"unidade_incompativel:{unit or 'vazia'}"
            blocked.append(item)
            continue
        if is_linhares_open_order(item):
            product = str(item.get("produto") or "").strip()
            item["_preview_source"] = OVERLAP_PENDING
            item["_preview_overlap_product_in_myweg"] = product in myweg_eligible_products
            # Mesmo sem prova documental, não somamos Linhares Protheus + MyWEG.
            overlap.append(item)
            continue
        item["_preview_source"] = SOURCE_PROTHEUS
        keep.append(item)
    return {
        "protheus_for_coverage": keep,
        "overlap_pending": overlap,
        "reconciliation_blocked": blocked,
        "has_linhares_protheus_open": bool(overlap),
    }


def build_stock_pool_mi(
    *,
    branch: str,
    protheus_items: Sequence[Mapping[str, Any]],
    myweg_product_codes: Iterable[str],
    sb2_quantities: Mapping[str, float | None],
    sb2_complete: bool,
    sb2_error: str | None = None,
) -> dict[str, Any]:
    """Pool único (filial, produto) → estoque MI.

    Produtos da carteira: ``no_estoque`` (não soma SB2).
    Exclusivos MyWEG: SB2 armazém 01. Indisponibilidade ≠ zero silencioso.
    """
    pool: dict[tuple[str, str], float] = {}
    source: dict[tuple[str, str], str] = {}
    for item in protheus_items:
        if str(item.get("filial") or "").strip() != branch:
            continue
        product = str(item.get("produto") or "").strip()
        if not product:
            continue
        key = (branch, product)
        stock = float(item.get("no_estoque") or 0.0)
        if key not in pool or stock > pool[key]:
            pool[key] = max(stock, 0.0)
            source[key] = "no_estoque"

    missing_sb2: list[str] = []
    zero_confirmed: list[str] = []
    exclusive_codes = []
    for code in myweg_product_codes:
        product = str(code or "").strip()
        if not product:
            continue
        key = (branch, product)
        if key in pool:
            continue
        exclusive_codes.append(product)
        if sb2_error:
            missing_sb2.append(product)
            continue
        if product not in sb2_quantities:
            missing_sb2.append(product)
            continue
        raw = sb2_quantities[product]
        if raw is None:
            missing_sb2.append(product)
            continue
        qty = float(raw)
        pool[key] = max(qty, 0.0)
        source[key] = "sb2_warehouse_01"
        if qty <= 0:
            zero_confirmed.append(product)

    incomplete = bool(sb2_error) or (not sb2_complete and exclusive_codes) or bool(missing_sb2)
    return {
        "pool": pool,
        "source_by_product": {f"{b}|{p}": src for (b, p), src in source.items()},
        "exclusive_myweg_products": exclusive_codes,
        "missing_sb2_products": missing_sb2,
        "zero_confirmed_products": zero_confirmed,
        "sb2_complete": sb2_complete and not sb2_error,
        "sb2_error": sb2_error,
        "incomplete": incomplete,
        "unit": COVERAGE_UNIT_MI,
        "warehouse": STOCK_WAREHOUSE_DEFAULT,
    }


def apply_pool_stock_to_inputs(
    inputs: Sequence[Mapping[str, Any]],
    pool: Mapping[tuple[str, str], float],
    *,
    branch: str,
) -> list[dict[str, Any]]:
    """Garante o mesmo product_stock em todas as linhas do produto (FIFO do motor)."""
    out: list[dict[str, Any]] = []
    for raw in inputs:
        item = dict(raw)
        product = str(item.get("produto") or "").strip()
        item["no_estoque"] = float(pool.get((branch, product), 0.0))
        out.append(item)
    return out


def conservation_check(lines: Sequence[Any]) -> dict[str, Any]:
    """quantidade_demandada ≈ coberta_estoque + coberta_OP + descoberta."""
    demanded = Decimal("0")
    stock = Decimal("0")
    orders = Decimal("0")
    uncovered = Decimal("0")
    for line in lines:
        demanded += Decimal(str(getattr(line, "open_quantity", 0)))
        stock += Decimal(str(getattr(line, "allocated_stock", 0)))
        covered_op = sum(
            Decimal(str(item.get("quantity") or 0))
            for item in (getattr(line, "covering_orders", None) or [])
        )
        orders += covered_op
        uncovered += Decimal(str(getattr(line, "uncovered_quantity", 0)))
    allocated = stock + orders + uncovered
    delta = (demanded - allocated).copy_abs()
    # Motor atual arredonda a 3 casas por linha; tolera 0.002 por linha.
    tolerance = _QTY_QUANTIZE * max(len(lines), 1) * Decimal("2")
    return {
        "demanded": float(demanded),
        "covered_by_stock": float(stock),
        "covered_by_orders": float(orders),
        "uncovered": float(uncovered),
        "allocated_sum": float(allocated),
        "delta_abs": float(delta),
        "tolerance": float(tolerance),
        "ok": delta <= tolerance,
        "unit": COVERAGE_UNIT_MI,
    }
