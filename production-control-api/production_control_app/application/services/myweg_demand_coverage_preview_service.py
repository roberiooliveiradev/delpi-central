"""Prévia interna Demanda MyWEG + Protheus — motor DemandCoverageService.

Inerte para usuários: não altera GET /demand, UI ou KPIs produtivos.
ADR de consolidação permanece ARCHITECTURE_DECISION_REQUIRED.
"""

from __future__ import annotations

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
    OVERLAP_PENDING,
    RECONCILIATION_BLOCKED,
    SOURCE_PROTHEUS,
    STOCK_WAREHOUSE_DEFAULT,
    apply_pool_stock_to_inputs,
    build_stock_pool_mi,
    classify_consolidation,
    conservation_check,
    projection_to_coverage_input,
)


def _unwrap(payload: Any, key: str) -> list[Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    source = data if isinstance(data, dict) else payload
    items = source.get(key) if isinstance(source, dict) else None
    return items if isinstance(items, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
        # Reusa summary/horizon do DemandService sem carregar carteira.
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
        self._assert_authorized(user)

        batch_meta, projected = self._myweg_source.project_latest_lines(user, branch=code)

        eligible = [line for line in projected if line.coverage_eligible and line.product_code]
        pending_identity = [line for line in projected if not line.coverage_eligible]

        try:
            sales_payload = self._gateway.fetch_open_sales_orders()
            ops_payload = self._gateway.fetch_open_production_orders()
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError("Não foi possível carregar carteira/OPs para a prévia.") from exc

        sales_all = [item for item in _unwrap(sales_payload, "items") if isinstance(item, dict)]
        sales_branch = [item for item in sales_all if _text(item.get("filial")) == code]
        ops_all = [item for item in _unwrap(ops_payload, "items") if isinstance(item, dict)]

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
        sb2_map, sb2_complete, sb2_error = self._fetch_sb2_stock(
            branch=code, warehouse=warehouse, product_codes=exclusive
        )
        stock = build_stock_pool_mi(
            branch=code,
            protheus_items=consolidation["protheus_for_coverage"]
            + consolidation["overlap_pending"],
            myweg_product_codes=myweg_products,
            sb2_quantities=sb2_map,
            sb2_complete=sb2_complete,
            sb2_error=sb2_error,
        )

        # --- Cenário 1: só Protheus (paridade Demanda atual da filial) ---
        protheus_lines = self._coverage.build(
            open_sales_orders=sales_branch,
            open_production_orders=ops_all,
            branch=code,
        )

        # --- Cenário 2: só MyWEG elegível ---
        myweg_inputs = []
        blocked_stock_products: list[str] = []
        for line in eligible:
            assert line.product_code
            key = (code, line.product_code)
            if key not in stock["pool"] and line.product_code in stock["missing_sb2_products"]:
                blocked_stock_products.append(line.product_code)
                continue
            product_stock = float(stock["pool"].get(key, 0.0))
            myweg_inputs.append(
                projection_to_coverage_input(line, product_stock_mi=product_stock)
            )
        myweg_inputs = apply_pool_stock_to_inputs(myweg_inputs, stock["pool"], branch=code)
        myweg_lines = self._coverage.build(
            open_sales_orders=myweg_inputs,
            open_production_orders=ops_all,
            branch=code,
        )

        # --- Cenário 3: consolidação proposta (não produtiva / ADR pendente) ---
        # MyWEG primário para Linhares; demais clientes Protheus; overlap não some.
        consolidated_inputs = list(consolidation["protheus_for_coverage"]) + myweg_inputs
        consolidated_inputs = apply_pool_stock_to_inputs(
            consolidated_inputs, stock["pool"], branch=code
        )
        consolidated_lines = self._coverage.build(
            open_sales_orders=consolidated_inputs,
            open_production_orders=ops_all,
            branch=code,
        )

        today = self._today or date.today()
        adr_accepted = False
        consolidation_blocked = (not adr_accepted) or bool(
            consolidation["reconciliation_blocked"]
        ) or bool(stock["incomplete"] and exclusive)

        return {
            "preview": True,
            "wired_to_demand_endpoint": False,
            "productive_activation_blocked": True,
            "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
            "branch": code,
            "customer_scope": {
                "weg_linhares_code": WEG_LINHARES_CUSTOMER_CODE,
                "weg_linhares_store": WEG_LINHARES_CUSTOMER_STORE,
            },
            "coverage_unit": COVERAGE_UNIT_MI,
            "batch": batch_meta,
            "stock": {
                "warehouse": warehouse,
                "unit": COVERAGE_UNIT_MI,
                "incomplete": stock["incomplete"],
                "sb2_complete": stock["sb2_complete"],
                "sb2_error": stock["sb2_error"],
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
                        "product_in_myweg": bool(item.get("_preview_overlap_product_in_myweg")),
                    }
                    for item in consolidation["overlap_pending"][:50]
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
                    }
                    for item in consolidation["reconciliation_blocked"][:50]
                ],
            },
            "scenarios": {
                "protheus_only": self._scenario_payload(
                    protheus_lines, today, source_label=SOURCE_PROTHEUS
                ),
                "myweg_only": self._scenario_payload(
                    myweg_lines, today, source_label="myweg"
                ),
                "consolidated_proposed": {
                    **self._scenario_payload(
                        consolidated_lines, today, source_label="consolidated"
                    ),
                    "definitive_total_published": False,
                    "blocked": consolidation_blocked,
                    "block_reasons": [
                        reason
                        for reason, flag in (
                            ("adr_not_accepted", not adr_accepted),
                            (
                                "unit_or_stock_incomplete",
                                bool(consolidation["reconciliation_blocked"])
                                or (stock["incomplete"] and exclusive),
                            ),
                            (
                                "linhares_protheus_overlap_present",
                                bool(consolidation["overlap_pending"]),
                            ),
                        )
                        if flag
                    ],
                },
            },
            "op_unit_assumption": {
                "status": "ASSUMED_PRODUCT_UM",
                "note": (
                    "Endpoint ops-abertas não expõe B1_UM; o motor atual de Demanda "
                    "já aloca saldo_op com no_estoque sem conversão. Prévia MyWEG "
                    "normaliza necessidade UN→MI (÷1000) alinhada à UM SB1 MI "
                    "homologada. Se a UM da OP divergir, a alocação fica sob "
                    "HIPOTESE_A_VALIDAR."
                ),
            },
        }

    def _scenario_payload(
        self, lines: list[DemandLine], today: date, *, source_label: str
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
        for bucket in horizon:
            bucket["unit"] = COVERAGE_UNIT_MI
        summary = self._presenter._summary(lines)
        summary["unit"] = COVERAGE_UNIT_MI
        summary["covered_by_stock"] = covered_stock
        summary["covered_by_orders"] = covered_op
        summary["source"] = source_label
        return {
            "summary": summary,
            "horizon": horizon,
            "status_counts": by_status,
            "conservation": conservation,
            "line_count": len(lines),
            "items_sample": [line.to_dict(today) for line in lines[:20]],
        }

    def _fetch_sb2_stock(
        self,
        *,
        branch: str,
        warehouse: str,
        product_codes: list[str],
    ) -> tuple[dict[str, float | None], bool, str | None]:
        if not product_codes:
            return {}, True, None
        balances: dict[str, float | None] = {code: None for code in product_codes}
        try:
            page = 1
            complete = True
            while page <= self.STOCK_MAX_PAGES:
                payload = self._gateway.fetch_stock_balances_items(
                    branch=branch,
                    warehouse=warehouse,
                    only_positive=False,
                    page=page,
                    page_size=self.STOCK_PAGE_SIZE,
                    product_codes=product_codes,
                )
                rows = _unwrap(payload, "items")
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    code = _text(row.get("product_code"))
                    if code not in balances:
                        continue
                    current = balances[code]
                    qty = _number(row.get("quantity"))
                    balances[code] = qty if current is None else float(current) + qty
                if len(rows) < self.STOCK_PAGE_SIZE:
                    break
                if page == self.STOCK_MAX_PAGES:
                    complete = False
                    break
                page += 1
            # Códigos pedidas sem linha: None permanece (≠ zero confirmado).
            for code, value in list(balances.items()):
                if value is None:
                    # only_positive=false deveria retornar 0; ausência = missing.
                    continue
            return balances, complete, None
        except Exception as exc:  # noqa: BLE001
            return {}, False, str(exc)[:200]

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
