"""Prévia / integração MyWEG × Demanda — motor DemandCoverageService.

E2: prévia operacional (CLI). E3: ``resolve_demand_origin_lines`` alimenta
``GET /demand`` com origem myweg|both. Consolidação oficial permanece
``ARCHITECTURE_DECISION_REQUIRED`` (sem total agregado definitivo).
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any

from production_control_app.application.services.demand_service import DemandService
from production_control_app.application.services.myweg_demand_source_service import (
    MyWegDemandSourceService,
)
from production_control_app.core.security import (
    PC_ACCESS,
    PC_DEMAND_VIEW,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_02,
    can,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
)
from production_control_app.domain.myweg_demand_source_contract import (
    DEMAND_SOURCE_BRANCH,
    DISPLAY_ORDER_MYWEG,
    SOURCE_MYWEG,
    WEG_LINHARES_CUSTOMER_CODE,
    WEG_LINHARES_CUSTOMER_STORE,
)
from production_control_app.domain.myweg_needs_contract import FORBIDDEN_BRANCH
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)
from production_control_app.domain.services.demand_coverage_service import (
    DemandCoverageService,
    DemandLine,
)
from production_control_app.domain.services.myweg_demand_coverage_adapter import (
    COVERAGE_UNIT_MI,
    CUSTOMER_IDENTITY_PENDING,
    OP_UNIT_UNVERIFIED,
    OVERLAP_PENDING,
    RECONCILIATION_BLOCKED,
    SOURCE_PROTHEUS,
    STOCK_WAREHOUSE_DEFAULT,
    apply_pool_stock_to_inputs,
    build_stock_pool_mi,
    classify_consolidation,
    conservation_check,
    projection_to_coverage_input,
    normalize_myweg_open_ops,
    summarize_units,
)


class PreviewPayloadError(DelpiGatewayError):
    """Payload de fonte com shape inválido ou incompleto (≠ lista vazia legítima)."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _finite_number(value: Any) -> float | None:
    try:
        qty = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(qty):
        return None
    return qty


def require_items_list(payload: Any, key: str, *, source_name: str) -> list[Any]:
    """Exige shape ``{data:{items:[...]}}`` ou ``{items:[...]}``. Lista vazia é válida."""
    if not isinstance(payload, dict):
        raise PreviewPayloadError(
            f"Resposta inválida de {source_name}: envelope não é objeto."
        )
    data = payload.get("data")
    source = data if isinstance(data, dict) else payload
    if not isinstance(source, dict):
        raise PreviewPayloadError(
            f"Resposta inválida de {source_name}: data não é objeto."
        )
    if key not in source:
        raise PreviewPayloadError(
            f"Resposta inválida de {source_name}: chave {key!r} ausente."
        )
    items = source.get(key)
    if not isinstance(items, list):
        raise PreviewPayloadError(
            f"Resposta inválida de {source_name}: {key!r} não é lista."
        )
    return items


