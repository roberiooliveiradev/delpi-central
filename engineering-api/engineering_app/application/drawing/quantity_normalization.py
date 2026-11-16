"""Normalização governada de quantidade BOM × desenho (E1/VAL-01 RQ07).

Base oficial: api-delpi playbook-conversao-unidades-protheus.md —
PA com ``B1_UM = MI`` → ``1 MI = 1000 peças`` no contexto produtivo.
Fora dessa base declarada, consumo BOM e quantidade de montagem do
desenho permanecem ``NOT_COMPARABLE`` — sem regra inventada.

Semântica da coluna QTD do desenho (família flat_component_table,
evidência ExcelStructureBuilder): ``PC`` com consumo múltiplo de
1000 exibe ``qty/1000``; demais unidades exibem ``1`` (ocorrência,
não medida). ``QTD=1`` nunca é interpretado como 1 metro.
"""

from __future__ import annotations

from typing import Any

MI_PIECES_BASIS = 1000
_BASIS_SOURCE = (
    "api-delpi/docs/api/padroes-totvs/playbooks/"
    "playbook-conversao-unidades-protheus.md §2 (1 MI = 1000 peças)"
)

# Unidades cujo consumo BOM pode ser reduzido por peça sob base MI.
_SUPPORTED_BOM_UNITS = {"MT", "PC", "UN"}


def normalize_bom_consumption(
    quantity: Any,
    unit: str | None,
    *,
    pa_unit: str | None,
) -> dict[str, Any]:
    """Normaliza consumo oficial para ``por peça de PA``.

    Retorna sempre o registro completo (status, fórmula, base,
    fonte) — mesmo quando não comparável, a normalização é
    evidência, não conclusão.
    """
    unit_norm = str(unit or "").strip().upper() or None
    pa_norm = str(pa_unit or "").strip().upper() or None
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        qty = None
    record: dict[str, Any] = {
        "status": "NOT_COMPARABLE",
        "basis_source": _BASIS_SOURCE,
        "quantity_raw": quantity,
        "unit_raw": unit_norm,
        "pa_unit": pa_norm,
    }
    if qty is None or unit_norm is None:
        record["limitation"] = "quantidade ou unidade oficial ausente"
        return record
    if pa_norm != "MI":
        record["limitation"] = (
            f"base produtiva do PA '{pa_norm or 'desconhecida'}' não "
            "ratificada — sem conversão aprovada"
        )
        return record
    if unit_norm not in _SUPPORTED_BOM_UNITS:
        record["limitation"] = (
            f"unidade de consumo '{unit_norm}' sem regra de "
            "normalização aprovada"
        )
        return record
    per_piece = qty / MI_PIECES_BASIS
    record.update(
        {
            "status": "NORMALIZED",
            "basis": MI_PIECES_BASIS,
            "value_per_piece": per_piece,
            "unit_per_piece": unit_norm,
            "formula": f"{qty:g} {unit_norm} / {MI_PIECES_BASIS} (MI)",
        }
    )
    if unit_norm == "MT":
        record["value_per_piece_mm"] = per_piece * 1000.0
        record["formula_mm"] = (
            f"{qty:g} MT / {MI_PIECES_BASIS} = "
            f"{per_piece:g} m = {per_piece * 1000.0:g} mm por peça"
        )
    return record


def compare_quantity(
    *,
    drawing_quantity: Any,
    drawing_unit: str | None,
    normalization: dict[str, Any],
) -> dict[str, Any]:
    """Compara QTD do desenho ao consumo normalizado quando a
    semântica é comprovadamente a mesma (peça contra peça).

    ``drawing_unit='PC'`` + consumo normalizado em ``PC`` é o único
    par comparável aprovado; qualquer outra combinação é
    ``NOT_COMPARABLE`` com a razão declarada — ``QTD=1`` de cabo é
    ocorrência, não metro.
    """
    if normalization.get("status") != "NORMALIZED":
        return {
            "result": "NOT_COMPARABLE",
            "reason": normalization.get("limitation")
            or "consumo oficial não normalizado",
        }
    unit_per_piece = normalization.get("unit_per_piece")
    draw_unit = str(drawing_unit or "").strip().upper() or None
    try:
        draw_qty = float(drawing_quantity)
    except (TypeError, ValueError):
        draw_qty = None
    if draw_qty is None:
        return {
            "result": "NOT_COMPARABLE",
            "reason": "quantidade do desenho não extraída ou inválida",
        }
    if draw_unit != "PC" or unit_per_piece not in {"PC", "UN"}:
        return {
            "result": "NOT_COMPARABLE",
            "reason": (
                "semânticas não comprovadamente iguais: desenho "
                f"'{draw_unit or 'desconhecida'}' × consumo "
                f"'{unit_per_piece}' — QTD do desenho pode ser "
                "ocorrência, não medida"
            ),
        }
    expected = float(normalization["value_per_piece"])
    return {
        "result": (
            "MATCH_CANDIDATE" if abs(draw_qty - expected) < 1e-9
            else "CONFLICT_CANDIDATE"
        ),
        "drawing_quantity": draw_qty,
        "normalized_expected": expected,
        "unit": "PC",
        "formula": normalization.get("formula"),
        "basis_source": normalization.get("basis_source"),
    }
