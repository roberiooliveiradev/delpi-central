"""Allowlist v17 -> v18 — Inventory & Material Flow wave (DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001)."""

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "app/content/davi_external_read_allowlist.json"
data = json.loads(PATH.read_text(encoding="utf-8"))
ops = data["operations"]
by_id = {o["operationId"]: o for o in ops}

# --- B1: get_product_stock — expose committed/reserved quantities ------------
stock = by_id["get_product_stock"]
for f in ("committed_quantity", "reserved_quantity"):
    if f not in stock["approvedResponseFields"]:
        stock["approvedResponseFields"].append(f)
for alias in (
    "saldo empenhado",
    "saldo comprometido",
    "empenho do produto",
    "reserva do produto",
    "committed quantity",
    "reserved quantity",
    "saldo empenhado do produto",
    "saldo reservado do produto",
):
    if alias not in stock["semanticAliases"]:
        stock["semanticAliases"].append(alias)
stock["reason"] = (
    "Stock READ; branch is query filter; API_DELPI_ACCESS backend AuthZ; flat projection; "
    "committed/reserved expose empenho/reserva slices already computed backend-side"
)

# --- B2: get_supplies_stock_value — expose estimation metadata ----------------
sv = by_id["get_supplies_stock_value"]
for f in (
    "estimation.method",
    "estimation.stock_method",
    "estimation.stock_method_resolved",
    "estimation.closing_base_date",
    "estimation.closing_base_value",
    "estimation.bridge_value",
    "estimation.period_net_value",
    "estimation.official_closure_available",
    "estimation.official_closure_date",
    "estimation.official_closure_value",
    "estimation.official_closure_on_period_end",
    "estimation.data_quality_warning",
    "estimation.note",
):
    if f not in sv["approvedResponseFields"]:
        sv["approvedResponseFields"].append(f)
for alias in (
    "valor do estoque histórico",
    "valor do estoque historico",
    "estoque histórico",
    "estoque historico",
    "fechamento de estoque",
    "inventory valuation history",
    "stock valuation history",
    "stock closing value",
    "método de avaliação de estoque",
):
    if alias not in sv["semanticAliases"]:
        sv["semanticAliases"].append(alias)
sv["reason"] = (
    "Stock value READ (SB2 current or SB9+SD3 historical estimation); summary/estimation "
    "projection only; API_DELPI_ACCESS; date pair bounded to 366 days"
)

# --- B3: get_product_internal_movements — semantic classification fields ------
im = by_id["get_product_internal_movements"]
for f in (
    "items[].movement_category",
    "items[].movement_direction",
    "items[].movement_label",
    "items[].inventory_adjustment_nature",
):
    if f not in im["approvedResponseFields"]:
        im["approvedResponseFields"].append(f)
for alias in (
    "ajuste de inventário",
    "ajuste de inventario",
    "entrada de produção",
    "entrada de producao",
    "consumo de produção",
    "consumo de producao",
    "movimentação de produção",
    "production receipt",
    "production consumption",
    "inventory adjustment movement",
):
    if alias not in im["semanticAliases"]:
        im["semanticAliases"].append(alias)
im["reason"] = (
    "Internal stock/production movements (SD3); tm/cf/user_name not exposed; kind governed to "
    "warehouse_transfer|inventory_adjustment|production_receipt|production_consumption or absent; "
    "INVENT documents classified as adjustments, never as transfers; date window is atomic pair "
    "bounded to 366 days"
)
im["argumentConstraints"]["argumentLimits"]["kind"]["enum"] = [
    "warehouse_transfer",
    "inventory_adjustment",
    "production_receipt",
    "production_consumption",
]

