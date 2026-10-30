"""Shared R06/R07 engine — one MATR910 movement universe, all surfaces.

Single rule implementation (doc 122 §4-§5): the query, the summaries,
the product drill, the inventory-adjustments view and the exports all
consume the SAME processed population — classification (TES<=500 with
the devolution inversion), as-of cost resolution (TTAT_OLD), opening
balances (previous month-end SB9) and running balances are computed
once, here.

Classification proven in ``matr910_dlp.prx`` (Section3 Print, L1040+):
- SD1: entrada when ``TES <= '500'`` and not a sales return; otherwise
  saída — a return prints in the saída column with a negative value and
  the balance ADDS the movement back;
- SD2: saída when ``TES > '500'``; ``TES <= '500'`` or a purchase return
  prints in the entrada column — a return prints negative and the
  balance SUBTRACTS the movement;
- SD3: ``TM <= '500'`` → entrada, otherwise saída (``lInverteMov`` is
  .F. in the source).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    STATUS_AVAILABLE,
    STATUS_INCOMPLETE,
    STATUS_NO_MATCHING_ITEMS,
    STATUS_SOURCE_MISSING,
)
from app.application.dto.financeiro_stock_kardex.constantes import (
    COST_AS_OF_CURRENT,
    COST_AS_OF_TTAT,
    MOVEMENT_KIND_ENTRY,
    MOVEMENT_KIND_OUTPUT,
)
from app.application.dto.financeiro_stock_kardex.stock_kardex_request import (
    StockKardexQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.domain.ports.financeiro_stock_kardex.stock_kardex_repository_port import (
    StockKardexRepositoryPort,
)

REPORT_STOCK_KARDEX = "stock-kardex"
REPORT_INVENTORY_ADJUSTMENTS = "inventory-adjustments"
R06_ENGINE_ID = "minha-delpi-r06-kardex-engine"
R06_OFFICIAL_PRODUCER = "matr910"


def report_name(document_kind: str) -> str:
    """R07 is the dedicated ``inventory-adjustments`` contract over the
    same engine — the report tag follows the document-kind selection."""
    return (
        REPORT_INVENTORY_ADJUSTMENTS
        if document_kind == "invent"
        else REPORT_STOCK_KARDEX
    )

PARITY_NOTE_R06 = (
    "Motor R06 com a seleção e a classificação MATR910 comprovadas "
    "contra o artefato histórico 09/2026 (cpv matriz); custos exibidos "
    "na convenção as_of (TTAT_OLD quando o custo foi retificado após o "
    "fechamento); paridade por competência pendente de homologação "
    "contra nova emissão oficial."
)

PARITY_NOTE_R07 = (
    "Motor R07 = recorte MATR910 D3_DOC='INVENT' comprovado contra o "
    "artefato histórico Invent.xlsb 09/2026 (45 movimentos, armazéns "
    "01/99 da filial 02); paridade por competência pendente de "
    "homologação contra nova emissão oficial."
)

_ZERO = Decimal("0")
_Q6 = Decimal("0.000001")


def _dec(value) -> Decimal:
    if value is None or value == "":
        return _ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _ZERO


def _dec_or_none(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def str6(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value.quantize(_Q6))


def classify_movement(
    source_table: str, tm: str, is_return: bool
) -> tuple[str, int]:
    """MATR910 printed-column rule.

    Returns ``(movement_kind, display_sign)`` — ``display_sign`` is -1
    only for devolution lines (negative print in the printed column).
    """
    tm_key = (tm or "").strip()
    if source_table == "SD3":
        return (
            (MOVEMENT_KIND_ENTRY, 1)
            if tm_key <= "500"
            else (MOVEMENT_KIND_OUTPUT, 1)
        )
    if source_table == "SD1":
        if is_return:
            return MOVEMENT_KIND_OUTPUT, -1
        return (
            (MOVEMENT_KIND_ENTRY, 1)
            if tm_key <= "500"
            else (MOVEMENT_KIND_OUTPUT, 1)
        )
    # SD2 — purchase returns print in the entrada column, negative.
    if is_return:
        return MOVEMENT_KIND_ENTRY, -1
    return (
        (MOVEMENT_KIND_ENTRY, 1)
        if tm_key <= "500"
        else (MOVEMENT_KIND_OUTPUT, 1)
    )


def build_reference(row: dict[str, Any]) -> str | None:
    """REF column decode (matr910_dlp.prx L1280+):
    SD1 ``F-<supplier>``, SD2 ``P-<order>``, SD3 ``PJ<project>`` /
    ``OP<op>`` / ``CC<cc>``."""
    source = row.get("source_table")
    if source == "SD1":
        partner = (row.get("partner_code") or "").strip()
        return f"F-{partner}" if partner else None
    if source == "SD2":
        order = (row.get("order_number") or "").strip()
        return f"P-{order}" if order else None
    if source == "SD3":
        project = (row.get("project_code") or "").strip()
        if project:
            return f"PJ{project}"
        op = (row.get("production_order") or "").strip()
        if op:
            return f"OP{op}"
        cc = (row.get("cost_center") or "").strip()
        if cc:
            return f"CC{cc}"
    return None


@dataclass(slots=True)
class ProcessedMovement:
    raw: dict[str, Any]
    movement_kind: str
    entry_quantity: Decimal
    entry_value: Decimal
    output_quantity: Decimal
    output_value: Decimal
    signed_quantity: Decimal
    signed_value: Decimal
    unit_cost: Decimal | None
    cost_as_of_source: str
    running_quantity: Decimal | None = None
    running_value: Decimal | None = None


@dataclass(slots=True)
class KardexUniverse:
    """The processed MATR910 population for one authorized request."""

    request: StockKardexQueryRequest
    status: str
    branches_available: list[str]
    branches_missing: list[str]
    movements: list[ProcessedMovement] = field(default_factory=list)
    blocks: dict[tuple[str, str, str], dict[str, Any]] = field(
        default_factory=dict
    )
    opening_snapshot_present: bool = False
    ttat_applied_count: int = 0

    def totals(self) -> dict[str, Any]:
        movement_count = len(self.movements)
        entry_q = sum(m.entry_quantity for m in self.movements)
        entry_v = sum(m.entry_value for m in self.movements)
        output_q = sum(m.output_quantity for m in self.movements)
        output_v = sum(m.output_value for m in self.movements)
        opening_v: Decimal | None = None
        closing_v: Decimal | None = None
        if self.opening_snapshot_present:
            opening_v = sum(
                _dec(block.get("opening_value"))
                for block in self.blocks.values()
            )
            closing_v = opening_v + entry_v - output_v
        return {
            "movementCount": movement_count,
            "blockCount": len(self.blocks),
            "entryQuantity": entry_q,
            "entryValue": entry_v,
            "outputQuantity": output_q,
            "outputValue": output_v,
            "netQuantity": entry_q - output_q,
            "netValue": entry_v - output_v,
            "openingValue": opening_v,
            "closingValue": closing_v,
        }


def load_kardex_universe(
    *,
    repository: StockKardexRepositoryPort,
    scope_resolver: StockInventoryScopeResolver,
    request: StockKardexQueryRequest,
    user_subject: str | None,
) -> KardexUniverse:
    """Authorize, fetch and process the full MATR910 population."""
    require_stock_inventory_scope(
        scope_resolver, user_subject=user_subject
    )

    opening_date = request.opening_snapshot_date()
    branches = request.requested_branches()
    warehouses = request.requested_warehouses()

    presence = repository.snapshot_branch_counts(
        snapshot_date=opening_date, branches=branches
    )
    available = [code for code in branches if presence.get(code, 0) > 0]
    missing = [code for code in branches if code not in available]

    universe = KardexUniverse(
        request=request,
        status=STATUS_AVAILABLE,
        branches_available=available,
        branches_missing=missing,
        opening_snapshot_present=bool(available),
    )
    if not available:
        universe.status = STATUS_SOURCE_MISSING
        return universe

    rows = repository.fetch_movements(
        period_start=request.period_start(),
        period_end=request.reference_date(),
        branches=branches,
        warehouses=warehouses,
        product_code=request.product_code,
        product_type=request.product_type,
        document_kind=request.document_kind,
    )
    if not rows:
        universe.status = (
            STATUS_INCOMPLETE if missing else STATUS_NO_MATCHING_ITEMS
        )
        return universe
    if missing:
        universe.status = STATUS_INCOMPLETE

    # --- As-of cost resolution (doc 122 §5.2): table-specific TTAT log
    # — the earliest COLD value logged after the competence boundary is
    # the cost the field carried at the boundary.
    boundary = request.reference_date()
    cost_history: dict[tuple[str, int], Decimal] = {}
    recnos_by_table: dict[str, list[int]] = {}
    for row in rows:
        source = str(row.get("source_table") or "")
        recno = int(row.get("movement_id") or 0)
        recnos_by_table.setdefault(source, []).append(recno)
    for source, recnos in recnos_by_table.items():
        history = repository.fetch_cost_history(
            source_table=source,
            boundary=boundary,
            recnos=tuple(sorted(set(recnos))),
        )
        for recno, cold in history.items():
            value = _dec_or_none(cold)
            if value is not None:
                cost_history[(source, recno)] = value

    # --- Opening balances for the product population (SB9 @ prev month)
    product_codes = tuple(
        sorted({str(row.get("product_code") or "") for row in rows})
    )
    openings = repository.fetch_opening_balances(
        snapshot_date=opening_date,
        branches=branches,
        product_codes=product_codes,
        warehouses=warehouses,
    )

    # --- Process each line: classify, apply as-of cost, resolve REF.
    running: dict[tuple[str, str, str], list[Decimal | None]] = {}
    for row in rows:
        source = str(row.get("source_table") or "")
        recno = int(row.get("movement_id") or 0)
        tm = str(row.get("tm") or "")
        is_return = bool(row.get("is_return"))
        kind, sign = classify_movement(source, tm, is_return)

        quantity = _dec(row.get("quantity"))
        cost_key = (source, recno)
        if cost_key in cost_history:
            total_cost = cost_history[cost_key]
            cost_source = COST_AS_OF_TTAT
            universe.ttat_applied_count += 1
        else:
            total_cost = _dec(row.get("total_cost"))
            cost_source = COST_AS_OF_CURRENT

        unit_cost = (
            total_cost / quantity if quantity != _ZERO else None
        )

        entry_q = quantity * sign if kind == MOVEMENT_KIND_ENTRY else _ZERO
        entry_v = total_cost * sign if kind == MOVEMENT_KIND_ENTRY else _ZERO
        output_q = (
            quantity * sign if kind == MOVEMENT_KIND_OUTPUT else _ZERO
        )
        output_v = (
            total_cost * sign if kind == MOVEMENT_KIND_OUTPUT else _ZERO
        )

        movement = ProcessedMovement(
            raw=row,
            movement_kind=kind,
            entry_quantity=entry_q,
            entry_value=entry_v,
            output_quantity=output_q,
            output_value=output_v,
            signed_quantity=entry_q - output_q,
            signed_value=entry_v - output_v,
            unit_cost=unit_cost,
            cost_as_of_source=cost_source,
        )
        universe.movements.append(movement)

        key = (
            str(row.get("branch_code") or ""),
            str(row.get("warehouse") or ""),
            str(row.get("product_code") or ""),
        )
        if key not in universe.blocks:
            opening = openings.get(key)
            universe.blocks[key] = {
                "product_code": key[2],
                "description": row.get("description"),
                "product_type": row.get("product_type"),
                "unit": row.get("unit"),
                "branch_code": key[0],
                "warehouse": key[1],
                "opening_quantity": (
                    _dec(opening.get("opening_quantity"))
                    if opening
                    else _ZERO
                ),
                "opening_value": (
                    _dec(opening.get("opening_value")) if opening else _ZERO
                ),
                "has_opening_snapshot": opening is not None,
                "entry_quantity": _ZERO,
                "entry_value": _ZERO,
                "output_quantity": _ZERO,
                "output_value": _ZERO,
                "movement_count": 0,
            }
        block = universe.blocks[key]
        block["entry_quantity"] += entry_q
        block["entry_value"] += entry_v
        block["output_quantity"] += output_q
        block["output_value"] += output_v
        block["movement_count"] += 1

        # Rows arrive ordered (branch, product, warehouse, date, seq,
        # recno) — iterate in fetch order so the running balance follows
        # the printed chain.
        acc = running.setdefault(
            key,
            [
                _dec(
                    openings.get(key, {}).get("opening_quantity")
                ),
                _dec(openings.get(key, {}).get("opening_value")),
            ],
        )
        acc[0] = (acc[0] or _ZERO) + movement.signed_quantity
        acc[1] = (acc[1] or _ZERO) + movement.signed_value
        movement.running_quantity = acc[0]
        movement.running_value = acc[1]

    return universe