def _pagination_meta(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    source = data if isinstance(data, dict) else payload
    if not isinstance(source, dict):
        return {}
    pagination = source.get("pagination")
    return pagination if isinstance(pagination, dict) else {}


class MyWegDemandCoveragePreviewService:
    """Orquestra prévia somente leitura; productive_activation_blocked=True."""

    STOCK_PAGE_SIZE = 500
    STOCK_MAX_PAGES = 40

    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        myweg_source: MyWegDemandSourceService,
        coverage: DemandCoverageService | None = None,
        demand_presenter: DemandService | None = None,
        today: date | None = None,
    ) -> None:
        self._gateway = gateway
        self._myweg_source = myweg_source
        self._today = today
        self._coverage = coverage or DemandCoverageService(today=today)
        self._presenter = demand_presenter or DemandService(
            gateway, today=today, coverage=self._coverage
        )

    def build_preview(
        self,
        user: object | None,
        *,
        branch: str = DEMAND_SOURCE_BRANCH,
        warehouse: str = STOCK_WAREHOUSE_DEFAULT,
    ) -> dict[str, Any]:
        code = _text(branch)
        if code == FORBIDDEN_BRANCH:
            raise InvalidBranch("Prévia MyWEG Demanda não se aplica à filial 01.")
        if code != DEMAND_SOURCE_BRANCH:
            raise InvalidBranch(f"Filial inválida para prévia MyWEG Demanda: {branch!r}.")
        warehouse_code = _text(warehouse) or STOCK_WAREHOUSE_DEFAULT
        if warehouse_code != STOCK_WAREHOUSE_DEFAULT:
            raise InvalidBranch(
                f"Armazém {warehouse_code!r} não homologado nesta prévia (somente 01)."
            )
        self._assert_authorized(user)

        batch_meta, projected = self._myweg_source.project_latest_lines(user, branch=code)

        eligible = [line for line in projected if line.coverage_eligible and line.product_code]
        pending_identity = [line for line in projected if not line.coverage_eligible]

        source_errors: list[str] = []
        sales_all: list[dict[str, Any]] = []
        ops_all: list[dict[str, Any]] = []
        try:
            sales_payload = self._gateway.fetch_open_sales_orders()
            sales_raw = require_items_list(
                sales_payload, "items", source_name="open_sales_orders"
            )
            sales_all = [item for item in sales_raw if isinstance(item, dict)]
        except PreviewPayloadError as exc:
            source_errors.append(str(exc))
        except DelpiGatewayError as exc:
            source_errors.append(f"open_sales_orders:{exc}")
        except Exception as exc:  # noqa: BLE001
            source_errors.append(f"open_sales_orders:falha_comunicacao:{type(exc).__name__}")

        try:
            ops_payload = self._gateway.fetch_open_production_orders()
            ops_raw = require_items_list(
                ops_payload, "items", source_name="open_production_orders"
            )
            ops_all = [item for item in ops_raw if isinstance(item, dict)]
        except PreviewPayloadError as exc:
            source_errors.append(str(exc))
        except DelpiGatewayError as exc:
            source_errors.append(f"open_production_orders:{exc}")
        except Exception as exc:  # noqa: BLE001
            source_errors.append(
                f"open_production_orders:falha_comunicacao:{type(exc).__name__}"
            )

        if source_errors:
            return self._blocked_preview(
                branch=code,
                warehouse=warehouse_code,
                batch_meta=batch_meta,
                pending_identity=pending_identity,
                source_errors=source_errors,
                reason="source_read_failed",
            )

        sales_branch = [item for item in sales_all if _text(item.get("filial")) == code]
        protheus_units = summarize_units(sales_branch)

        myweg_products = {line.product_code for line in eligible if line.product_code}
        consolidation = classify_consolidation(
            protheus_items=sales_branch,
            myweg_eligible_products=myweg_products,
        )

        exclusive = sorted(
            code_p
            for code_p in myweg_products
            if not any(
                _text(item.get("produto")) == code_p and _text(item.get("filial")) == code
                for item in consolidation["protheus_for_coverage"]
            )
        )
        sb2_map, sb2_meta = self._fetch_sb2_stock(
            branch=code, warehouse=warehouse_code, product_codes=exclusive
        )
        stock = build_stock_pool_mi(
            branch=code,
            protheus_items=consolidation["protheus_for_coverage"]
            + consolidation["overlap_pending"],
            myweg_product_codes=myweg_products,
            sb2_quantities=sb2_map,
            sb2_complete=bool(sb2_meta.get("complete")),
            sb2_error=sb2_meta.get("error"),
        )

        # OPs verificadas por C2_UM (fallback B1_UM), convertidas para MI.
        candidate_products = myweg_products | {
            _text(item.get("produto")) for item in consolidation["protheus_for_coverage"]
        }
        op_pool = normalize_myweg_open_ops(
            ops_all, branch=code, product_codes=candidate_products
        )
        op_unit = {
            "status": op_pool["status"],
            "evidence": "C2_UM da OP; fallback B1_UM via ops-abertas.",
            "myweg_op_allocation": "verified_units_only",
            "protheus_parity_op_allocation": "enabled_unchanged",
            "potential_ops_count": len(ops_all),
            "verified_ops_count": op_pool["verified_count"],
            "unverified_ops_count": op_pool["unverified_count"],
            "unverified_sample": op_pool["unverified_sample"],
        }

        # --- Cenário 1: só Protheus (paridade Demanda atual; OP inalterada) ---
        protheus_lines = self._coverage.build(
            open_sales_orders=sales_branch,
            open_production_orders=ops_all,
            branch=code,
        )

        # --- Cenário 2: MyWEG elegível (estoque e OP com unidade confirmada) ---
        myweg_inputs = []
        blocked_stock_products: list[str] = []
        pending_stock_qty_mi = 0.0
        for line in eligible:
            assert line.product_code
            key = (code, line.product_code)
            stock_unavailable = (
                key not in stock["pool"]
                and line.product_code in stock["missing_sb2_products"]
            )
            if stock_unavailable:
                blocked_stock_products.append(line.product_code)
                pending_stock_qty_mi += float(line.open_quantity) / 1000.0
                product_stock = 0.0
            else:
                product_stock = float(stock["pool"].get(key, 0.0))
            # Mantém a necessidade na prévia mesmo sem fonte SB2 (cobertura pendente).
            myweg_inputs.append(
                projection_to_coverage_input(line, product_stock_mi=product_stock)
            )
        myweg_inputs = apply_pool_stock_to_inputs(myweg_inputs, stock["pool"], branch=code)
        myweg_lines = self._coverage.build(
            open_sales_orders=myweg_inputs,
            open_production_orders=op_pool["items"],
            branch=code,
        )

        # --- Cenário 3: consolidação proposta (ADR pendente) ---
        # Um único build e um pool de OPs por (filial, produto), sem duplicação.
        consolidated_inputs = apply_pool_stock_to_inputs(
            list(consolidation["protheus_for_coverage"]) + list(myweg_inputs),
            stock["pool"],
            branch=code,
        )
        consolidated_lines = self._coverage.build(
            open_sales_orders=consolidated_inputs,
            open_production_orders=op_pool["items"],
            branch=code,
        )

        for line in [*myweg_lines, *consolidated_lines]:
            line.op_coverage_incomplete = line.product_code in op_pool["unverified_products"]
        today = self._today or date.today()
        adr_accepted = False
        stock_data_complete = bool(sb2_meta.get("complete")) and not sb2_meta.get("error")
        if exclusive and stock["incomplete"]:
            stock_data_complete = False
        sources_readable = not source_errors
        productive_coverage_complete = bool(op_pool["complete"])
        consolidation_blocked = (
            (not adr_accepted)
            or bool(consolidation["reconciliation_blocked"])
            or bool(consolidation["customer_identity_pending"])
            or bool(stock["incomplete"] and exclusive)
            or bool(protheus_units["mixed"])
            or not stock_data_complete
        )
        # Cobertura consolidada nunca é confiável enquanto ADR/OP pendentes.
        integrity = {
            "sources_readable": sources_readable,
            "stock_data_complete": stock_data_complete,
            "productive_coverage_complete": productive_coverage_complete,
            "consolidation_adr_blocked": not adr_accepted,
            "op_unit_unverified": not op_pool["complete"],
            "consolidated_coverage_reliable": False,
        }
        # reliable global exige fontes + estoque completos; incomplete com error vazio → False.
        preview_reliable = sources_readable and stock_data_complete

        return {
            "preview": True,
            "wired_to_demand_endpoint": False,
            "productive_activation_blocked": True,
            "reliable": preview_reliable,
            "integrity": integrity,
            "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
            "branch": code,
            "customer_scope": {
                "weg_linhares_code": WEG_LINHARES_CUSTOMER_CODE,
                "weg_linhares_store": WEG_LINHARES_CUSTOMER_STORE,
                "identification": "codigo_cadastro+loja_cadastro",
                "codigo_cliente_is_product_reference": True,
            },
            "coverage_unit": COVERAGE_UNIT_MI,
            "batch": batch_meta,
            "protheus_units": protheus_units,
            "quantities_mi": {
                "myweg_eligible_demanded": round(
                    sum(float(line.open_quantity) / 1000.0 for line in eligible), 3
                ),
                "myweg_covered_by_validated_stock": round(
                    sum(line.allocated_stock for line in myweg_lines), 3
                ),
                "myweg_covered_by_verified_op": round(
                    sum(float(order["quantity"]) for line in myweg_lines for order in line.covering_orders),
                    3,
                ),
                "myweg_uncovered_confirmed": round(
                    sum(line.uncovered_quantity for line in myweg_lines), 3
                ),
                "myweg_pending_missing_stock_source": round(pending_stock_qty_mi, 3),
                "overlap_retained_protheus_open": round(
                    sum(_number(item.get("saldo")) for item in consolidation["overlap_pending"]),
                    3,
                ),
                "reconciliation_blocked_open": round(
                    sum(
                        _number(item.get("saldo"))
                        for item in consolidation["reconciliation_blocked"]
                    ),
                    3,
                ),
            },
            "stock": {
                "warehouse": warehouse_code,
                "unit": COVERAGE_UNIT_MI,
                "incomplete": stock["incomplete"],
                "sb2_complete": stock["sb2_complete"],
                "sb2_error": stock["sb2_error"],
                "sb2_diagnostics": {
                    "zero_vs_absent": {
                        "zero_confirmed": stock["zero_confirmed_products"][:50],
                        "absent_or_invalid": stock["missing_sb2_products"][:50],
                    },
                    "rejected_rows": sb2_meta.get("rejected_rows", [])[:20],
                    "duplicate_products": sb2_meta.get("duplicate_products", [])[:20],
                    "pages_read": sb2_meta.get("pages_read"),
                    "rows_accepted": sb2_meta.get("rows_accepted"),
                },
                "exclusive_product_count": len(stock["exclusive_myweg_products"]),
                "missing_sb2_count": len(stock["missing_sb2_products"]),
                "zero_confirmed_count": len(stock["zero_confirmed_products"]),
                "blocked_products_without_stock_source": sorted(set(blocked_stock_products)),
            },
            "identity_pending": {
                "line_count": len(pending_identity),
                "items": [
                    {
                        "id": line.id,
                        "record_id": line.record_id,
                        "resolution_status": line.resolution_status,
                        "identity_kind": line.identity_kind,
                        "matched_by": line.matched_by,
                        "open_quantity_un": str(line.open_quantity),
                        "due_date": line.due_date.isoformat(),
                    }
                    for line in pending_identity[:50]
                ],
            },
            "overlap_pending": {
                "line_count": len(consolidation["overlap_pending"]),
                "items": [
                    {
                        "source": OVERLAP_PENDING,
                        "sales_order": _text(item.get("pedido")),
                        "line_item": _text(item.get("linha")),
                        "product_code": _text(item.get("produto")),
                        "open_quantity": _number(item.get("saldo")),
                        "unit": _text(item.get("unidade")) or None,
                        "due_date": _text(item.get("data_entrega"))[:10] or None,
                        "codigo_cadastro": _text(item.get("codigo_cadastro")) or None,
                        "loja_cadastro": _text(item.get("loja_cadastro")) or None,
                        "product_in_myweg": bool(item.get("_preview_overlap_product_in_myweg")),
                    }
                    for item in consolidation["overlap_pending"][:50]
                ],
            },
            "customer_identity_pending": {
                "line_count": len(consolidation["customer_identity_pending"]),
                "items": [
                    {
                        "source": CUSTOMER_IDENTITY_PENDING,
                        "sales_order": _text(item.get("pedido")),
                        "product_code": _text(item.get("produto")),
                        "reason": item.get("_preview_block_reason"),
                        "codigo_cliente_product_ref": _text(item.get("codigo_cliente")) or None,
                        "loja_cadastro": _text(item.get("loja_cadastro")) or None,
                    }
                    for item in consolidation["customer_identity_pending"][:50]
                ],
            },
            "reconciliation_blocked": {
                "line_count": len(consolidation["reconciliation_blocked"]),
                "items": [
                    {
                        "source": RECONCILIATION_BLOCKED,
                        "sales_order": _text(item.get("pedido")),
                        "product_code": _text(item.get("produto")),
                        "reason": item.get("_preview_block_reason"),
                        "unit": _text(item.get("unidade")) or None,
                        "open_quantity": _number(item.get("saldo")),
                    }
                    for item in consolidation["reconciliation_blocked"][:50]
                ],
            },
            "scenarios": {
                "protheus_only": self._scenario_payload(
                    protheus_lines,
                    today,
                    source_label=SOURCE_PROTHEUS,
                    unit_meta=protheus_units,
                    sales_reference_line_count=len(sales_branch),
                ),
                "myweg_only": {
                    **self._scenario_payload(
                        myweg_lines, today, source_label="myweg", force_unit=COVERAGE_UNIT_MI
                    ),
                    "op_coverage_confirmed": op_pool["complete"],
                    "op_unit_status": op_pool["status"],
                    "pending_without_stock_source_mi": round(pending_stock_qty_mi, 3),
                },
                "consolidated_proposed": {
                    **self._scenario_payload(
                        consolidated_lines,
                        today,
                        source_label="consolidated",
                        force_unit=None if consolidation_blocked else COVERAGE_UNIT_MI,
                        incomplete=True,
                    ),
                    "definitive_total_published": False,
                    "blocked": consolidation_blocked,
                    "reliable": False,
                    "stock_only_partial": not op_pool["items"],
                    "single_pool_allocation": True,
                    "op_coverage_confirmed_for_myweg": op_pool["complete"],
                    "block_reasons": [
                        reason
                        for reason, flag in (
                            ("adr_not_accepted", not adr_accepted),
                            (
                                "unit_or_stock_incomplete",
                                bool(consolidation["reconciliation_blocked"])
                                or (stock["incomplete"] and exclusive)
                                or not stock_data_complete,
                            ),
                            (
                                "linhares_protheus_overlap_present",
                                bool(consolidation["overlap_pending"]),
                            ),
                            (
                                "customer_identity_pending",
                                bool(consolidation["customer_identity_pending"]),
                            ),
                            ("protheus_units_mixed", bool(protheus_units["mixed"])),
                            ("op_unit_unverified_myweg", not op_pool["complete"]),
                        )
                        if flag
                    ],
                },
            },
            "op_unit_assumption": op_unit,
        }

    def resolve_demand_origin_lines(
        self,
        user: object | None,
        *,
        branch: str = DEMAND_SOURCE_BRANCH,
        origin: str,
        warehouse: str = STOCK_WAREHOUSE_DEFAULT,
    ) -> dict[str, Any]:
        """Linhas completas para ``GET /demand`` (origin=myweg|both).

        Reusa o mesmo pool/adapter da prévia E2, com OPs normalizadas para MI.
        Consolidação não é total oficial (ADR ainda pendente).
        """
        code = _text(branch)
        if code == FORBIDDEN_BRANCH:
            raise InvalidBranch("MyWEG na Demanda não se aplica à filial 01.")
        if code != DEMAND_SOURCE_BRANCH:
            raise InvalidBranch(f"Filial inválida para MyWEG na Demanda: {branch!r}.")
        warehouse_code = _text(warehouse) or STOCK_WAREHOUSE_DEFAULT
        if warehouse_code != STOCK_WAREHOUSE_DEFAULT:
            raise InvalidBranch(
                f"Armazém {warehouse_code!r} não homologado (somente 01)."
            )
        origin_norm = _text(origin).lower()
        if origin_norm not in {"myweg", "both"}:
            raise ValueError(f"origin inválida para integração MyWEG: {origin!r}")
        self._assert_authorized(user)

        batch_meta, projected = self._myweg_source.project_latest_lines(user, branch=code)
        eligible = [line for line in projected if line.coverage_eligible and line.product_code]

        sales_payload = self._gateway.fetch_open_sales_orders()
        sales_raw = require_items_list(
            sales_payload, "items", source_name="open_sales_orders"
        )
        sales_all = [item for item in sales_raw if isinstance(item, dict)]
        sales_branch = [item for item in sales_all if _text(item.get("filial")) == code]

        myweg_products = {line.product_code for line in eligible if line.product_code}
        consolidation = classify_consolidation(
            protheus_items=sales_branch,
            myweg_eligible_products=myweg_products,
        )
        exclusive = sorted(
            code_p
            for code_p in myweg_products
            if not any(
                _text(item.get("produto")) == code_p and _text(item.get("filial")) == code
                for item in consolidation["protheus_for_coverage"]
            )
        )
        sb2_map, sb2_meta = self._fetch_sb2_stock(
            branch=code, warehouse=warehouse_code, product_codes=exclusive
        )
        stock = build_stock_pool_mi(
            branch=code,
            protheus_items=consolidation["protheus_for_coverage"]
            + consolidation["overlap_pending"],
            myweg_product_codes=myweg_products,
            sb2_quantities=sb2_map,
            sb2_complete=bool(sb2_meta.get("complete")),
            sb2_error=sb2_meta.get("error"),
        )

        myweg_inputs: list[dict[str, Any]] = []
        pending_without_stock = 0
        for line in eligible:
            assert line.product_code
            key = (code, line.product_code)
            stock_unavailable = (
                key not in stock["pool"]
                and line.product_code in stock["missing_sb2_products"]
            )
            # Necessidade permanece na Demanda mesmo sem SB2 consultável:
            # entra com estoque 0 (cobertura pendente), sem omitir o volume.
            product_stock = (
                0.0
                if stock_unavailable
                else float(stock["pool"].get(key, 0.0))
            )
            if stock_unavailable:
                pending_without_stock += 1
            item = projection_to_coverage_input(line, product_stock_mi=product_stock)
            if stock_unavailable:
                item["_preview_stock_source_pending"] = True
            myweg_inputs.append(item)
        myweg_inputs = apply_pool_stock_to_inputs(myweg_inputs, stock["pool"], branch=code)

        ops_payload = self._gateway.fetch_open_production_orders()
        ops_all = require_items_list(
            ops_payload, "items", source_name="open_production_orders"
        )
        candidate_products = myweg_products
        if origin_norm == "both":
            candidate_products = myweg_products | {
                _text(item.get("produto")) for item in consolidation["protheus_for_coverage"]
            }
        op_pool = normalize_myweg_open_ops(
            ops_all, branch=code, product_codes=candidate_products
        )

        if origin_norm == "myweg":
            lines = self._coverage.build(
                open_sales_orders=myweg_inputs,
                open_production_orders=op_pool["items"],
                branch=code,
            )
        else:
            consolidated_inputs = apply_pool_stock_to_inputs(
                list(consolidation["protheus_for_coverage"]) + list(myweg_inputs),
                stock["pool"],
                branch=code,
            )
            lines = self._coverage.build(
                open_sales_orders=consolidated_inputs,
                open_production_orders=op_pool["items"],
                branch=code,
            )

        for line in lines:
            line.op_coverage_incomplete = (
                line.product_code in op_pool["unverified_products"]
            )
            if line.source == SOURCE_MYWEG or line.sales_order == DISPLAY_ORDER_MYWEG:
                line.source = SOURCE_MYWEG
                line.planning = True
            else:
                line.source = SOURCE_PROTHEUS
                line.planning = False

        stock_data_complete = bool(sb2_meta.get("complete")) and not sb2_meta.get("error")
        if exclusive and stock["incomplete"]:
            stock_data_complete = False

        return {
            "lines": lines,
            "meta": {
                "origin": origin_norm,
                "branch": code,
                "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
                "official_aggregate": False,
                "op_unit_status": op_pool["status"],
                "op_coverage_complete": op_pool["complete"],
                "op_verified_count": op_pool["verified_count"],
                "op_unverified_count": op_pool["unverified_count"],
                "coverage_mode": (
                    "stock_and_op" if op_pool["complete"] else "stock_and_verified_op_partial"
                ),
                "productive_activation_blocked": True,
                "stock_data_complete": stock_data_complete,
                "stock_incomplete": bool(stock["incomplete"]),
                "pending_without_stock_source_count": pending_without_stock,
                "overlap_pending_count": len(consolidation["overlap_pending"]),
                "reconciliation_blocked_count": len(consolidation["reconciliation_blocked"]),
                "customer_identity_pending_count": len(
                    consolidation["customer_identity_pending"]
                ),
                "batch": batch_meta,
                "customer_scope": {
                    "weg_linhares_code": WEG_LINHARES_CUSTOMER_CODE,
                    "weg_linhares_store": WEG_LINHARES_CUSTOMER_STORE,
                },
                "unit": COVERAGE_UNIT_MI,
            },
        }

    def _blocked_preview(
        self,
        *,
        branch: str,
        warehouse: str,
        batch_meta: dict[str, Any] | None,
        pending_identity: list[Any],
        source_errors: list[str],
        reason: str,
    ) -> dict[str, Any]:
        return {
            "preview": True,
            "wired_to_demand_endpoint": False,
            "productive_activation_blocked": True,
            "reliable": False,
            "integrity": {
                "sources_readable": False,
                "stock_data_complete": False,
                "productive_coverage_complete": False,
                "consolidation_adr_blocked": True,
                "op_unit_unverified": True,
                "consolidated_coverage_reliable": False,
            },
            "blocked": True,
            "block_reason": reason,
            "source_errors": source_errors[:10],
            "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
            "branch": branch,
            "batch": batch_meta,
            "stock": {"warehouse": warehouse, "incomplete": True, "sb2_complete": False},
            "identity_pending": {"line_count": len(pending_identity), "items": []},
            "scenarios": {},
            "op_unit_assumption": {"status": OP_UNIT_UNVERIFIED},
        }

    def _scenario_payload(
        self,
        lines: list[DemandLine],
        today: date,
        *,
        source_label: str,
        unit_meta: dict[str, Any] | None = None,
        force_unit: str | None = COVERAGE_UNIT_MI,
        incomplete: bool = False,
        sales_reference_line_count: int | None = None,
    ) -> dict[str, Any]:
        covered_stock = round(sum(line.allocated_stock for line in lines), 3)
        covered_op = round(
            sum(
                sum(_number(item.get("quantity")) for item in line.covering_orders)
                for line in lines
            ),
            3,
        )
        conservation = conservation_check(lines)
        by_status: dict[str, int] = {}
        for line in lines:
            by_status[line.status] = by_status.get(line.status, 0) + 1
        horizon = self._presenter._horizon(lines)
        summary = self._presenter._summary(lines)
        summary["covered_by_stock"] = covered_stock
        summary["covered_by_orders"] = covered_op
        summary["source"] = source_label
        summary["incomplete"] = incomplete

        if unit_meta is not None:
            summary["unit"] = unit_meta["unit_label"]
            summary["units"] = unit_meta
            summary["global_total_authoritative"] = not unit_meta["mixed"]
            if unit_meta["mixed"]:
                # Evita total global artificial MI+PC.
                summary["open_quantity_mixed"] = True
                summary["open_quantity_by_unit"] = unit_meta["open_quantity_by_unit"]
            for bucket in horizon:
                bucket["unit"] = unit_meta["unit_label"]
        elif force_unit:
            summary["unit"] = force_unit
            for bucket in horizon:
                bucket["unit"] = force_unit
        else:
            summary["unit"] = "INCOMPLETE"
            for bucket in horizon:
                bucket["unit"] = "INCOMPLETE"

        payload: dict[str, Any] = {
            "summary": summary,
            "horizon": horizon,
            "status_counts": by_status,
            "conservation": conservation,
            "line_count": len(lines),
            "items_sample": [line.to_dict(today) for line in lines[:20]],
        }
        if sales_reference_line_count is not None:
            payload["protheus_sales_reference_line_count"] = sales_reference_line_count
        return payload

    def _fetch_sb2_stock(
        self,
        *,
        branch: str,
        warehouse: str,
        product_codes: list[str],
    ) -> tuple[dict[str, float | None], dict[str, Any]]:
        meta: dict[str, Any] = {
            "complete": True,
            "error": None,
            "rejected_rows": [],
            "duplicate_products": [],
            "pages_read": 0,
            "rows_accepted": 0,
            "rows_received": 0,
            "declared_total": None,
        }
        if not product_codes:
            return {}, meta

        balances: dict[str, float | None] = {code: None for code in product_codes}
        allowed = set(product_codes)
        seen_counts: dict[str, int] = {}
        _reject_reasons = {
            "branch_missing",
            "branch_mismatch",
            "warehouse_missing",
            "warehouse_mismatch",
            "unit_missing",
            "unit_incompatible",
            "quantity_invalid",
            "row_not_object",
            "product_not_requested",
            "product_missing",
            "duplicate_product",
        }

        try:
            page = 1
            declared_total: int | None = None
            while page <= self.STOCK_MAX_PAGES:
                payload = self._gateway.fetch_stock_balances_items(
                    branch=branch,
                    warehouse=warehouse,
                    only_positive=False,
                    page=page,
                    page_size=self.STOCK_PAGE_SIZE,
                    product_codes=product_codes,
                )
                rows = require_items_list(
                    payload, "items", source_name="stock_balances_items"
                )
                meta["pages_read"] = page
                meta["rows_received"] += len(rows)
                pagination = _pagination_meta(payload)

                page_total = pagination.get("total")
                if isinstance(page_total, int) and page_total >= 0:
                    if declared_total is None:
                        declared_total = page_total
                        meta["declared_total"] = declared_total
                    elif page_total != declared_total:
                        meta["complete"] = False
                        meta["error"] = "pagination_total_inconsistent"
                        break

                for row in rows:
                    if not isinstance(row, dict):
                        meta["rejected_rows"].append({"reason": "row_not_object"})
                        meta["complete"] = False
                        continue
                    code = _text(row.get("product_code"))
                    # Campos de identidade obrigatórios — ausência ≠ “bateu por omissão”.
                    raw_branch = row.get("branch", row.get("filial", None))
                    raw_wh = row.get("warehouse", row.get("armazem", None))
                    raw_uom = row.get("unit_of_measure", row.get("unidade", None))
                    row_branch = _text(raw_branch)
                    row_wh = _text(raw_wh)
                    uom = _text(raw_uom).upper()
                    qty = _finite_number(row.get("quantity"))

                    if not code:
                        meta["rejected_rows"].append({"reason": "product_missing"})
                        meta["complete"] = False
                        continue
                    if code not in allowed:
                        meta["rejected_rows"].append(
                            {"reason": "product_not_requested", "product_code": code}
                        )
                        meta["complete"] = False
                        continue
                    if raw_branch is None or not row_branch:
                        meta["rejected_rows"].append(
                            {"reason": "branch_missing", "product_code": code}
                        )
                        meta["complete"] = False
                        continue
                    if row_branch != branch:
                        meta["rejected_rows"].append(
                            {
                                "reason": "branch_mismatch",
                                "product_code": code,
                                "branch": row_branch,
                            }
                        )
                        meta["complete"] = False
                        continue
                    if raw_wh is None or not row_wh:
                        meta["rejected_rows"].append(
                            {"reason": "warehouse_missing", "product_code": code}
                        )
                        meta["complete"] = False
                        continue
                    if row_wh != warehouse:
                        meta["rejected_rows"].append(
                            {
                                "reason": "warehouse_mismatch",
                                "product_code": code,
                                "warehouse": row_wh,
                            }
                        )
                        meta["complete"] = False
                        continue
                    if raw_uom is None or not uom:
                        meta["rejected_rows"].append(
                            {"reason": "unit_missing", "product_code": code}
                        )
                        meta["complete"] = False
                        continue
                    if uom != COVERAGE_UNIT_MI:
                        meta["rejected_rows"].append(
                            {
                                "reason": "unit_incompatible",
                                "product_code": code,
                                "unit": uom,
                            }
                        )
                        meta["complete"] = False
                        continue
                    if qty is None:
                        meta["rejected_rows"].append(
                            {"reason": "quantity_invalid", "product_code": code}
                        )
                        meta["complete"] = False
                        continue

                    seen_counts[code] = seen_counts.get(code, 0) + 1
                    if seen_counts[code] > 1:
                        if code not in meta["duplicate_products"]:
                            meta["duplicate_products"].append(code)
                        balances[code] = None
                        meta["complete"] = False
                        meta["rejected_rows"].append(
                            {"reason": "duplicate_product", "product_code": code}
                        )
                        continue

                    balances[code] = qty
                    meta["rows_accepted"] += 1

                if declared_total is not None:
                    expected_pages = max(
                        1, (declared_total + self.STOCK_PAGE_SIZE - 1) // self.STOCK_PAGE_SIZE
                    )
                    if page >= expected_pages:
                        break
                    if len(rows) == 0:
                        meta["complete"] = False
                        meta["error"] = "pagination_incomplete"
                        break
                    if len(rows) < self.STOCK_PAGE_SIZE and page < expected_pages:
                        meta["complete"] = False
                        meta["error"] = "pagination_short_page"
                        break
                elif len(rows) < self.STOCK_PAGE_SIZE:
                    break

                if page == self.STOCK_MAX_PAGES:
                    # Ainda haveria páginas? Só incompleto se total sugere mais ou página cheia.
                    if declared_total is not None and page * self.STOCK_PAGE_SIZE < declared_total:
                        meta["complete"] = False
                        meta["error"] = "pagination_max_pages"
                    elif declared_total is None and len(rows) >= self.STOCK_PAGE_SIZE:
                        meta["complete"] = False
                        meta["error"] = "pagination_max_pages"
                    break
                page += 1

            if declared_total is not None and meta["rows_received"] != declared_total:
                # Contagem recebida diverge do total declarado → consulta incompleta/inválida.
                meta["complete"] = False
                if not meta["error"]:
                    meta["error"] = "pagination_count_mismatch"

            if meta["duplicate_products"] or any(
                r.get("reason") in _reject_reasons for r in meta["rejected_rows"]
            ):
                meta["complete"] = False

            return balances, meta
        except PreviewPayloadError as exc:
            return {}, {**meta, "complete": False, "error": str(exc)[:200]}
        except Exception as exc:  # noqa: BLE001
            return {}, {
                **meta,
                "complete": False,
                "error": f"falha_comunicacao:{type(exc).__name__}",
            }

    @staticmethod
    def _assert_authorized(user: object | None) -> None:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        if not can(user, PC_DEMAND_VIEW):
            raise PermissionError("Você não tem permissão para ver a demanda.")
        if not can(user, PC_MYWEG_NEEDS_VIEW):
            raise PermissionError(
                "Você não tem permissão para consultar Necessidades WEG."
            )
        if not can(user, PC_VIEW_FILIAL_02):
            raise BranchAccessDenied("Sem permissão para a filial 02.")