NEW_OPS = [
    {
        "operationId": "list_supplies_inventory_adjustments",
        "reason": (
            "Inventory adjustments (SD3 doc='INVENT' from the SB7/MATA270 count processing); "
            "nature classified backend-side by CF (RE0=surplus entrance, DE0=shortage exit); "
            "raw tm/cf never exposed; page_size bounded to 50 broker-side; "
            "API_DELPI_ACCESS backend AuthZ"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "start_date",
            "end_date",
            "branch",
            "product_code",
            "warehouse",
            "nature",
            "page",
            "page_size",
        ],
        "approvedResponseFields": [
            "period_start",
            "period_end",
            "items[].issue_date",
            "items[].branch",
            "items[].product_code",
            "items[].product_description",
            "items[].unit",
            "items[].warehouse",
            "items[].document",
            "items[].movement_category",
            "items[].movement_direction",
            "items[].movement_label",
            "items[].inventory_adjustment_nature",
            "items[].nature_label",
            "items[].quantity",
            "items[].signed_quantity",
            "items[].movement_value",
            "items[].signed_value",
            "items[].inventory_document",
            "items[].counted_quantity",
            "page",
            "page_size",
            "total",
            "total_pages",
        ],
        "semanticAliases": [
            "ajustes de inventário",
            "ajustes de inventario",
            "furo de inventário",
            "furo de inventario",
            "sobra de inventário",
            "sobra de inventario",
            "divergência de inventário",
            "divergencia de inventario",
            "inventory adjustments",
            "inventory shortage",
            "inventory surplus",
            "inventory count adjustments",
            "ajuste de estoque por inventário",
        ],
        "argumentConstraints": {
            "requireArguments": ["start_date", "end_date"],
            "dateRanges": [
                {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 366,
                    "allowSingleBound": False,
                }
            ],
            "argumentLimits": {
                "nature": {"enum": ["shortage", "surplus"]},
                "page": {"minimum": 1, "default": 1},
                "page_size": {"minimum": 1, "maximum": 50, "default": 50},
            },
        },
    },
    {
        "operationId": "get_supplies_inventory_adjustments_summary",
        "reason": (
            "Inventory adjustment summary (totals plus by_month/by_branch/by_nature buckets) "
            "over SD3 doc='INVENT'; same governed classification as the list sibling; "
            "API_DELPI_ACCESS backend AuthZ"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "start_date",
            "end_date",
            "branch",
            "product_code",
            "warehouse",
            "nature",
        ],
        "approvedResponseFields": [
            "period_start",
            "period_end",
            "summary.adjustment_count",
            "summary.shortage_count",
            "summary.surplus_count",
            "summary.gross_quantity",
            "summary.net_quantity",
            "summary.gross_value",
            "summary.net_value",
            "summary.shortage_quantity",
            "summary.shortage_value",
            "summary.surplus_quantity",
            "summary.surplus_value",
            "by_month[].month",
            "by_month[].adjustment_count",
            "by_month[].shortage_count",
            "by_month[].surplus_count",
            "by_month[].gross_quantity",
            "by_month[].net_quantity",
            "by_month[].gross_value",
            "by_month[].net_value",
            "by_month[].shortage_quantity",
            "by_month[].shortage_value",
            "by_month[].surplus_quantity",
            "by_month[].surplus_value",
            "by_branch[].branch",
            "by_branch[].adjustment_count",
            "by_branch[].shortage_count",
            "by_branch[].surplus_count",
            "by_branch[].gross_quantity",
            "by_branch[].net_quantity",
            "by_branch[].gross_value",
            "by_branch[].net_value",
            "by_branch[].shortage_quantity",
            "by_branch[].shortage_value",
            "by_branch[].surplus_quantity",
            "by_branch[].surplus_value",
            "by_nature[].nature",
            "by_nature[].nature_label",
            "by_nature[].adjustment_count",
            "by_nature[].shortage_count",
            "by_nature[].surplus_count",
            "by_nature[].gross_quantity",
            "by_nature[].net_quantity",
            "by_nature[].gross_value",
            "by_nature[].net_value",
            "by_nature[].shortage_quantity",
            "by_nature[].shortage_value",
            "by_nature[].surplus_quantity",
            "by_nature[].surplus_value",
        ],
        "semanticAliases": [
            "resumo de ajustes de inventário",
            "resumo de ajustes de inventario",
            "total de furos",
            "total de sobras",
            "divergência de inventário resumida",
            "inventory adjustment summary",
            "inventory shortage total",
            "inventory surplus total",
            "valor de ajustes de inventário",
        ],
        "argumentConstraints": {
            "requireArguments": ["start_date", "end_date"],
            "dateRanges": [
                {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 366,
                    "allowSingleBound": False,
                }
            ],
            "argumentLimits": {"nature": {"enum": ["shortage", "surplus"]}},
        },
    },
    {
        "operationId": "get_product_raw_material_set_shortages",
        "reason": (
            "Raw-material shortage projection for the product's open production sets; "
            "branch REQUIRED; max_depth bounded 1-20; layered backend gate preserved "
            "(API_DELPI_ACCESS or PRODUCTION_CONTROL global or per-branch view perm via "
            "BranchAccessGate) — DAVI adds no ACL"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": ["code", "branch", "max_depth"],
        "approvedResponseFields": [
            "product.product_code",
            "product.product_description",
            "product.unit",
            "product.product_type",
            "sets[].production_order",
            "sets[].planned_start_date",
            "sets[].due_date",
            "sets[].open_quantity",
            "sets[].status",
            "sets[].short_material_count",
            "sets[].materials[].product_code",
            "sets[].materials[].product_description",
            "sets[].materials[].unit",
            "sets[].materials[].status",
            "sets[].materials[].shortage_date",
            "sets[].materials[].shortage_quantity",
            "sets[].materials[].needed_quantity",
            "sets[].materials[].consuming_production_order",
            "sets[].materials[].available_stock",
            "sets[].materials[].safety_stock",
            "sets[].materials[].structure_quantity",
            "summary.open_set_count",
            "summary.at_risk_set_count",
            "summary.short_mp_count",
            "summary.first_shortage_date",
            "summary.ok_set_count",
            "summary.no_commitment_set_count",
        ],
        "semanticAliases": [
            "falta de matéria-prima",
            "falta de materia prima",
            "ruptura de matéria-prima",
            "ruptura de materia prima",
            "falta de MP para produção",
            "falta de mp para producao",
            "raw material shortage",
            "material shortage for production",
            "ruptura no conjunto",
            "falta de insumo",
        ],
        "argumentConstraints": {
            "requireArguments": ["code", "branch"],
            "argumentLimits": {
                "max_depth": {"minimum": 1, "maximum": 20, "default": 8}
            },
        },
    },
    {
        "operationId": "get_production_consumption_by_item",
        "reason": (
            "Production consumption per item (SD4 real consumption); period defaults to "
            "current month when absent; limit bounded to 200; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "code",
            "start_date",
            "end_date",
            "branch",
            "product_group",
            "limit",
        ],
        "approvedResponseFields": [
            "item_code",
            "product_group",
            "items[].product_code",
            "items[].description",
            "items[].product_group",
            "items[].real_consumption_qty",
            "summary.total_records",
            "summary.branch",
            "summary.branch_filter_applied",
            "summary.period.start",
            "summary.period.end",
            "summary.is_complete",
            "pagination.limit",
            "pagination.offset",
            "pagination.returned",
            "pagination.is_complete",
        ],
        "semanticAliases": [
            "consumo do item na produção",
            "consumo do item na producao",
            "consumo de produção do produto",
            "consumo de producao do produto",
            "consumo real do item",
            "consumption by item",
            "item production consumption",
            "consumo de MP por produto",
        ],
        "argumentConstraints": {
            "requireArguments": ["code"],
            "dateRanges": [
                {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 366,
                    "allowSingleBound": True,
                }
            ],
            "argumentLimits": {
                "limit": {"minimum": 1, "maximum": 200, "default": 10},
                "product_group": {"minLength": 4, "maxLength": 4},
            },
        },
    },
    {
        "operationId": "get_production_consumption_top_items",
        "reason": (
            "Top consumed items in production (SD4), group_by governed to the declared "
            "dimension registry; limit bounded to 200; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "start_date",
            "end_date",
            "branch",
            "limit",
            "group_by",
        ],
        "approvedResponseFields": [
            "group_by",
            "items[].branch",
            "items[].item_code",
            "items[].description",
            "items[].unit",
            "items[].product_group",
            "items[].real_consumption_qty",
            "summary.total_records",
            "summary.branch",
            "summary.branch_filter_applied",
            "summary.period.start",
            "summary.period.end",
            "summary.consolidated_across_branches",
            "summary.is_complete",
            "pagination.limit",
            "pagination.offset",
            "pagination.returned",
            "pagination.is_complete",
        ],
        "semanticAliases": [
            "itens mais consumidos",
            "maiores consumos de produção",
            "maiores consumos de producao",
            "ranking de consumo",
            "top consumed items",
            "top production consumption",
            "consumo por grupo de produto",
            "consumo por filial",
        ],
        "argumentConstraints": {
            "dateRanges": [
                {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 366,
                    "allowSingleBound": True,
                }
            ],
            "argumentLimits": {
                "limit": {"minimum": 1, "maximum": 200, "default": 10},
                "group_by": {
                    "enum": ["general", "branch", "product_group", "unit", "branch_summary"]
                },
            },
        },
    },
    {
        "operationId": "get_production_allocation_gaps",
        "reason": (
            "Open production-order material allocations (SD4 empenhos) as of reference_date; "
            "limit bounded to 200; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "reference_date",
            "branch",
            "work_center",
            "limit",
        ],
        "approvedResponseFields": [
            "reference_date",
            "items[].branch",
            "items[].production_order",
            "items[].component_code",
            "items[].description",
            "items[].operation",
            "items[].allocated_qty",
            "items[].work_center",
            "summary.total_records",
            "summary.branch",
            "summary.branch_filter_applied",
            "summary.is_complete",
            "pagination.limit",
            "pagination.offset",
            "pagination.returned",
            "pagination.is_complete",
        ],
        "semanticAliases": [
            "empenhos em aberto",
            "materiais empenhados",
            "materiais alocados",
            "compromissos de produção",
            "compromissos de producao",
            "allocation gaps",
            "open commitments",
            "open material allocations",
            "production order commitments",
        ],
        "argumentConstraints": {
            "argumentLimits": {
                "limit": {"minimum": 1, "maximum": 200, "default": 10}
            }
        },
    },
    {
        "operationId": "get_production_orders_finished_without_consumption",
        "reason": (
            "Finished production orders whose set never recorded material consumption — "
            "anomaly signal for missing baixa; limit bounded to 200; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "reference_date",
            "branch",
            "work_center",
            "limit",
        ],
        "approvedResponseFields": [
            "reference_date",
            "items[].branch",
            "items[].production_order",
            "items[].product_code",
            "items[].description",
            "items[].planned_qty",
            "items[].produced_qty",
            "items[].component_code",
            "items[].operation",
            "items[].allocated_qty",
            "items[].work_center",
            "summary.total_records",
            "summary.branch",
            "summary.branch_filter_applied",
            "summary.is_complete",
            "pagination.limit",
            "pagination.offset",
            "pagination.returned",
            "pagination.is_complete",
        ],
        "semanticAliases": [
            "produção finalizada sem consumo",
            "producao finalizada sem consumo",
            "OP encerrada sem baixa",
            "op encerrada sem baixa",
            "finished orders without consumption",
            "missing material consumption",
            "produção sem baixa de MP",
        ],
        "argumentConstraints": {
            "argumentLimits": {
                "limit": {"minimum": 1, "maximum": 200, "default": 10}
            }
        },
    },
    {
        "operationId": "list_production_order_operation_materials",
        "reason": (
            "Active SD4 commitments (empenhos) for one production order + operation; "
            "branch REQUIRED; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": ["production_order", "operation", "branch"],
        "approvedResponseFields": [
            "branch",
            "production_order",
            "operation",
            "items[].product_code",
            "items[].description",
            "items[].unit",
            "items[].product_type",
            "items[].original_qty",
            "items[].open_qty",
            "items[].consumed_qty",
            "items[].commitment_count",
            "summary.material_count",
            "summary.commitment_count",
        ],
        "semanticAliases": [
            "materiais da operação",
            "materiais da operacao",
            "empenhos da OP",
            "materiais empenhados da ordem",
            "operation materials",
            "production order materials",
            "order operation commitments",
            "necessidade de material da operação",
        ],
        "argumentConstraints": {
            "requireArguments": ["production_order", "operation", "branch"]
        },
    },
    {
        "operationId": "list_production_order_operation_materials_batch",
        "reason": (
            "Batch variant of operation materials — SEMANTIC_READ_POST with trusted "
            "requestBody contract; production_orders deduped and bounded to 300 (fail-loud "
            "overflow, never silently truncated); branch REQUIRED; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "semanticTransport": "SEMANTIC_READ_POST",
        "approvedInputFields": ["branch", "production_orders"],
        "approvedResponseFields": [
            "branch",
            "production_orders",
            "items[].production_order",
            "items[].operation",
            "items[].product_code",
            "items[].description",
            "items[].unit",
            "items[].product_type",
            "items[].original_qty",
            "items[].open_qty",
            "items[].consumed_qty",
            "items[].commitment_count",
            "summary.requested_count",
            "summary.returned_count",
            "summary.order_count",
            "summary.commitment_count",
        ],
        "semanticAliases": [
            "materiais de várias OPs",
            "materiais de varias ops",
            "empenhos de várias ordens",
            "batch operation materials",
            "materials for multiple orders",
            "necessidade de material em lote",
        ],
        "argumentConstraints": {
            "requireArguments": ["branch", "production_orders"],
            "argumentLimits": {
                "production_orders": {"minItems": 1, "maxItems": 300}
            },
        },
    },
    {
        "operationId": "get_production_losses_records",
        "reason": (
            "Production loss records (SBC refugo/scrap); loss_type enum; limit bounded "
            "to 200; internal sequence/appointment ids not exposed; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "start_date",
            "end_date",
            "branch",
            "limit",
            "loss_type",
        ],
        "approvedResponseFields": [
            "loss_type",
            "items[].branch",
            "items[].loss_date",
            "items[].production_order",
            "items[].operation",
            "items[].material_code",
            "items[].description",
            "items[].loss_type",
            "items[].loss_qty",
            "items[].reason",
            "items[].resource",
            "summary.total_records",
            "summary.branch",
            "summary.branch_filter_applied",
            "summary.period.start",
            "summary.period.end",
            "summary.is_complete",
            "pagination.limit",
            "pagination.offset",
            "pagination.returned",
            "pagination.is_complete",
        ],
        "semanticAliases": [
            "perdas de produção",
            "perdas de producao",
            "refugo de produção",
            "refugo de producao",
            "registros de perda",
            "production losses",
            "scrap records",
            "perda de material",
        ],
        "argumentConstraints": {
            "dateRanges": [
                {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 366,
                    "allowSingleBound": True,
                }
            ],
            "argumentLimits": {
                "limit": {"minimum": 1, "maximum": 200, "default": 10},
                "loss_type": {"enum": ["refugo", "scrap", "both"]},
            },
        },
    },
    {
        "operationId": "get_production_losses_top_materials",
        "reason": (
            "Top materials by production loss quantity (SBC); loss_type enum; limit "
            "bounded to 200; API_DELPI_ACCESS"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": [
            "start_date",
            "end_date",
            "branch",
            "limit",
            "loss_type",
        ],
        "approvedResponseFields": [
            "loss_type",
            "items[].branch",
            "items[].material_code",
            "items[].description",
            "items[].loss_type",
            "items[].total_loss_qty",
            "items[].occurrence_count",
            "summary.total_records",
            "summary.branch",
            "summary.branch_filter_applied",
            "summary.period.start",
            "summary.period.end",
            "summary.is_complete",
            "pagination.limit",
            "pagination.offset",
            "pagination.returned",
            "pagination.is_complete",
        ],
        "semanticAliases": [
            "materiais com mais perdas",
            "maiores perdas de produção",
            "maiores perdas de producao",
            "ranking de refugo",
            "top loss materials",
            "top production losses",
            "materiais mais refugados",
        ],
        "argumentConstraints": {
            "dateRanges": [
                {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 366,
                    "allowSingleBound": True,
                }
            ],
            "argumentLimits": {
                "limit": {"minimum": 1, "maximum": 200, "default": 10},
                "loss_type": {"enum": ["refugo", "scrap", "both"]},
            },
        },
    },
    {
        "operationId": "get_supplies_safety_stock_item_details",
        "reason": (
            "Single-item safety stock detail: stock projection, purchase coverage and "
            "collection totals projected; per-collection item lists and the projection "
            "timeline stay internal; peer branch stock auto-derived and gated by "
            "branch_access_error; layered backend gate "
            "(require_any_permission_or_supplies_bff + BranchAccessGate); API_DELPI_ACCESS "
            "remains a qualifying global perm"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": ["code", "branch"],
        "approvedResponseFields": [
            "product.product_code",
            "product.product_description",
            "product.product_type",
            "product.unit",
            "product.product_group",
            "product.branch",
            "product.blocked",
            "product.status",
            "stock.safety_stock",
            "stock.available_stock",
            "stock.primary_stock",
            "stock.warehouse_50_stock",
            "stock.warehouse_98_stock",
            "stock.warehouse_99_stock",
            "stock.work_in_process_stock",
            "stock.work_in_process_committed",
            "stock.work_in_process_available",
            "stock.deficit_quantity",
            "stock.last_inventory_date",
            "peer_branch_stock.branch",
            "peer_branch_stock.found",
            "peer_branch_stock.available_stock",
            "peer_branch_stock.last_consumption_date",
            "purchase_coverage.status",
            "purchase_coverage.deficit_quantity",
            "purchase_coverage.eligible_open_quantity",
            "purchase_coverage.remaining_to_buy",
            "purchase_coverage.open_order_count",
            "purchase_coverage.eligible_order_count",
            "purchase_coverage.next_expected_delivery_date",
            "purchase_coverage.incompatible_unit_order_count",
            "purchase_coverage.warnings",
            "open_purchase_orders.total",
            "open_purchase_requests.total",
            "open_commitments.total",
            "open_commitments.summary.eligible_open_quantity",
            "open_commitments.summary.next_commitment_date",
            "open_commitments.summary.incompatible_unit_commitment_count",
            "open_commitments.summary.eligible_warehouses",
            "open_commitments.summary.warnings",
            "stock_projection.summary.as_of_date",
            "stock_projection.summary.initial_balance",
            "stock_projection.summary.safety_stock",
            "stock_projection.summary.eligible_purchase_quantity",
            "stock_projection.summary.eligible_commitment_quantity",
            "stock_projection.summary.final_projected_balance",
            "stock_projection.summary.final_balance_after_safety",
            "stock_projection.summary.minimum_projected_balance",
            "stock_projection.summary.first_shortage_date",
            "stock_projection.summary.projected_remaining_to_buy",
            "stock_projection.summary.status",
            "stock_projection.summary.eligible_warehouses",
            "stock_projection.summary.warnings",
            "monthly_consumption.total",
            "monthly_consumption.period_consumption",
            "monthly_consumption.period_start",
            "monthly_consumption.period_end",
            "monthly_consumption.items[].year_month",
            "monthly_consumption.items[].year_month_label",
            "monthly_consumption.items[].consumption_quantity",
        ],
        "semanticAliases": [
            "estoque de segurança do item",
            "estoque de seguranca do item",
            "detalhe de estoque de segurança",
            "detalhe de estoque de seguranca",
            "projeção de estoque do item",
            "projecao de estoque do item",
            "safety stock item details",
            "item safety stock",
            "item stock projection",
            "estoque mínimo do item",
            "estoque minimo do item",
        ],
        "argumentConstraints": {
            "requireArguments": ["code"]
        },
    },
    {
        "operationId": "get_supplies_safety_stock_consumption_analysis_item_details",
        "reason": (
            "Single-item consumption analysis with suggested safety stock and "
            "calculation memory (formula + inputs) — the explanation surface; "
            "item-level monthly series projected; annual chart data stays internal; "
            "same layered backend gate as the item details sibling"
        ),
        "executionMode": "catalog_action",
        "approvedInputFields": ["code", "branch"],
        "approvedResponseFields": [
            "item.product_code",
            "item.product_description",
            "item.product_type",
            "item.unit",
            "item.product_group",
            "item.branch",
            "item.blocked",
            "item.safety_stock",
            "item.available_stock",
            "item.primary_stock",
            "item.lead_time_days",
            "item.lead_time_business_days",
            "item.period_start",
            "item.period_end",
            "item.period_calendar_days",
            "item.period_business_days",
            "item.period_consumption",
            "item.average_daily_consumption",
            "item.suggested_safety_stock",
            "item.difference_quantity",
            "item.difference_percent",
            "item.coverage_business_days",
            "item.analysis_status",
            "item.quality_warnings",
            "item.has_inconsistent_data",
            "monthly_consumption.total",
            "monthly_consumption.items[].year_month",
            "monthly_consumption.items[].year_month_label",
            "monthly_consumption.items[].consumption_quantity",
            "calculation_memory.formula",
            "calculation_memory.average_daily_consumption_formula",
            "calculation_memory.period_consumption",
            "calculation_memory.period_business_days",
            "calculation_memory.average_daily_consumption",
            "calculation_memory.lead_time_days",
            "calculation_memory.lead_time_business_days",
            "calculation_memory.suggested_safety_stock",
            "calculation_memory.current_safety_stock",
            "calculation_memory.available_stock",
            "calculation_memory.coverage_business_days",
            "calculation_memory.quality_warnings",
            "period_start",
            "period_end",
        ],
        "semanticAliases": [
            "análise de consumo do item",
            "analise de consumo do item",
            "consumo médio do item",
            "consumo medio do item",
            "estoque de segurança sugerido",
            "estoque de seguranca sugerido",
            "consumption analysis item",
            "suggested safety stock",
            "item consumption analysis",
            "cobertura de estoque do item",
        ],
        "argumentConstraints": {
            "requireArguments": ["code"]
        },
    },
]

for entry in NEW_OPS:
    assert entry["operationId"] not in by_id, entry["operationId"]
    ops.append(entry)
    by_id[entry["operationId"]] = entry

# Remove promoted ops from explicitlyNotApproved.
promoted = {
    "get_product_raw_material_set_shortages",
    "get_supplies_safety_stock_item_details",
    "get_supplies_safety_stock_consumption_analysis_item_details",
}
data["explicitlyNotApproved"] = [
    e for e in data["explicitlyNotApproved"]
    if e["operationId"] not in promoted
]

# Record the explicit defer/redundant decisions for the reviewed siblings.
existing_na = {e["operationId"] for e in data["explicitlyNotApproved"]}
for entry in (
    {
        "operationId": "get_production_consumption_top_items_by_work_center",
        "coverageDisposition": "DEFER",
        "primaryBlocker": "REWORK_REQUIRED",
        "reason": (
            "Semantics reviewed: the work-center slice counts allocation-side rows, "
            "not realized consumption — answers a different question than the top-items "
            "consumption family. Needs its own bounded contract before READ promotion."
        ),
    },
    {
        "operationId": "get_production_consumption_top_items_validated",
        "coverageDisposition": "SEMANTICALLY_REDUNDANT",
        "primaryBlocker": "SEMANTICALLY_REDUNDANT",
        "reason": (
            "Same ranking as get_production_consumption_top_items narrowed to rows whose "
            "OP has an appointment — a filter variant of the promoted operation, not a "
            "distinct governed capability."
        ),
    },
):
    if entry["operationId"] not in existing_na:
        data["explicitlyNotApproved"].append(entry)

data["version"] = 18
data["coverageDecision"] = {
    "taskId": "DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001",
    "decision": "PROMOTE_INVENTORY_MATERIAL_FLOW_READS",
    "reason": (
        "Promote 14 Inventory & Material Flow READs: 2 new inventory-adjustment ops "
        "(list + summary over SD3 doc='INVENT', CF-owned nature RE0=surplus/DE0=shortage, "
        "SB7 provenance, 366d pair, page_size<=50), raw-material set shortages (branch "
        "required, layered BranchAccessGate preserved), production consumption by-item "
        "and top-items, allocation gaps, finished-without-consumption anomaly, OP "
        "operation materials (single + SEMANTIC_READ_POST batch bounded 300), losses "
        "records and top-materials, safety-stock item details and consumption-analysis "
        "details (composite blocks minimized: collection totals/summaries and "
        "calculation memory only). Enrich get_product_stock with committed/reserved "
        "quantities, get_supplies_stock_value with estimation.* provenance, and "
        "get_product_internal_movements with governed kind enum (4 values) plus "
        "movement classification fields. DEFER: top_items_by_work_center "
        "(REWORK_REQUIRED — allocation-side semantics), top_items_validated "
        "(SEMANTICALLY_REDUNDANT), purchase_requests_open_coverage "
        "(UNBOUNDED_LIST_NO_PAGINATION, unchanged). MCP tools remain 2. GPT Actions "
        "unchanged. No deploy, no rollout."
    ),
}

PATH.write_text(
    json.dumps(data, indent=1, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"version={data['version']} ops={len(ops)} na={len(data['explicitlyNotApproved'])}")
