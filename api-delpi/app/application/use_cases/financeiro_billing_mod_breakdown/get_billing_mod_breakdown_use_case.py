"""R09 billing × MOD breakdown — operational view (doc 141, DR-1/DR-2).

Assembles the proven DLP204 information chain set-based:

```
SD2/SF4 billed anchors (F4_DUPLIC='S', D2_EMISSAO)
  -> SG1 direct children per level (Estrut semantics)
  -> SG2 cadastral operations (roteiro '01')
  -> SH1010.H1_CCUSTO -> MOD* item
  -> line: level, product, operation, resource, stdTime,
     propagatedQty (own billed or anchor's), hours
  -> cost fields: typed `source_missing` (DR-2)
```

Proven rules (doc 85 §9, doc 141): levels ``02``/``04``/``06`` = PA /
direct component / subcomponent; ``Quantidade`` = ``G2_TEMPAD``;
``Horas`` = ``Qtd Fat.`` x ``Quantidade``; ``QTDFAT`` = own billed qty
of the line's product, falling back to the anchor's billed qty when the
product has no own billing in the competence.

Known gaps stay typed, never zeroed: MOD rate basis (SP
``STP_DELPI_FORMA_PRECO_*`` absent), frozen-OP ``HY_TEMPAD`` routes and
unmapped ``resource -> MOD`` bridges.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.application.dto.financeiro_billing_mod_breakdown.billing_mod_breakdown_request import (
    BillingModBreakdownRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.domain.ports.financeiro_billing_mod_breakdown.billing_mod_breakdown_repository_port import (
    BillingModBreakdownRepositoryPort,
)

REPORT_BILLING_MOD_BREAKDOWN = "billing-mod-breakdown"

LEVEL_PA = "02"          # billed PA anchor (SP level marker '0')
LEVEL_COMPONENT = "04"   # direct SG1 component (SP level marker '1')
LEVEL_SUBCOMPONENT = "06"  # second-level component (SP level marker '2')

SOURCE_MISSING_COST_RATE = "cost_rate_basis"

_COST_NODE = {
    "value": None,
    "state": "source_missing",
    "reason": "cost_rate_basis_unavailable",
    "detail": (
        "Taxa de MOD sem fonte comprovada: SP STP_DELPI_FORMA_PRECO_* "
        "ausente dos bancos acessíveis (E9). DR-2: ausência tipada, "
        "nunca zero nem valor inferido."
    ),
}

_LIMITATIONS = (
    "SP STP_DELPI_FORMA_PRECO_<empresa> ausente do catálogo produtivo — "
    "motor interno do DLP204 reconstruído por engenharia reversa (E9).",
    "Base da taxa de MOD não comprovada: costUnit/costTotal ausentes "
    "tipados (DR-2). BZ_CUSTD as_of é candidato documentado (BR-R09-010) "
    "pendente de homologação — não calculado neste slice.",
    "Tempo padrão do roteiro congelado da OP mais recente existente na "
    "data de execução (HY_TEMPAD, BR-R09-007/008 — fonte primária "
    "comprovada) com fallback para o roteiro cadastral SG2 ('01') "
    "quando o produto não tem OP com roteiro.",
    "Semântica do divisor ÷C2_QUANT em desdobramentos: pendente (E9) — "
    "linhas afetadas compõem divergência conhecida, não cálculo inventado.",
    "Paridade oficial com DLP204: PENDING — homologação informacional "
    "item a item com a Controladoria permanece obrigatória (DR-3).",
)


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _typed_number(value: float | None, *, state: str) -> dict[str, Any]:
    if value is None:
        return {"value": None, "state": state}
    return {"value": value, "state": state}


class GetBillingModBreakdownUseCase:
    def __init__(
        self,
        repository: BillingModBreakdownRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: BillingModBreakdownRequest,
        *,
        user_subject: str | None,
        run_date: str | None = None,
    ) -> dict:
        require_stock_inventory_scope(
            self._scope_resolver, user_subject=user_subject
        )
        # Latest OP existing at run date — the DLP204 semantic ("the
        # OP current when the report ran"). Defaults to today; the
        # parity probe passes the artifact's generation date.
        self._run_date = run_date or datetime.now(
            timezone.utc
        ).strftime("%Y%m%d")

        anchors: list[dict[str, Any]] = []
        limitations = list(_LIMITATIONS)

        for branch in request.requested_branches():
            billed = self._billed_map(request, branch)
            anchors.extend(
                self._build_branch_anchors(branch, billed)
            )

        return {
            "report": REPORT_BILLING_MOD_BREAKDOWN,
            "reportId": "R09",
            "period": request.period,
            "branch": request.branch,
            "officiality": "operational_view",
            "officialParity": "pending",
            "observedAt": datetime.now(timezone.utc).isoformat(),
            "anchors": anchors,
            "limitations": limitations,
            "provenance": {
                "officialProducer": "DLP204.prw + STP_DELPI_FORMA_PRECO_<empresa>",
                "engine": "api-delpi/billing-mod-breakdown (slice 1)",
                "selection": {
                    "axis": "D2_EMISSAO",
                    "tesRule": "SF4.F4_DUPLIC='S'",
                    "qtdFatRule": "SUM(D2_QUANT) com D2_TIPO<>'D'",
                    "structure": "SG1010 filial própria, vigência corrente",
                    "route": "SG2010 roteiro '01' (MV_PAR09 default)",
                    "modBridge": "SH1010.H1_CCUSTO -> SB1010 MOD*",
                },
                "evidence": (
                    "doc 85 §9 BR-R09-001..013; doc 141 G039; "
                    "PRW literal fGetProds/Estrut/fGPrdMod"
                ),
                "spInternal": "SOURCE_MISSING_WITH_SEARCH_SCOPE (E9)",
            },
        }

    # -- data assembly -----------------------------------------------------

    def _billed_map(
        self, request: BillingModBreakdownRequest, branch: str
    ) -> dict[str, float]:
        rows = self._repository.fetch_billed_quantities(
            period_start=request.period_start(),
            period_end=request.period_end(),
            branch=branch,
        )
        return {
            str(r["product_code"]).strip(): _num(r.get("billed_qty")) or 0.0
            for r in rows
            if r.get("has_billing")
        }

    def _build_branch_anchors(
        self, branch: str, billed: dict[str, float]
    ) -> list[dict[str, Any]]:
        """Set-based prefetch for the whole branch — the same queries
        as before but executed ONCE for all anchors instead of once
        per anchor (~299× refetch). Proven: DB time ~20s vs 200s+ of
        per-anchor round-trips (Gate 049 profile)."""
        level1_all = self._edges(list(billed), branch)
        edges_by_parent: dict[str, list[dict]] = {}
        for edge in level1_all:
            edges_by_parent.setdefault(
                str(edge["parent_code"]).strip(), []
            ).append(edge)

        level1_parents = sorted(
            {e["component_code"] for e in level1_all}
        )
        level2_all = self._edges(level1_parents, branch)
        level2_by_parent: dict[str, list[dict]] = {}
        for edge in level2_all:
            level2_by_parent.setdefault(
                str(edge["parent_code"]).strip(), []
            ).append(edge)

        tree_products = set(billed)
        tree_products.update(e["component_code"] for e in level1_all)
        tree_products.update(e["component_code"] for e in level2_all)
        operations = self._operations(
            sorted(tree_products), branch
        )

        return [
            self._build_anchor(
                branch,
                product,
                billed,
                edges_by_parent,
                level2_by_parent,
                operations,
            )
            for product in sorted(billed)
        ]

    def _build_anchor(
        self,
        branch: str,
        product: str,
        billed: dict[str, float],
        edges_by_parent: dict[str, list[dict]],
        level2_by_parent: dict[str, list[dict]],
        operations: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        anchor_qty = billed[product]
        level1_edges = edges_by_parent.get(product, [])
        level2_edges = [
            edge
            for level1 in level1_edges
            for edge in level2_by_parent.get(
                str(level1["component_code"]).strip(), []
            )
        ]

        lines: list[dict[str, Any]] = []
        unresolved_products: list[str] = []
        unmapped: list[dict[str, str]] = []

        lines.extend(
            self._lines_for_product(
                product, LEVEL_PA, product, anchor_qty, billed,
                operations, unresolved_products, unmapped,
            )
        )
        for edge in level1_edges:
            lines.extend(
                self._lines_for_product(
                    product, LEVEL_COMPONENT, edge["component_code"],
                    anchor_qty, billed, operations,
                    unresolved_products, unmapped,
                )
            )
        for edge in level2_edges:
            lines.extend(
                self._lines_for_product(
                    product, LEVEL_SUBCOMPONENT, edge["component_code"],
                    anchor_qty, billed, operations,
                    unresolved_products, unmapped,
                )
            )

        source_missing = [SOURCE_MISSING_COST_RATE]
        if unresolved_products:
            source_missing.append("route_operations_missing")
        if unmapped:
            source_missing.append("resource_mod_bridge_unmapped")

        return {
            "product": product,
            "branch": branch,
            "billedQty": anchor_qty,
            "modLines": lines,
            "sourceMissing": sorted(set(source_missing)),
            "diagnostics": {
                "productsWithoutRouteOperations": sorted(
                    set(unresolved_products)
                ),
                "unmappedResourceMod": unmapped,
            },
        }

    def _lines_for_product(
        self,
        anchor: str,
        level: str,
        exploded_product: str,
        anchor_qty: float,
        billed: dict[str, float],
        operations: dict[str, list[dict[str, Any]]],
        unresolved_products: list[str],
        unmapped: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        ops = operations.get(exploded_product)
        if not ops:
            unresolved_products.append(exploded_product)
            return []

        own_qty = billed.get(exploded_product)
        propagated = (
            own_qty
            if own_qty is not None and own_qty > 0
            else anchor_qty
        )

        lines: list[dict[str, Any]] = []
        for op in ops:
            if op.get("mod_item") is None:
                # Artifact grain is MOD lines only — unmapped operations
                # stay visible in diagnostics, never as invented items.
                unmapped.append(
                    {
                        "product": exploded_product,
                        "operation": str(op.get("operation") or ""),
                        "resource": str(op.get("resource") or ""),
                        "stdTime": _num(op.get("std_time")),
                    }
                )
                continue
            std_time = _num(op.get("std_time"))
            hours = (
                propagated * std_time if std_time is not None else None
            )
            lines.append(
                {
                    "level": level,
                    "anchorProduct": anchor,
                    "explodedProduct": exploded_product,
                    "modItem": op.get("mod_item"),
                    "modDescription": op.get("mod_description"),
                    "unit": op.get("mod_unit"),
                    "operation": op.get("operation"),
                    "operationDescription": op.get(
                        "operation_description"
                    ),
                    "resource": op.get("resource"),
                    "stdTime": _typed_number(
                        std_time, state=op["std_time_source"]
                    ),
                    "sourceOp": op.get("op_code"),
                    "propagatedQty": propagated,
                    "hours": _typed_number(
                        hours,
                        state=(
                            "computed"
                            if hours is not None
                            else "source_missing"
                        ),
                    ),
                    "costUnit": dict(_COST_NODE),
                    "costTotal": dict(_COST_NODE),
                    "modItemState": "mapped",
                }
            )
        return lines

    def _edges(
        self, parent_codes: list[str], branch: str
    ) -> list[dict[str, Any]]:
        """Direct SG1 children — Estrut dedup on (parent, component, trt)."""
        if not parent_codes:
            return []
        rows = self._repository.fetch_structure_edges(
            parent_codes=sorted(set(parent_codes)), branch=branch
        )
        seen: set[tuple[str, str, str]] = set()
        edges: list[dict[str, Any]] = []
        for row in rows:
            parent = str(row["parent_code"]).strip()
            component = str(row["component_code"]).strip()
            seq = str(row.get("component_seq") or "").strip()
            qty = _num(row.get("quantity_per_unit"))
            if not component or component == parent:
                continue  # Estrut skips self-referencing components
            if qty is None or qty <= 0:
                continue  # ExplEstr > 0 guard
            key = (parent, component, seq)
            if key in seen:
                continue
            seen.add(key)
            edges.append({"parent_code": parent, "component_code": component})
        return edges

    def _operations(
        self, product_codes: list[str], branch: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Ops per product — frozen-OP route (SHY) is the proven primary
        source (~96% of artifact lines, BR-R09-007/008); cadastral SG2
        is the fallback for products without an OP carrying a route."""
        if not product_codes:
            return {}
        frozen = self._op_rows(
            self._repository.fetch_frozen_route_ops(
                product_codes=product_codes,
                branch=branch,
                run_date=self._run_date,
            ),
            source="shy_frozen_op",
        )
        cadastral = self._op_rows(
            self._repository.fetch_route_operations(
                product_codes=product_codes, branch=branch
            ),
            source="sg2_cadastral",
        )
        operations: dict[str, list[dict[str, Any]]] = {}
        for product, rows in cadastral.items():
            operations.setdefault(product, []).extend(rows)
        for product, rows in frozen.items():
            operations[product] = rows  # SHY route wins over cadastral
        return operations

    @staticmethod
    def _op_rows(rows, *, source: str):
        operations: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            product = str(row["product_code"]).strip()
            operations.setdefault(product, []).append(
                {
                    "operation": row.get("operation"),
                    "operation_description": row.get(
                        "operation_description"
                    ),
                    "resource": row.get("resource"),
                    "std_time": row.get("std_time"),
                    "std_time_source": source,
                    "op_code": row.get("op_code"),
                    "mod_item": row.get("mod_item"),
                    "mod_description": row.get("mod_description"),
                    "mod_unit": row.get("mod_unit"),
                }
            )
        return operations
