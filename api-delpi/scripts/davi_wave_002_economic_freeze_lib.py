#!/usr/bin/env python3
"""DAVI Wave 2 Product Economic Intelligence — evidence freeze (no runtime mutation)."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE"
CORRECTION_TASK_ID = "DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE-CORRECTION-001"
IMPLEMENTATION_TASK_ID = "DAVI-CAPABILITY-EXPANSION-WAVE-002"
SOURCE_FREEZE_SHA = "b5de5122f13bb921f6e6a48a0fad2d559e97eb80"
ACCEPTANCE_STEM = "davi-capability-wave-002-architecture-acceptance"
DEFERRED_STATUSES = frozenset({"DEFER", "DEFER_FROM_READ_WAVE"})
INVENTORY_STEM = "davi-capability-wave-002-economic-inventory"
FREEZE_STEM = "davi-capability-wave-002-freeze"
ARTIFACT_CLASS = "EVIDENCE_NOT_RUNTIME_AUTHORITY"

CURRENT_ELIGIBLE = [
    "search_products",
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
    "get_product_factory_status",
    "get_product_structure_exclusivity",
    "get_product_shipping_status",
]
MCP_TOOLS = [
    "discover_delpi_information",
    "execute_delpi_information",
]
ECONOMIC_QUARANTINE_TOKENS = ["preco", "price", "pricing", "custo", "cost"]
REQUIRED_FREEZE_FIELDS = (
    "capabilityId",
    "businessName",
    "businessNeed",
    "status",
    "canonicalOperations",
    "canonicalUseCases",
    "readPrepareAct",
    "technicalOwner",
    "businessOwner",
    "sourceOfTruth",
    "identity",
    "backendAuthz",
    "approvedInputFields",
    "requiredInputFields",
    "optionalInputFields",
    "approvedResponseFields",
    "shape",
    "projectionMode",
    "argumentConstraints",
    "pagination",
    "limits",
    "timeSemantics",
    "monetarySemantics",
    "currencySemantics",
    "unitSemantics",
    "derivedFields",
    "completeness",
    "provenance",
    "semanticAliasesPtBr",
    "semanticAliasesEn",
    "privacy",
    "risk",
    "observability",
    "negativeAuthzPlan",
    "quarantineDeltaRequired",
    "openGaps",
)

_SAFE_OBS = (
    "Log action_id, actor identifier when policy allows, status, latency, "
    "result_count, date window when applicable, truncated, correlation id. "
    "Never log Authorization, OAuth tokens, candidate token, raw monetary payload, "
    "full supplier/customer records, or secrets."
)
_NEG_AUTHZ = (
    "Local/backend: authenticated caller without API_DELPI_ACCESS must receive "
    "backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless "
    "genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden."
)
_PROVENANCE = (
    "Preserve canonical operation/use case, product code, reference/start/end dates "
    "or date_end_exclusive, branch filter when used, truncated/is_complete, and "
    "currency/unit fields that are approved. Do not expose SQL, hosts, tokens, "
    "repository internals, or route mechanics."
)

_PRICING_FIELDS = [
    "product.code",
    "product.description",
    "product.unit",
    "prices[].table_code",
    "prices[].table_description",
    "prices[].sale_price",
    "prices[].currency",
    "prices[].lot_quantity",
    "prices[].valid_from",
    "prices[].active",
]
_HISTORY_FIELDS = [
    "product.product_code",
    "product.description",
    "product.product_type",
    "product.unit",
    "start_date",
    "date_end_exclusive",
    "branch",
    "items[].issue_date",
    "items[].invoice_number",
    "items[].supplier_code",
    "items[].supplier_name",
    "items[].quantity",
    "items[].unit_price",
    "items[].total_value",
    "items[].icms_rate",
    "items[].previous_unit_price",
    "items[].variation_percent",
    "summary.total_purchases",
    "summary.min_unit_price",
    "summary.max_unit_price",
    "summary.avg_unit_price",
    "summary.last_variation_percent",
]
_LAST_PURCHASE_FIELDS = [
    "product.product_code",
    "product.description",
    "product.product_type",
    "product.unit",
    "last_purchase.branch",
    "last_purchase.invoice_number",
    "last_purchase.issue_date",
    "last_purchase.supplier_code",
    "last_purchase.supplier_name",
    "last_purchase.quantity",
    "last_purchase.unit_price",
    "last_purchase.total_value",
    "last_purchase.icms_rate",
    "last_purchase.purchase_order",
]
_SIMULATION_FIELDS = [
    "product.product_code",
    "product.description",
    "product.product_type",
    "product.unit",
    "product.group_code",
    "product.standard_cost",
    "product.standard_cost_date",
    "pa_reference.reference_quantity",
    "pa_reference.reference_unit",
    "pa_reference.bom_quantity_factor",
    "cost_basis.reference_quantity",
    "cost_basis.reference_unit",
    "cost_basis.standard_cost_unit",
    "cost_basis.material_cost_unit",
    "cost_basis.pa_standard_cost_basis",
    "cost_basis.material_cost_basis",
    "cost_basis.catalog_unit",
    "cost_basis.catalog_pieces_per_unit",
    "cost_basis.catalog_quantity_per_reference",
    "cost_basis.pa_standard_cost_per_piece",
    "cost_basis.total_material_cost_per_piece",
    "price_source",
    "adjustment_percent",
    "materials.items[].rank",
    "materials.items[].raw_material_code",
    "materials.items[].raw_material_description",
    "materials.items[].unit",
    "materials.items[].quantity_per_pa",
    "materials.items[].unit_cost",
    "materials.items[].extended_cost",
    "materials.items[].impact_on_material_cost_percent",
    "materials.items[].impact_on_pa_cost_percent",
    "materials.items[].simulated_unit_cost",
    "materials.items[].simulated_extended_cost",
    "materials.items[].simulated_impact_on_pa_cost_percent",
    "materials.items[].cost_delta",
    "materials.total",
    "materials.returned",
    "summary.total_raw_materials",
    "summary.returned_materials",
    "summary.total_material_cost",
    "summary.simulated_total_material_cost",
    "summary.projected_cost_delta",
    "summary.top_material_impact_percent",
    "summary.pa_standard_cost",
    "summary.pa_cost_comparable",
    "summary.material_to_pa_cost_ratio",
    "simulation.adjustment_percent",
    "simulation.projected_total_material_cost",
    "simulation.projected_cost_delta",
    "simulation.projected_pa_cost_delta_percent",
]


def api_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return api_root().parents[0]


def git_sha(ref: str = "HEAD") -> str:
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _keep_global(token: str, aliases: str) -> dict[str, str]:
    return {
        "token": token,
        "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES",
        "rationale": (
            f"Do not remove global `{token}` quarantine. Future implementation must add "
            f"precise multiword aliases ({aliases}) so the promoted action owns the token; "
            "unrelated economic actions remain quarantined."
        ),
    }


def _record(**kwargs: Any) -> dict[str, Any]:
    missing = [k for k in REQUIRED_FREEZE_FIELDS if k not in kwargs]
    if missing:
        raise ValueError(f"{kwargs.get('capabilityId')} missing fields: {missing}")
    status = kwargs["status"]
    fields = kwargs.get("approvedResponseFields") or []
    if status == "FROZEN_FOR_IMPLEMENTATION":
        if not fields:
            raise ValueError(f"{kwargs['capabilityId']} frozen without approvedResponseFields")
        if any("*" in str(f) or str(f).endswith(".") for f in fields):
            raise ValueError(f"{kwargs['capabilityId']} wildcard projection forbidden")
        if not str(kwargs.get("backendAuthz") or "").startswith("PROVEN"):
            raise ValueError(f"{kwargs['capabilityId']} backendAuthz is not PROVEN")
        if kwargs.get("readPrepareAct") not in {"READ"}:
            raise ValueError(f"{kwargs['capabilityId']} is not READ")
        if kwargs.get("projectionMode") != "nested":
            raise ValueError(f"{kwargs['capabilityId']} projectionMode must be nested")
        if kwargs.get("perOperationProjectorRequired") is True:
            raise ValueError(f"{kwargs['capabilityId']} requires per-operation projector")
    return kwargs


def candidate_records() -> list[dict[str, Any]]:
    technical_owner = "api-delpi Product bounded context"
    business_owner = (
        "TO_INVENTORY — no canonical named business owner proven in source; "
        "do not invent Comercial, Suprimentos, Controladoria or Financeiro"
    )
    return [
        _record(
            capabilityId="product.commercial.pricing",
            businessName={
                "ptBr": "Tabelas e preços comerciais do produto",
                "en": "Commercial product price tables",
            },
            businessNeed=(
                "Consultar as tabelas comerciais registradas para um produto, incluindo "
                "preço de venda, moeda armazenada, lote, vigência e indicador de ativo, "
                "sem afirmar que todas as linhas representam o preço atual. Not purchase "
                "cost and not a mega-financial dump."
            ),
            status="FROZEN_FOR_IMPLEMENTATION",
            canonicalOperations=["get_product_pricing"],
            canonicalUseCases=["GetProductPricingUseCase"],
            readPrepareAct="READ",
            technicalOwner=technical_owner,
            businessOwner=business_owner,
            sourceOfTruth=(
                "GET /products/{code}/pricing → GetProductPricingUseCase → "
                "ProductPricingRepository: SB1010 header (B1_COD/B1_DESC/B1_UM) + "
                "DA1010/DA0010 sale tables (DA1_PRCVEN, DA1_CODTAB, DA1_MOEDA, "
                "DA1_QTDLOT, DA1_DATVIG, DA1_ATIVO)"
            ),
            identity="END_USER_ACCOUNT",
            backendAuthz="PROVEN: @require_permission(API_DELPI_ACCESS) on product_pricing",
            approvedInputFields=["code"],
            requiredInputFields=["code"],
            optionalInputFields=[],
            inputMinimization={
                "code": "APPROVED_REQUIRED",
            },
            approvedResponseFields=_PRICING_FIELDS,
            droppedFields=[
                "prices[].max_price",
                "prices[].discount_value",
                "prices[].discount_percent",
                "prices[].state",
                "prices[].operation_type",
            ],
            droppedFieldReasons=(
                "max_price/discounts are commercial-strategy internals; state/operation_type "
                "are extra commercial-condition dimensions not required for registered table sale price."
            ),
            shape="scalar OpenAPI shape wrapping nested product+prices payload",
            projectionMode="nested",
            projectionFeasibility="SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR",
            perOperationProjectorRequired=False,
            argumentConstraints={},
            pagination="none — prices[] is a table list; global execute_max_items=50 slices arrays",
            limits={
                "maxModelVisibleItems": 50,
                "executeMaxResponseBytes": 65536,
                "note": "Backend returns all DA1 rows for the product; DAVI generic array slice caps at 50.",
            },
            timeSemantics=(
                "prices[].valid_from is DA1_DATVIG as stored. prices[].active is DA1_ATIVO as stored. "
                "No start_date/end_date filter exists. The route does not prove that returned rows "
                "are only currently active/effective. DAVI may report the row active flag, valid_from "
                "and registered sale_price; it must not claim sale_price is the current effective price."
            ),
            monetarySemantics=(
                "sale_price is DA1_PRCVEN table unit sale price. Tax inclusion/exclusion and "
                "gross/net meaning are NOT proven in source — do not freeze a net/gross claim. "
                "lot_quantity (DA1_QTDLOT) is the lot basis for that row."
            ),
            currencySemantics=(
                "currency is DA1_MOEDA as stored (Protheus currency code). ISO 4217 mapping "
                "to BRL is NOT proven in source; do not assume BRL. Keep the raw field."
            ),
            unitSemantics=(
                "product.unit is SB1 B1_UM catalog unit. sale_price is per catalog unit on the "
                "price-table row, interpreted with prices[].lot_quantity."
            ),
            derivedFields=[],
            completeness=(
                "Complete for the DA1 rows returned in this payload after DAVI array cap. "
                "truncated=true if more than 50 tables. Do not imply complete market pricing "
                "and do not imply every row is the current effective price."
            ),
            provenance=_PROVENANCE,
            semanticAliasesPtBr=[
                "preço do produto",
                "preço comercial",
                "tabela de preço",
                "preço de venda",
            ],
            semanticAliasesEn=[
                "product sale price",
                "commercial price table",
                "product pricing",
            ],
            privacy=(
                "Sale-table prices are commercially sensitive but not prohibited merely for "
                "being monetary. Drop discounts, max_price, state and operation_type. No "
                "customer-specific negotiated price field is present in the proven DTO."
            ),
            risk={
                "databaseQueryCost": "LOW",
                "responseVolume": "LOW",
                "nesting": "LOW",
                "historicalScan": "LOW",
                "recursiveBom": "NONE",
                "downstreamUseCases": "LOW",
                "timeoutRisk": "LOW",
                "overall": "LOW",
            },
            observability=_SAFE_OBS,
            negativeAuthzPlan=_NEG_AUTHZ,
            quarantineDeltaRequired=[
                _keep_global("preco", "preço do produto / preço comercial / preço de venda"),
                _keep_global("price", "product sale price / product pricing"),
                _keep_global("pricing", "product pricing / commercial price table"),
            ],
            openGaps=[
                "ISO 4217 currency mapping for DA1_MOEDA is not proven",
                "Tax inclusion/exclusion of DA1_PRCVEN is not proven",
                "SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN",
            ],
            failClosedInjectedSiblings=[
                "internal_debug",
                "raw_sql",
                "legacy",
                "secret",
                "unexpected",
                "max_price",
                "discount_value",
                "discount_percent",
                "state",
                "operation_type",
                "standard_cost",
                "unit_price",
                "customer_reference",
            ],
            httpRoute="GET /products/{code}/pricing",
            routeHandler="product_pricing",
            candidateClass="PRIMARY",
            runtimeCost="LOW",
        ),
        _record(
            capabilityId="product.purchase.price_history",
            businessName={
                "ptBr": "Histórico de preço de compra da matéria-prima",
                "en": "Raw-material purchase price history",
            },
            businessNeed=(
                "Bounded recent purchase-price series for one product within a resolved "
                "date window, limited to the latest N canonical inbound-NF occurrences, "
                "with consecutive variation on the returned set — not purchase-order "
                "listings, not commercial sale tables, and not a complete-period history."
            ),
            status="FROZEN_FOR_IMPLEMENTATION",
            canonicalOperations=["get_product_purchase_price_history"],
            canonicalUseCases=["GetProductPurchasePriceHistoryUseCase"],
            readPrepareAct="READ",
            technicalOwner=technical_owner,
            businessOwner=business_owner,
            sourceOfTruth=(
                "GET /products/{code}/purchase-price-history → "
                "GetProductPurchasePriceHistoryUseCase → ProductRawMaterialPriceRepository."
                "fetch_purchase_price_history: SD1010 valid inbound NF (D1_VUNIT, D1_QUANT, "
                "D1_TOTAL, D1_PICM, D1_DOC, D1_EMISSAO) + SA2010 supplier name. "
                "variation_percent/previous_unit_price/summary are CANONICAL_BACKEND_CALCULATION "
                "in product_raw_material_price_service.enrich_price_history_with_variation / "
                "summarize_price_history."
            ),
            identity="END_USER_ACCOUNT",
            backendAuthz=(
                "PROVEN: @require_permission(API_DELPI_ACCESS) on get_purchase_price_history"
            ),
            approvedInputFields=["code", "branch", "start_date", "end_date", "history_limit"],
            requiredInputFields=["code"],
            optionalInputFields=["branch", "start_date", "end_date", "history_limit"],
            inputMinimization={
                "code": "APPROVED_REQUIRED",
                "branch": "APPROVED_OPTIONAL",
                "start_date": "APPROVED_OPTIONAL",
                "end_date": "APPROVED_OPTIONAL",
                "history_limit": "APPROVED_OPTIONAL",
                "date_start": "NOT_EXPOSED",
                "date_end": "NOT_EXPOSED",
            },
            approvedResponseFields=_HISTORY_FIELDS,
            droppedFields=[
                "product.registered_last_purchase_price",
                "product.registered_last_purchase_date",
                "product.registered_icms_rate",
                "product.standard_cost",
                "items[].entry_date",
                "items[].invoice_series",
                "items[].supplier_store",
                "items[].icms_value",
                "items[].purchase_order",
                "items[].branch",
            ],
            shape="playbook_report",
            projectionMode="nested",
            projectionFeasibility="SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR",
            perOperationProjectorRequired=False,
            argumentConstraints={
                "dateRange": {
                    "startField": "start_date",
                    "endField": "end_date",
                    "maxDays": 365,
                },
                "argumentLimits": {
                    "history_limit": {"minimum": 1, "maximum": 50, "default": 24},
                },
            },
            pagination="none — history_limit TOP N, not page/page_size",
            limits={
                "backendDefaultLimit": 24,
                "backendMaxLimit": 200,
                "daviDefaultLimit": 24,
                "daviMaxLimit": 50,
                "backendDefaultDateWindowDays": 365,
                "daviMaxDateRangeDays": 365,
                "rationale": (
                    "Backend default 24/365 already matches the business grain of recent "
                    "price evolution. DAVI tightens only the item cap 200→50 to the global "
                    "execute_max_items budget. Do not silently clamp dates."
                ),
            },
            timeSemantics=(
                "Canonical HTTP filters are start_date and end_date. If omitted, backend "
                "sets start=today-365d and exclusive end=today+1 (resolve_history_date_range). "
                "Default date_basis is issue (D1_EMISSAO). Proven ordering in "
                "fetch_purchase_price_history: D1_EMISSAO DESC, D1_DTDIGIT DESC, R_E_C_N_O_ DESC "
                "(latest-first). date_start/date_end are legacy NOT_EXPOSED. Returned "
                "start_date / date_end_exclusive are provenance of the resolved window, not "
                "proof that every matching NF in that window was returned."
            ),
            monetarySemantics=(
                "items[].unit_price is SD1 D1_VUNIT NF unit price; total_value is D1_TOTAL; "
                "icms_rate is D1_PICM. Gross/net of ICMS is not fully defined in source — "
                "expose unit_price + icms_rate together. summary min/max/avg and "
                "variation_percent are backend calculations over the returned items only."
            ),
            currencySemantics=(
                "No D1_MOEDA/currency field exists on the NF history payload. Currency is "
                "UNPROVEN; do not assume BRL. Do not invent a currency field."
            ),
            unitSemantics=(
                "product.unit is B1_UM. quantity is D1_QUANT in that catalog unit. "
                "unit_price is per that unit; total_value is the NF line total."
            ),
            derivedFields=[
                {
                    "field": "items[].previous_unit_price",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "product_raw_material_price_service.enrich_price_history_with_variation",
                },
                {
                    "field": "items[].variation_percent",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "product_raw_material_price_service.enrich_price_history_with_variation",
                    "formula": "((unit_price - previous_unit_price) / previous_unit_price) * 100 when previous > 0",
                },
                {
                    "field": "summary.*",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "product_raw_material_price_service.summarize_price_history",
                    "completenessAssumption": (
                        "Aggregates the returned TOP N items only. Does not prove total matching "
                        "NFs in the whole requested period."
                    ),
                },
            ],
            completeness=(
                "dataset_scope = bounded latest-N occurrences within the resolved date window. "
                "Default N=24, DAVI max N=50, requested window max 365 days. "
                "history_limit bounds the dataset returned by the canonical backend TOP N. "
                "summary fields describe that returned bounded dataset only. "
                "summary.total_purchases does NOT prove total matching NFs in the whole period. "
                "Backend does not expose total, has_more, or a next cursor. "
                "full_period_completeness = NOT_PROVEN. "
                "DAVI is_complete/truncated describe DAVI projection/transport completeness only. "
                "is_complete=true MUST NOT be interpreted as 'there are no more matching purchases "
                "in the requested period'. truncated=true only when DAVI projection sliced the "
                "already-returned payload (e.g. execute_max_items), not when the backend TOP N "
                "quietly omitted older matching records."
            ),
            datasetScope="bounded latest-N occurrences within the resolved date window",
            fullPeriodCompleteness="NOT_PROVEN",
            provenOrdering="D1_EMISSAO DESC, D1_DTDIGIT DESC, R_E_C_N_O_ DESC (default date_basis=issue)",
            provenance=_PROVENANCE,
            semanticAliasesPtBr=[
                "histórico de preço de compra",
                "evolução de preço de compra",
                "preço de compra da matéria-prima",
            ],
            semanticAliasesEn=[
                "purchase price history",
                "buying price history",
                "raw material purchase price history",
            ],
            privacy=(
                "Supplier name/code are already in eligible get_product_purchases. History "
                "has no A2_CGC. Drop registered cadastro costs and unused NF internals."
            ),
            risk={
                "databaseQueryCost": "MEDIUM",
                "responseVolume": "MEDIUM",
                "nesting": "LOW",
                "historicalScan": "MEDIUM",
                "recursiveBom": "NONE",
                "downstreamUseCases": "LOW",
                "timeoutRisk": "MEDIUM",
                "overall": "MEDIUM",
            },
            observability=_SAFE_OBS,
            negativeAuthzPlan=_NEG_AUTHZ,
            quarantineDeltaRequired=[
                _keep_global("preco", "histórico de preço de compra / preço de compra da matéria-prima"),
                _keep_global("price", "purchase price history"),
            ],
            openGaps=[
                "NF currency is absent from the payload (UNPROVEN)",
                "SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN",
            ],
            failClosedInjectedSiblings=[
                "internal_debug",
                "raw_sql",
                "legacy",
                "secret",
                "unexpected",
                "supplier_tax_id",
                "registered_last_purchase_price",
                "standard_cost",
                "sale_price",
                "customer_reference",
            ],
            httpRoute="GET /products/{code}/purchase-price-history",
            routeHandler="get_purchase_price_history",
            candidateClass="PRIMARY",
            distinctFrom=[
                "get_product_purchases is SC7010 purchase orders; DAVI currently drops unit_price there",
                "get_product_pricing is DA1 commercial sale tables",
                "get_product_last_purchase is unbounded TOP 1 latest valid NF",
            ],
        ),
        _record(
            capabilityId="product.raw_material.price_intelligence",
            businessName={
                "ptBr": "Inteligência de preço de matéria-prima",
                "en": "Raw-material price intelligence",
            },
            businessNeed=(
                "Classified overlay of last-purchase snapshot, price-history summary, "
                "budget-history summary and backend price_status/indicators for one MP."
            ),
            status="DEFER",
            canonicalOperations=["get_product_raw_material_price_intelligence"],
            canonicalUseCases=["GetProductRawMaterialPriceIntelligenceUseCase"],
            readPrepareAct="READ",
            technicalOwner=technical_owner,
            businessOwner=business_owner,
            sourceOfTruth=(
                "GET /products/{code}/raw-material-price-intelligence → "
                "GetProductRawMaterialPriceIntelligenceUseCase composes fetch_last_purchase "
                "+ fetch_purchase_price_history + fetch_purchase_budget_history (SC1010 UNION "
                "SC7010, no TOP/limit) + classify_price_status / build_indicators."
            ),
            identity="END_USER_ACCOUNT",
            backendAuthz=(
                "PROVEN: @require_permission(API_DELPI_ACCESS) on get_raw_material_price_intelligence"
            ),
            approvedInputFields=[],
            requiredInputFields=["code"],
            optionalInputFields=["branch", "start_date", "end_date", "history_limit"],
            approvedResponseFields=[],
            shape="composite_analysis",
            projectionMode="nested",
            projectionFeasibility="SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR",
            perOperationProjectorRequired=False,
            argumentConstraints={},
            pagination="none",
            limits={},
            timeSemantics=(
                "Same resolve_history_date_range as purchase price history (default 365 days). "
                "last_purchase inside the composite is unbounded TOP 1, independent of the window."
            ),
            monetarySemantics=(
                "Mix of AUTHORITATIVE_RAW_FACT (NF/cadastro prices), CANONICAL_BACKEND_CALCULATION "
                "(variation, summaries, indicators) and CANONICAL_BACKEND_CLASSIFICATION "
                "(price_status ESTAVEL/ALTA DE PRECO/QUEDA DE PRECO). DAVI must not relabel "
                "model inference as source fact."
            ),
            currencySemantics="Same UNPROVEN NF currency gap as purchase price history.",
            unitSemantics="product.unit from SB1; monetary fields inherit sibling semantics.",
            derivedFields=[
                {
                    "field": "price_status",
                    "class": "CANONICAL_BACKEND_CLASSIFICATION",
                    "owner": "classify_price_status",
                    "inputs": "last variation_percent vs ±2 percent band",
                },
                {
                    "field": "indicators.*",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "build_indicators",
                },
            ],
            completeness=(
                "Would still execute unbounded budget_history even if DAVI projected summaries only."
            ),
            provenance=_PROVENANCE,
            semanticAliasesPtBr=[
                "inteligência de preço de matéria-prima",
                "análise de preço de mp",
                "status de preço da mp",
            ],
            semanticAliasesEn=[
                "raw material price intelligence",
                "mp price analysis",
            ],
            privacy="Composite includes last_purchase.supplier_tax_id (A2_CGC) — must never be approved.",
            risk={
                "databaseQueryCost": "HIGH",
                "responseVolume": "HIGH",
                "nesting": "HIGH",
                "historicalScan": "HIGH",
                "recursiveBom": "NONE",
                "downstreamUseCases": "HIGH",
                "timeoutRisk": "HIGH",
                "overall": "HIGH",
            },
            observability=_SAFE_OBS,
            negativeAuthzPlan=_NEG_AUTHZ,
            quarantineDeltaRequired=[
                _keep_global("preco", "keep global; do not own via this deferred capability"),
                _keep_global("custo", "keep global; do not own via this deferred capability"),
                _keep_global("cost", "keep global; do not own via this deferred capability"),
            ],
            openGaps=[
                "fetch_purchase_budget_history has no item limit (unbounded UNION ALL in the date window)",
                "Composite dump overlaps last_purchase + purchase_price_history",
                "No summaries-only backend contract exists to isolate price_status cheaply",
                "supplier_tax_id present on last_purchase nested object",
            ],
            deferReason=(
                "Distinct classified overlay exists, but executing the canonical operation "
                "always scans unbounded SC+PC budget history and dumps sibling item arrays. "
                "Projection cannot reduce backend work. Freeze last_valid + price_history "
                "instead; do not promote a mega-intelligence capability in this wave."
            ),
            httpRoute="GET /products/{code}/raw-material-price-intelligence",
            routeHandler="get_raw_material_price_intelligence",
            candidateClass="PRIMARY",
        ),
        _record(
            capabilityId="product.cost.impact_simulation",
            businessName={
                "ptBr": "Simulação de impacto de custo do PA",
                "en": "Finished-product cost impact simulation",
            },
            businessNeed=(
                "Authorized compute-only ranking of raw materials that most impact the "
                "material cost of one finished product (PA), optionally applying a percent "
                "adjustment. Result is not an approved price, persisted cost, purchasing "
                "authorization, accounting entry or business approval."
            ),
            status="DEFER_FROM_READ_WAVE",
            canonicalOperations=["get_product_cost_impact_simulation"],
            canonicalUseCases=["GetProductCostImpactSimulationUseCase"],
            readPrepareAct="PREPARE",
            technicalOwner=technical_owner,
            businessOwner=business_owner,
            sourceOfTruth=(
                "GET /products/{code}/cost-impact-simulation → "
                "GetProductCostImpactSimulationUseCase → ProductCostImpactRepository "
                "(SB1010 header B1_CUSTD/B1_UCALSTD + recursive SG1010 BOM MP aggregation "
                "OPTION MAXRECURSION 0) → build_cost_impact_simulation (in-memory only). "
                "Unit basis: ProductCostImpactUnitService + product_cost_impact_units.json "
                "(MI = 1000 pieces). PA-only (rejects non-PA)."
            ),
            identity="END_USER_ACCOUNT",
            backendAuthz=(
                "PROVEN: @require_permission(API_DELPI_ACCESS) on get_cost_impact_simulation"
            ),
            approvedInputFields=[
                "code",
                "max_depth",
                "price_source",
                "adjustment_percent",
                "top_n",
            ],
            requiredInputFields=["code"],
            optionalInputFields=["max_depth", "price_source", "adjustment_percent", "top_n"],
            inputMinimization={
                "code": "APPROVED_REQUIRED",
                "max_depth": "APPROVED_OPTIONAL",
                "price_source": "APPROVED_OPTIONAL",
                "adjustment_percent": "APPROVED_OPTIONAL",
                "top_n": "APPROVED_OPTIONAL",
            },
            approvedResponseFields=_SIMULATION_FIELDS,
            droppedFields=[
                "materials.items[].path",
                "materials.items[].group_code",
                "product.last_purchase_price",
                "product.last_purchase_date",
                "product.pa_reference",
            ],
            shape="composite_analysis",
            projectionMode="nested",
            projectionFeasibility="SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR",
            perOperationProjectorRequired=False,
            argumentConstraints={
                "argumentLimits": {
                    "max_depth": {"minimum": 1, "maximum": 8, "default": 8},
                    "top_n": {"minimum": 1, "maximum": 50, "default": 50},
                    "adjustment_percent": {"minimum": -100, "maximum": 1000, "default": 0},
                },
            },
            pagination="none — top_n ranking slice, not page/page_size",
            limits={
                "backendDefaultMaxDepth": 50,
                "backendMaxDepthQuery": 100,
                "daviMaxDepth": 8,
                "backendTopNMax": 200,
                "daviTopNMax": 50,
                "adjustmentPercentBackend": {"minimum": -100, "maximum": 1000},
                "priceSourceEnum": ["standard_cost", "last_purchase"],
            },
            timeSemantics=(
                "No start_date/end_date. BOM validity is ProductBomValidityFilterService "
                "for today. product.standard_cost_date is B1_UCALSTD cadastro date. "
                "Simulation is a point-in-time compute against current BOM + current costs."
            ),
            monetarySemantics=(
                "unit_cost is CANONICAL_BACKEND_CALCULATION from price_source "
                "(B1_CUSTD standard_cost or B1_UPRC last_purchase, with fallback). "
                "extended_cost = quantity_per_pa * unit_cost. simulated_* apply "
                "adjustment_percent multiplier. Impact percents are backend calculations. "
                "simulation result != approved price / persisted product cost / purchasing "
                "authorization / accounting entry / business approval. GET compute-only: "
                "no INSERT/UPDATE/DELETE in use case, service or repository."
            ),
            currencySemantics=(
                "B1_CUSTD/B1_UPRC have no currency field in this payload. Currency UNPROVEN; "
                "do not assume BRL. Do not invent a currency field."
            ),
            unitSemantics=(
                "quantity_per_pa is normalized via ProductPaBomReferenceService for 1 PA. "
                "cost_basis documents MI vs piece: parentUnits.MI catalogPiecesPerUnit=1000. "
                "materials.items[].unit is the MP catalog unit. Do not expose amount without "
                "these unit fields."
            ),
            derivedFields=[
                {
                    "field": "unit_cost / simulated_* / extended_cost / cost_delta / impact percents",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "product_cost_impact_service.build_cost_impact_simulation",
                },
                {
                    "field": "summary.pa_cost_comparable / material_to_pa_cost_ratio",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "ProductCostImpactUnitService.resolve_comparability",
                    "assumptions": "comparable only if ratio in [0.05, 5.0]",
                },
                {
                    "field": "cost_basis.*",
                    "class": "CANONICAL_BACKEND_CALCULATION",
                    "owner": "ProductCostImpactUnitService.build_cost_basis",
                    "config": "app/content/product_cost_impact_units.json",
                },
            ],
            completeness=(
                "Ranking is complete for MP components found in the bounded BOM explosion "
                "(max_depth). materials.total is all ranked MPs; materials.returned is the "
                "top_n slice. truncated when returned < total. Not a complete cost accounting "
                "analysis and not a complete market simulation."
            ),
            provenance=_PROVENANCE,
            semanticAliasesPtBr=[
                "impacto no custo",
                "simulação de custo",
                "simular impacto de custo",
                "matérias-primas que mais impactam o custo",
            ],
            semanticAliasesEn=[
                "cost impact simulation",
                "simulate cost impact",
                "raw materials cost impact",
            ],
            privacy=(
                "Internal cost/margin-adjacent ranking. Minimize to ranking + simulation totals. "
                "Drop BOM path. No customer/supplier PII in this payload."
            ),
            risk={
                "databaseQueryCost": "HIGH",
                "responseVolume": "MEDIUM",
                "nesting": "MEDIUM",
                "historicalScan": "LOW",
                "recursiveBom": "HIGH",
                "downstreamUseCases": "LOW",
                "timeoutRisk": "HIGH",
                "overall": "HIGH",
            },
            observability=_SAFE_OBS,
            negativeAuthzPlan=_NEG_AUTHZ,
            quarantineDeltaRequired=[
                {
                    "token": "custo",
                    "action": "KEEP_GLOBAL",
                    "rationale": (
                        "Cost simulation is PREPARE / DEFER_FROM_READ_WAVE. Do not own `custo` "
                        "in the READ broker. Keep the global token; a future PREPARE track may "
                        "own precise aliases later."
                    ),
                },
                {
                    "token": "cost",
                    "action": "KEEP_GLOBAL",
                    "rationale": (
                        "Cost simulation is PREPARE / DEFER_FROM_READ_WAVE. Do not own `cost` "
                        "in the READ broker."
                    ),
                },
            ],
            openGaps=[
                "Currency of B1_CUSTD/B1_UPRC is UNPROVEN",
                "SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN",
                "Recursive BOM with MAXRECURSION 0 remains HIGH cost even with DAVI max_depth=8",
            ],
            failClosedInjectedSiblings=[
                "internal_debug",
                "raw_sql",
                "legacy",
                "secret",
                "unexpected",
                "path",
                "sale_price",
                "supplier_tax_id",
                "customer_reference",
            ],
            httpRoute="GET /products/{code}/cost-impact-simulation",
            routeHandler="get_cost_impact_simulation",
            candidateClass="PRIMARY",
            readWavePromotion="NO",
            deferReason=(
                "HTTP GET compute-only simulation is PREPARE, not READ, under the canonical "
                "DAVI capability model (preview/draft/simulação sem persistir). Architecture "
                "Acceptance reclassified it out of Wave 2 READ. Analysis of source, AuthZ, "
                "projection, monetary/unit/currency gaps and simulation boundary remains valid "
                "for a future PREPARE track. Do not create PREPARE runtime, MCP tools or Agent "
                "Instruction changes in Wave 2."
            ),
            futureTrack="DAVI-PREPARE-GOVERNED-SIMULATION (not opened here)",
            simulationBoundary={
                "computeOnly": True,
                "sideEffects": "NONE_PROVEN",
                "httpGetDoesNotImplyRead": True,
                "notApprovedPrice": True,
                "notPersistedProductCost": True,
                "notPurchasingAuthorization": True,
                "notAccountingEntry": True,
                "notBusinessApproval": True,
                "notAct": True,
                "writeSemantics": "FORBIDDEN",
            },
        ),
        _record(
            capabilityId="product.purchase.last_valid",
            businessName={
                "ptBr": "Última compra válida da matéria-prima",
                "en": "Last valid inbound purchase snapshot",
            },
            businessNeed=(
                "Authorized latest valid inbound NF snapshot for one product (supplier, "
                "unit price, quantity, date) without a date window and without a history series."
            ),
            status="FROZEN_FOR_IMPLEMENTATION",
            canonicalOperations=["get_product_last_purchase"],
            canonicalUseCases=["GetProductLastPurchaseUseCase"],
            readPrepareAct="READ",
            technicalOwner=technical_owner,
            businessOwner=business_owner,
            sourceOfTruth=(
                "GET /products/{code}/last-purchase → GetProductLastPurchaseUseCase → "
                "ProductRawMaterialPriceRepository.fetch_last_purchase: SD1010 TOP 1 valid "
                "inbound NF ordered by D1_EMISSAO/D1_DTDIGIT/D1_DOC DESC + SA2010 name. "
                "No date filter. Distinct from purchase_price_history default 365-day window."
            ),
            identity="END_USER_ACCOUNT",
            backendAuthz="PROVEN: @require_permission(API_DELPI_ACCESS) on get_last_purchase",
            approvedInputFields=["code", "branch"],
            requiredInputFields=["code"],
            optionalInputFields=["branch"],
            inputMinimization={
                "code": "APPROVED_REQUIRED",
                "branch": "APPROVED_OPTIONAL",
            },
            approvedResponseFields=_LAST_PURCHASE_FIELDS,
            droppedFields=[
                "last_purchase.supplier_tax_id",
                "last_purchase.supplier_state",
                "last_purchase.supplier_part_number",
                "last_purchase.invoice_series",
                "last_purchase.entry_date",
                "last_purchase.supplier_store",
                "last_purchase.icms_value",
                "product.registered_last_purchase_price",
                "product.standard_cost",
            ],
            shape="playbook_report",
            projectionMode="nested",
            projectionFeasibility="SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR",
            perOperationProjectorRequired=False,
            argumentConstraints={},
            pagination="none — single snapshot",
            limits={"maxItems": 1},
            timeSemantics=(
                "No start_date/end_date. Returns the latest valid NF regardless of age. "
                "This is the proven distinction versus purchase price history (windowed series)."
            ),
            monetarySemantics=(
                "last_purchase.unit_price is D1_VUNIT; total_value is D1_TOTAL; icms_rate is "
                "D1_PICM. Same UNPROVEN gross/net caveat as history."
            ),
            currencySemantics="No currency field on last_purchase payload. UNPROVEN; do not assume BRL.",
            unitSemantics="product.unit is B1_UM; quantity/unit_price follow that catalog unit.",
            derivedFields=[],
            completeness=(
                "Complete as the single latest valid inbound NF after PurchaseValidityFilterService, "
                "or last_purchase=null if none. Not a complete purchase history."
            ),
            provenance=_PROVENANCE,
            semanticAliasesPtBr=[
                "último preço de compra",
                "última compra da matéria-prima",
                "última NF de compra",
            ],
            semanticAliasesEn=[
                "last purchase price",
                "last valid purchase",
                "latest inbound invoice price",
            ],
            privacy=(
                "MUST drop supplier_tax_id (SA2 A2_CGC). Keep supplier_name/code consistent "
                "with eligible purchases list."
            ),
            risk={
                "databaseQueryCost": "LOW",
                "responseVolume": "LOW",
                "nesting": "LOW",
                "historicalScan": "LOW",
                "recursiveBom": "NONE",
                "downstreamUseCases": "LOW",
                "timeoutRisk": "LOW",
                "overall": "LOW",
            },
            observability=_SAFE_OBS,
            negativeAuthzPlan=_NEG_AUTHZ,
            quarantineDeltaRequired=[
                _keep_global("preco", "último preço de compra / última NF de compra"),
                _keep_global("price", "last purchase price"),
            ],
            openGaps=[
                "NF currency UNPROVEN",
                "SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN",
            ],
            failClosedInjectedSiblings=[
                "internal_debug",
                "raw_sql",
                "legacy",
                "secret",
                "unexpected",
                "supplier_tax_id",
                "sale_price",
                "standard_cost",
                "customer_reference",
            ],
            httpRoute="GET /products/{code}/last-purchase",
            routeHandler="get_last_purchase",
            candidateClass="SECONDARY",
            notRedundantReason=(
                "Same SD1 source as history, but no date window and TOP 1. History default "
                "365d can miss an older last NF. get_product_purchases is SC7 POs without "
                "DAVI unit_price. Therefore a distinct cheap snapshot capability."
            ),
        ),
        _record(
            capabilityId="product.snapshot.summary",
            businessName={
                "ptBr": "Resumo composto do produto",
                "en": "Product composite summary",
            },
            businessNeed=(
                "A light cadastro+estoque+preços snapshot. Revalidated after economic inventory."
            ),
            status="DEFER",
            canonicalOperations=["get_product_summary"],
            canonicalUseCases=["get_product_summary handler (composite search+stock+pricing)"],
            readPrepareAct="READ",
            technicalOwner=technical_owner,
            businessOwner=business_owner,
            sourceOfTruth=(
                "GET /products/{code}/summary composes search_products + list stock[:10] + "
                "GetProductPricingUseCase. Not a distinct minimized business contract."
            ),
            identity="END_USER_ACCOUNT",
            backendAuthz="PROVEN: @require_permission(API_DELPI_ACCESS) on get_product_summary",
            approvedInputFields=[],
            requiredInputFields=["code"],
            optionalInputFields=[],
            approvedResponseFields=[],
            shape="product_snapshot",
            projectionMode="nested",
            projectionFeasibility="SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR",
            perOperationProjectorRequired=False,
            argumentConstraints={},
            pagination="none",
            limits={},
            timeSemantics="No dedicated time contract; stock and prices are current slices.",
            monetarySemantics="Would duplicate product.commercial.pricing if prices were included.",
            currencySemantics="Same DA1_MOEDA gap as pricing.",
            unitSemantics="Duplicates search/stock/pricing units.",
            derivedFields=[],
            completeness="Not a distinct complete snapshot; mega-summary is forbidden.",
            provenance=_PROVENANCE,
            semanticAliasesPtBr=[],
            semanticAliasesEn=[],
            privacy="Composite would mix stock with commercial prices.",
            risk={"overall": "MEDIUM"},
            observability=_SAFE_OBS,
            negativeAuthzPlan=_NEG_AUTHZ,
            quarantineDeltaRequired=[],
            openGaps=[
                "No distinct minimized semantic snapshot that does not duplicate search+stock+pricing"
            ],
            deferReason=(
                "Pricing becoming governable does not promote summary. Without prices it "
                "duplicates search+stock; with prices it is a mega-summary. Remain DEFER."
            ),
            httpRoute="GET /products/{code}/summary",
            routeHandler="get_product_summary",
            candidateClass="SECONDARY",
        ),
    ]


def frozen_records(caps: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    caps = caps or candidate_records()
    return [c for c in caps if c["status"] == "FROZEN_FOR_IMPLEMENTATION"]


def load_allowlist() -> dict[str, Any]:
    path = api_root() / "app/content/davi_external_read_allowlist.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_baseline_operations() -> dict[str, dict[str, Any]]:
    path = api_root() / "app/content/openapi_baseline.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for item in payload.get("operations") or payload.get("paths") or []:
        if not isinstance(item, dict):
            continue
        oid = (item.get("operationId") or "").strip()
        if oid:
            out[oid] = item
    return out


def _load_operation_id_constants() -> dict[str, str]:
    from app.interface.http import openapi_agent_metadata as meta

    mapping: dict[str, str] = {}
    for name, value in vars(meta).items():
        if isinstance(value, dict) and isinstance(value.get("operation_id"), str):
            mapping[name] = value["operation_id"].strip()
    return mapping


def scan_product_route_authz() -> dict[str, dict[str, Any]]:
    """PROVEN only when require_permission shares the handler with the OpenAPI splat."""
    const_oids = _load_operation_id_constants()
    path = api_root() / "app/interface/http/routes/product_routes.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        op_ids: list[str] = []
        perms: list[str] = []
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            func_name = ""
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr
            if func_name in {"require_permission", "require_any_permission"}:
                for arg in dec.args:
                    if isinstance(arg, ast.Name):
                        perms.append(arg.id)
            for kw in dec.keywords:
                if kw.arg == "operation_id" and isinstance(kw.value, ast.Constant):
                    if isinstance(kw.value.value, str):
                        op_ids.append(kw.value.value)
                if kw.arg is None and isinstance(kw.value, ast.Name):
                    mapped = const_oids.get(kw.value.id)
                    if mapped:
                        op_ids.append(mapped)
        for oid in op_ids:
            found[oid] = {
                "handler": node.name,
                "permissions": perms,
                "authzEvidence": "PROVEN" if "API_DELPI_ACCESS" in perms else "TO_INVENTORY",
            }
    return found


def simulation_has_persistence() -> bool:
    files = [
        api_root()
        / "app/application/use_cases/product/get_product_cost_impact_simulation_use_case.py",
        api_root() / "app/application/services/product/product_cost_impact_service.py",
        api_root()
        / "app/infrastructure/persistence/totvs/product_repositories/product_cost_impact_repository.py",
    ]
    pattern = re.compile(r"\b(INSERT|UPDATE|DELETE|commit\(|flush\()\b", re.I)
    for path in files:
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            return True
    return False


def validate_against_source(caps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    caps = caps or candidate_records()
    baseline = load_baseline_operations()
    allow = load_allowlist()
    eligible_ids = {
        item.get("operationId")
        for item in allow.get("operations") or []
        if isinstance(item, dict)
    }
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    issues: list[str] = []
    proofs: list[dict[str, Any]] = []
    authz_index = scan_product_route_authz()
    for cap in caps:
        for oid in cap["canonicalOperations"]:
            op = baseline.get(oid)
            if not op:
                issues.append(f"{oid}: missing from OpenAPI baseline")
                continue
            method = (op.get("method") or "").upper()
            if method != "GET":
                issues.append(f"{oid}: method {method} != GET")
            params = {
                p.get("name")
                for p in (op.get("parameters") or [])
                if isinstance(p, dict)
            }
            for name in cap["approvedInputFields"]:
                if name not in params:
                    issues.append(f"{oid}: approved input `{name}` not in OpenAPI parameters")
            authz = authz_index.get(oid) or {}
            if authz.get("authzEvidence") != "PROVEN":
                issues.append(f"{oid}: API_DELPI_ACCESS decorator not proven on handler {authz}")
            if oid in eligible_ids:
                if cap.get("status") in {"DEFER", "DEFER_FROM_READ_WAVE"}:
                    issues.append(f"{oid}: deferred capability unexpectedly allowlisted")
                elif cap.get("status") != "FROZEN_FOR_IMPLEMENTATION":
                    issues.append(f"{oid}: unexpectedly already allowlisted")
            proofs.append(
                {
                    "operationId": oid,
                    "method": method,
                    "path": op.get("path"),
                    "shape": (op.get("xDelpi") or {}).get("shape"),
                    "parameters": sorted(x for x in params if x),
                    "authz": authz,
                    "currentlyEligible": oid in eligible_ids,
                    "explicitlyNotApproved": oid in blocked,
                }
            )
    if simulation_has_persistence():
        issues.append("cost impact simulation source contains persistence markers")
    tokens = allow.get("retrievalQuarantineTokens") or []
    for token in ECONOMIC_QUARANTINE_TOKENS:
        if token not in tokens:
            issues.append(f"quarantine token `{token}` missing from allowlist")
    return {"ok": not issues, "issues": issues, "proofs": proofs}


def retrieval_collision_plan() -> list[dict[str, str]]:
    return [
        {
            "intent": "preço do produto",
            "owner": "product.commercial.pricing",
            "not": "purchase history / last purchase / intelligence / simulation",
        },
        {
            "intent": "preço comercial / tabela de preço / preço de venda",
            "owner": "product.commercial.pricing",
            "not": "purchase-side capabilities",
        },
        {
            "intent": "preço de compra",
            "owner": "product.purchase.price_history",
            "not": "commercial pricing; too broad for last_valid unless 'último' is present",
        },
        {
            "intent": "histórico de preço de compra / evolução de preço de compra",
            "owner": "product.purchase.price_history",
            "not": "last_valid snapshot",
        },
        {
            "intent": "último preço de compra / última NF de compra",
            "owner": "product.purchase.last_valid",
            "not": "history series",
        },
        {
            "intent": "inteligência de preço de matéria-prima / análise de preço de mp",
            "owner": "NONE_THIS_WAVE (capability DEFER; remain globally quarantined)",
            "not": "do not steal via broad preço aliases",
        },
        {
            "intent": "impacto no custo / simular impacto de custo",
            "owner": "NONE_THIS_READ_WAVE (PREPARE / DEFER_FROM_READ_WAVE; remain globally quarantined)",
            "not": "do not own custo/cost aliases in the READ broker",
        },
        {
            "intent": "preço / custo / produto (bare tokens)",
            "owner": "NONE — keep global quarantine; do not freeze these as aliases",
            "not": "all economic capabilities",
        },
    ]


def build_documents(*, source_head: str, origin_main: str) -> tuple[dict[str, Any], dict[str, Any]]:
    caps = candidate_records()
    frozen = frozen_records(caps)
    source = validate_against_source(caps)
    if not source["ok"]:
        raise ValueError("source validation failed: " + "; ".join(source["issues"]))
    allow = load_allowlist()
    budgets = json.loads(
        (api_root() / "app/content/davi_dynamic_read_budgets.json").read_text(encoding="utf-8")
    )
    inventory = {
        "metadata": {
            "taskId": TASK_ID,
            "artifact_class": ARTIFACT_CLASS,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_head": source_head,
            "origin_main": origin_main,
            "wave1_historical_freeze": "docs/integrations/evidence/davi-capability-wave-001-freeze.json",
            "correctionTaskId": CORRECTION_TASK_ID,
            "architectureDecision": "ACCEPT_WITH_RESIDUAL",
            "sourceFreezeSha": SOURCE_FREEZE_SHA,
            "implementation": "NOT_STARTED",
            "deploy": "NOT_REQUIRED",
            "live": "UNCHANGED_FROM_CURRENT_BASELINE",
        },
        "rebaseline": {
            "currentEligible": CURRENT_ELIGIBLE,
            "currentEligibleCount": len(CURRENT_ELIGIBLE),
            "mcpTools": MCP_TOOLS,
            "allowlistVersion": allow.get("version"),
            "executionDrift": "NONE",
        },
        "architecture": {
            "chain": (
                "Workspace Agent DAVI → DAVI App/Plugin → remote MCP → governed discovery → "
                "opaque candidate token → generic governed execute → API DELPI canonical "
                "route/use case → backend AuthZ → authoritative source → fail-closed "
                "model-safe projection → DAVI explanation"
            ),
            "daviIs": ["intelligence", "orchestration", "presentation"],
            "daviIsNot": [
                "source of truth",
                "RBAC",
                "permission engine",
                "domain owner",
                "SQL client",
                "generic HTTP proxy",
                "financial authority",
                "pricing authority",
            ],
            "authz": {
                "DAVI_BUSINESS_AUTHZ_OWNER": "NONE",
                "CANONICAL_BACKEND_AUTHZ": "REQUIRED_FINAL",
                "DAVI_LOCAL_RBAC": "FORBIDDEN",
                "DAVI_ROLE_AUTHZ": "FORBIDDEN",
                "DAVI_BRANCH_AUTHZ": "FORBIDDEN",
                "DAVI_OBJECT_LEVEL_AUTHZ": "FORBIDDEN",
                "identity": "END_USER_ACCOUNT",
                "DAVI_AUTH_SESSION_001": "TARGET / separate architecture track — not this freeze",
                "MCP_RATE_POLICY": "separate rollout governance — not a freeze blocker",
                "SECOND_USER_NEGATIVE_AUTHZ": "TEST_NOT_RUN",
            },
        },
        "budgets": budgets,
        "candidates": caps,
        "semanticRedundancies": [
            {
                "group": "RG-PRODUCT-ECONOMIC-SALE-VS-PURCHASE",
                "operations": ["get_product_pricing", "get_product_purchase_price_history"],
                "decision": "DISTINCT: DA1 sale tables vs SD1 inbound NF unit prices.",
            },
            {
                "group": "RG-PRODUCT-PURCHASE-ORDERS-VS-NF-PRICES",
                "operations": ["get_product_purchases", "get_product_purchase_price_history"],
                "decision": (
                    "DISTINCT: SC7010 POs (DAVI already eligible, unit_price dropped) vs "
                    "SD1 NF purchase-price series."
                ),
            },
            {
                "group": "RG-PRODUCT-LAST-PURCHASE-VS-HISTORY",
                "operations": ["get_product_last_purchase", "get_product_purchase_price_history"],
                "decision": (
                    "DISTINCT snapshot vs bounded latest-N windowed series. last_purchase has "
                    "no date filter (latest valid NF ever); history is TOP N inside a date "
                    "window and does not prove full-period completeness."
                ),
            },
            {
                "group": "RG-PRODUCT-INTELLIGENCE-COMPOSITE",
                "operations": [
                    "get_product_raw_material_price_intelligence",
                    "get_product_last_purchase",
                    "get_product_purchase_price_history",
                    "get_product_purchase_budget_history",
                ],
                "decision": "DEFER intelligence: composite dump + unbounded budget_history scan.",
            },
            {
                "group": "RG-PRODUCT-COST-SIMULATION-PREPARE",
                "operations": ["get_product_cost_impact_simulation"],
                "semantic_capability": "product.cost.impact_simulation",
                "decision": (
                    "HTTP GET != semantic READ. Compute-only simulation with adjustment_percent "
                    "and simulated_*/projected_* fields is PREPARE. Defer from Wave 2 READ."
                ),
            },
            {
                "group": "RG-PRODUCT-SUMMARY-AFTER-PRICING",
                "operations": [
                    "get_product_summary",
                    "search_products",
                    "get_product_stock",
                    "get_product_pricing",
                ],
                "decision": "Remain DEFER. Pricing freeze does not promote mega-summary.",
            },
        ],
        "quarantinePlan": {
            "currentEconomicTokens": ECONOMIC_QUARANTINE_TOKENS,
            "tokensToKeepGlobal": ECONOMIC_QUARANTINE_TOKENS,
            "globalTokensToRemove": [],
            "strategy": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES (same pattern as factory)",
            "collisionPlan": retrieval_collision_plan(),
        },
        "projectionAssessment": {
            "currentGenericProjectorSupport": "SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR for all frozen caps",
            "requiredExtension": "NONE",
            "perOperationProjectorRequired": "NO",
        },
        "runtimeImpactOfThisTask": {
            "allowlist": "UNCHANGED",
            "eligibility": "UNCHANGED",
            "retrieval": "UNCHANGED",
            "projection": "UNCHANGED",
            "executor": "UNCHANGED",
            "mcp": "UNCHANGED",
            "agent": "UNCHANGED",
            "api": "UNCHANGED",
        },
        "sourceValidation": source,
    }
    freeze = {
        "artifact_class": ARTIFACT_CLASS,
        "taskId": TASK_ID,
        "correctionTaskId": CORRECTION_TASK_ID,
        "architectureDecision": "ACCEPT_WITH_RESIDUAL",
        "sourceFreezeSha": SOURCE_FREEZE_SHA,
        "implementationTaskId": IMPLEMENTATION_TASK_ID,
        "generated_at": inventory["metadata"]["generated_at"],
        "source_head": source_head,
        "origin_main": origin_main,
        "status": "FROZEN_FOR_IMPLEMENTATION",
        "theme": "Product Economic Intelligence",
        "implementation": "NOT_STARTED",
        "deploy": "NOT_REQUIRED",
        "live": "UNCHANGED_FROM_CURRENT_BASELINE",
        "current_eligible": 10,
        "new_capabilities": len(frozen),
        "wave2_read_additions": 3,
        "expected_eligible_after_implementation": 13,
        "expected_mcp_tools_after_implementation": 3,
        "agent_instruction_change": "NO",
        "capability_ids": [c["capabilityId"] for c in frozen],
        "deferred_capability_ids": [
            c["capabilityId"] for c in caps if c["status"] in DEFERRED_STATUSES
        ],
        "capabilities": frozen,
        "all_candidates": [
            {
                "capabilityId": c["capabilityId"],
                "status": c["status"],
                "readPrepareAct": c["readPrepareAct"],
            }
            for c in caps
        ],
        "primary_decisions": {
            "product.commercial.pricing": "FROZEN_FOR_IMPLEMENTATION",
            "product.purchase.price_history": "FROZEN_FOR_IMPLEMENTATION",
            "product.raw_material.price_intelligence": "DEFER",
            "product.cost.impact_simulation": "PREPARE / DEFER_FROM_READ_WAVE",
        },
        "secondary_decisions": {
            "get_product_last_purchase": "FROZEN_FOR_IMPLEMENTATION as product.purchase.last_valid",
            "get_product_summary": "DEFER",
        },
        "quarantinePlan": inventory["quarantinePlan"],
        "projectionAssessment": inventory["projectionAssessment"],
        "runtimeImpactOfThisTask": inventory["runtimeImpactOfThisTask"],
        "implementationHandoff": {
            "taskId": IMPLEMENTATION_TASK_ID,
            "capabilitiesToImplement": [c["capabilityId"] for c in frozen],
            "canonicalOperationsToImplement": [
                c["canonicalOperations"][0] for c in frozen
            ],
            "allowlistDelta": [
                {
                    "operationId": c["canonicalOperations"][0],
                    "capabilityId": c["capabilityId"],
                    "executionMode": "catalog_action",
                    "approvedInputFields": c["approvedInputFields"],
                    "approvedResponseFields": c["approvedResponseFields"],
                    "semanticAliases": c["semanticAliasesPtBr"] + c["semanticAliasesEn"],
                    "argumentConstraints": c["argumentConstraints"],
                }
                for c in frozen
            ],
            "removeFromExplicitlyNotApproved": [
                "get_product_pricing",
                "get_product_purchase_price_history",
            ],
            "keepBlockedInExplicitlyNotApproved": [
                "get_product_cost_impact_simulation",
                "get_product_raw_material_price_intelligence",
                "get_product_summary",
            ],
            "lastPurchaseCurrentlyInExplicitlyNotApproved": False,
            "doNotImplement": ["get_product_cost_impact_simulation"],
            "expectedEligibleCount": 13,
            "mcpToolCount": 3,
            "agentInstructionChange": "NO",
            "doNotImplementNow": True,
        },
    }
    return inventory, freeze


def render_inventory_md(doc: dict[str, Any]) -> str:
    lines = [
        "# DAVI Wave 2 economic capability inventory",
        "",
        "> **SOURCE/EVIDENCE FREEZE only.** Not implemented, not deployed, not live.",
        "",
        f"- Task: `{doc['metadata']['taskId']}`",
        f"- Source HEAD: `{doc['metadata']['source_head']}`",
        f"- origin/main: `{doc['metadata']['origin_main']}`",
        f"- Current eligible: **{doc['rebaseline']['currentEligibleCount']}**",
        f"- MCP tools: `{', '.join(doc['rebaseline']['mcpTools'])}`",
        f"- Execution drift: `{doc['rebaseline']['executionDrift']}`",
        "",
        "## Architecture",
        "",
        "```text",
        doc["architecture"]["chain"],
        "```",
        "",
        "DAVI is intelligence / orchestration / presentation. DAVI is not source of truth, "
        "RBAC, domain owner, SQL client, generic HTTP proxy, financial authority or pricing authority.",
        "",
        "## Candidates",
        "",
    ]
    for cap in doc["candidates"]:
        lines.extend(
            [
                f"### {cap['capabilityId']} — `{cap['status']}`",
                "",
                f"- **BUSINESS NEED:** {cap['businessNeed']}",
                f"- **TECHNICAL OWNER:** {cap['technicalOwner']}",
                f"- **BUSINESS OWNER:** {cap['businessOwner']}",
                f"- **SOURCE OF TRUTH:** {cap['sourceOfTruth']}",
                f"- **BACKEND AUTHZ:** {cap['backendAuthz']}",
                f"- **READ/PREPARE/ACT:** {cap['readPrepareAct']}",
                f"- **CANONICAL OPERATION(S):** {', '.join('`'+o+'`' for o in cap['canonicalOperations'])}",
                f"- **INPUTS:** required={cap['requiredInputFields']} optional={cap['optionalInputFields']}",
                f"- **OUTPUT PATH COUNT:** {len(cap.get('approvedResponseFields') or [])}",
                f"- **PROJECTION:** {cap['projectionFeasibility']} / mode={cap['projectionMode']}",
                f"- **MONETARY:** {cap['monetarySemantics']}",
                f"- **CURRENCY:** {cap['currencySemantics']}",
                f"- **UNIT:** {cap['unitSemantics']}",
                f"- **TIME:** {cap['timeSemantics']}",
                f"- **PRIVACY:** {cap['privacy']}",
                f"- **RISK:** {cap['risk']}",
                f"- **QUARANTINE DELTA:** {json.dumps(cap['quarantineDeltaRequired'], ensure_ascii=False)}",
                f"- **OPEN GAPS:** {cap['openGaps']}",
                f"- **DECISION:** `{cap['status']}`",
                "",
            ]
        )
        if cap.get("deferReason"):
            lines.extend([f"- **DEFER REASON:** {cap['deferReason']}", ""])
    lines.extend(["## Semantic redundancies", ""])
    for row in doc["semanticRedundancies"]:
        lines.append(f"- `{row['group']}`: {row['decision']}")
    lines.extend(
        [
            "",
            "## Quarantine plan",
            "",
            f"- Keep global: {doc['quarantinePlan']['tokensToKeepGlobal']}",
            f"- Remove global: {doc['quarantinePlan']['globalTokensToRemove'] or 'NONE'}",
            "",
        ]
    )
    for row in doc["quarantinePlan"]["collisionPlan"]:
        lines.append(f"- **{row['intent']}** → `{row['owner']}` (not: {row['not']})")
    lines.extend(
        [
            "",
            "## Runtime impact of this task",
            "",
            "ALLOWLIST / ELIGIBILITY / RETRIEVAL / PROJECTION / EXECUTOR / MCP / AGENT / API: **UNCHANGED**.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def render_freeze_md(freeze: dict[str, Any]) -> str:
    lines = [
        "# DAVI Wave 2 capability freeze — Product Economic Intelligence",
        "",
        "> **Normative for the next implementation task.** Evidence/governance only. Does not change runtime.",
        "",
        f"- Task: `{freeze['taskId']}`",
        f"- Architecture correction: `{freeze.get('correctionTaskId')}` — `{freeze.get('architectureDecision')}`",
        f"- Source freeze SHA: `{freeze.get('sourceFreezeSha')}`",
        f"- Future implementation task: `{freeze['implementationTaskId']}` (DO NOT implement here)",
        f"- Source HEAD: `{freeze['source_head']}`",
        f"- Freeze status: `{freeze['status']}`",
        f"- Theme: {freeze['theme']}",
        f"- Current eligible: **{freeze['current_eligible']}**",
        f"- Wave 2 READ additions: **{freeze.get('wave2_read_additions', freeze['new_capabilities'])}**",
        f"- Expected eligible after implementation: **{freeze['expected_eligible_after_implementation']}**",
        f"- Expected MCP tools after implementation: **{freeze['expected_mcp_tools_after_implementation']}**",
        f"- Agent instructions change: **{freeze['agent_instruction_change']}**",
        "",
        "## Architecture invariants (do not reopen)",
        "",
        "```text",
        "DAVI capability <= authenticated user capability",
        "DAVI_BUSINESS_AUTHZ_OWNER = NONE",
        "CANONICAL_BACKEND_AUTHZ = REQUIRED_FINAL",
        "DAVI_LOCAL_RBAC / BRANCH / OBJECT / ROLE AUTHZ = FORBIDDEN",
        "FILTER != AUTHORIZATION",
        "endpoint != capability",
        "backend AuthZ != raw model exposure",
        "OAuth scope != business permission",
        "price/cost classification != independent DAVI permission",
        "simulation != ACT, recommendation != authorization, calculation != persistence",
        "HTTP GET != semantic READ",
        "PREPARE = preview/draft/simulação sem persistir — not Wave 2 READ",
        "MCP tools remain search_products + discover_delpi_information + execute_delpi_information",
        "```",
        "",
        "## Primary decisions",
        "",
    ]
    for key, value in freeze["primary_decisions"].items():
        lines.append(f"- `{key}`: **{value}**")
    lines.extend(["", "## Secondary decisions", ""])
    for key, value in freeze["secondary_decisions"].items():
        lines.append(f"- `{key}`: **{value}**")
    lines.extend(
        [
            "",
            "`get_product_summary` remains **DEFER**. Pricing freeze does not create a mega-summary.",
            "",
            "`product.cost.impact_simulation` is **PREPARE / DEFER_FROM_READ_WAVE**. HTTP GET compute-only "
            "simulation is not Wave 2 READ. Do not add it to the READ allowlist. A future PREPARE track "
            "may reuse the preserved source/projection analysis.",
            "",
            "Wave 1 operational capabilities are not reopened.",
            "",
        ]
    )
    for cap in freeze["capabilities"]:
        name = cap["businessName"]
        lines.extend(
            [
                f"## {cap['capabilityId']}",
                "",
                f"- **CAPABILITY ID:** `{cap['capabilityId']}`",
                f"- **BUSINESS NAME:** {name['ptBr']} / {name['en']}",
                f"- **BUSINESS NEED:** {cap['businessNeed']}",
                f"- **TECHNICAL OWNER:** {cap['technicalOwner']}",
                f"- **BUSINESS OWNER:** {cap['businessOwner']}",
                f"- **SOURCE OF TRUTH:** {cap['sourceOfTruth']}",
                f"- **CANONICAL OPERATION(S):** {', '.join('`'+o+'`' for o in cap['canonicalOperations'])}",
                f"- **CANONICAL USE CASE:** {', '.join('`'+u+'`' for u in cap['canonicalUseCases'])}",
                f"- **READ/PREPARE/ACT:** {cap['readPrepareAct']}",
                f"- **IDENTITY:** {cap['identity']}",
                f"- **BACKEND AUTHZ:** {cap['backendAuthz']}",
                f"- **APPROVED INPUT FIELDS:** {cap['approvedInputFields']}",
                f"- **REQUIRED INPUTS:** {cap['requiredInputFields']}",
                f"- **OPTIONAL INPUTS:** {cap['optionalInputFields']}",
                "- **APPROVED RESPONSE FIELDS:**",
            ]
        )
        for field in cap["approvedResponseFields"]:
            lines.append(f"  - `{field}`")
        lines.extend(
            [
                f"- **SHAPE:** {cap['shape']}",
                f"- **PROJECTION MODE:** {cap['projectionMode']}",
                f"- **PROJECTION FEASIBILITY:** {cap['projectionFeasibility']}",
                f"- **PER-OPERATION PROJECTOR:** {cap['perOperationProjectorRequired']}",
                f"- **ARGUMENT CONSTRAINTS:** {json.dumps(cap['argumentConstraints'], ensure_ascii=False)}",
                f"- **PAGINATION:** {cap['pagination']}",
                f"- **LIMITS:** {json.dumps(cap['limits'], ensure_ascii=False)}",
                f"- **TIME SEMANTICS:** {cap['timeSemantics']}",
                f"- **MONETARY SEMANTICS:** {cap['monetarySemantics']}",
                f"- **CURRENCY SEMANTICS:** {cap['currencySemantics']}",
                f"- **UNIT SEMANTICS:** {cap['unitSemantics']}",
                f"- **DERIVED FIELDS:** {json.dumps(cap['derivedFields'], ensure_ascii=False)}",
                f"- **COMPLETENESS:** {cap['completeness']}",
                f"- **PROVENANCE:** {cap['provenance']}",
                f"- **RETRIEVAL ALIASES PT-BR:** {cap['semanticAliasesPtBr']}",
                f"- **RETRIEVAL ALIASES EN:** {cap['semanticAliasesEn']}",
                f"- **PRIVACY:** {cap['privacy']}",
                f"- **RISK:** {cap['risk']}",
                f"- **OBSERVABILITY:** {cap['observability']}",
                f"- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; "
                "execute bounded payload; sibling non-match (venda vs compra vs última NF); "
                "negative AuthZ 403 without API_DELPI_ACCESS.",
                "- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; "
                "verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.",
                f"- **NEGATIVE AUTHZ PLAN:** {cap['negativeAuthzPlan']}",
                f"- **QUARANTINE CHANGE REQUIRED:** {json.dumps(cap['quarantineDeltaRequired'], ensure_ascii=False)}",
                f"- **OPEN GAPS:** {cap['openGaps']}",
                f"- **FREEZE STATUS:** `{cap['status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Implementation handoff (do not execute here)",
            "",
            f"Future task: `{freeze['implementationTaskId']}`",
            "",
            "Capabilities to implement:",
            "",
        ]
    )
    for cid in freeze["capability_ids"]:
        lines.append(f"- `{cid}`")
    handoff = freeze.get("implementationHandoff") or {}
    lines.extend(
        [
            "",
            "Canonical operations: `get_product_pricing`, `get_product_purchase_price_history`, `get_product_last_purchase`.",
            "",
            "Do **not** implement `get_product_cost_impact_simulation` in Wave 2 READ.",
            "",
            "Allowlist delta: add `operations[]` entries only (catalog_action + nested projection + aliases + generic argumentConstraints).",
            "Future removals from `explicitlyNotApproved`: `get_product_pricing`, `get_product_purchase_price_history`.",
            "`get_product_last_purchase` is not currently in `explicitlyNotApproved` (nested-shape blocked only).",
            "Keep blocked: `get_product_cost_impact_simulation`, `get_product_raw_material_price_intelligence`, `get_product_summary`.",
            "Do not remove global economic quarantine tokens; READ capabilities own via precise aliases. Cost tokens stay global-only.",
            "",
            f"Expected eligible after implementation: **{freeze['expected_eligible_after_implementation']}**.",
            "Expected MCP tools: **3**.",
            "Agent instruction change: **NO**.",
            "",
            "Must not change in this freeze/correction task (already true): MCP server tool surface, Agent Instructions, "
            "eligibility classifier semantics, executor genericity, API routes, use cases, repositories.",
            "",
        ]
    )
    _ = handoff
    return "\n".join(lines) + "\n"


def render_acceptance_md(freeze: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# DAVI Wave 2 Architecture Acceptance",
            "",
            f"- Task: `{CORRECTION_TASK_ID}`",
            f"- Source freeze SHA: `{SOURCE_FREEZE_SHA}`",
            f"- Decision: `{freeze.get('architectureDecision')}`",
            f"- Corrected freeze HEAD (generation): `{freeze.get('source_head')}`",
            "",
            "## Corrections",
            "",
            "1. `product.cost.impact_simulation`: READ / FROZEN_FOR_IMPLEMENTATION → **PREPARE / DEFER_FROM_READ_WAVE**.",
            "2. `product.commercial.pricing`: remove currentness claim → registered commercial price tables.",
            "3. `product.purchase.price_history`: bounded latest-N; `full_period_completeness = NOT_PROVEN`.",
            "",
            "## Wave 2 READ set",
            "",
            "- `product.commercial.pricing`",
            "- `product.purchase.price_history`",
            "- `product.purchase.last_valid`",
            "",
            "Count: **3**. Expected eligible after implementation: **13**. MCP tools: **3**. Agent Instructions: **UNCHANGED**.",
            "",
            "Canonical freeze authority after this correction remains `davi-capability-wave-002-freeze.json`.",
            "",
        ]
    ) + "\n"


def write_artifacts(
    inventory: dict[str, Any],
    freeze: dict[str, Any],
    *,
    out_dir: Path | None = None,
) -> dict[str, Path]:
    target = out_dir or (api_root() / "docs/integrations/evidence")
    target.mkdir(parents=True, exist_ok=True)
    acceptance = {
        "artifact_class": ARTIFACT_CLASS,
        "taskId": CORRECTION_TASK_ID,
        "sourceFreezeSha": SOURCE_FREEZE_SHA,
        "architectureDecision": "ACCEPT_WITH_RESIDUAL",
        "correctedFreezeAuthority": f"docs/integrations/evidence/{FREEZE_STEM}.json",
        "corrections": [
            {
                "capabilityId": "product.cost.impact_simulation",
                "before": "READ / FROZEN_FOR_IMPLEMENTATION",
                "after": "PREPARE / DEFER_FROM_READ_WAVE",
            },
            {
                "capabilityId": "product.commercial.pricing",
                "before": "Current commercial product pricing / Preço comercial atual",
                "after": "Commercial product price tables / Tabelas e preços comerciais do produto",
            },
            {
                "capabilityId": "product.purchase.price_history",
                "before": "implied complete-period history via truncated/is_complete",
                "after": "bounded latest-N; full_period_completeness = NOT_PROVEN",
            },
        ],
        "wave2ReadSet": freeze["capability_ids"],
        "expectedEligibleAfterImplementation": freeze["expected_eligible_after_implementation"],
        "mcpTools": 3,
        "generated_at": freeze.get("generated_at"),
        "source_head": freeze.get("source_head"),
    }
    paths = {
        "inventory_json": target / f"{INVENTORY_STEM}.json",
        "inventory_md": target / f"{INVENTORY_STEM}.md",
        "freeze_json": target / f"{FREEZE_STEM}.json",
        "freeze_md": target / f"{FREEZE_STEM}.md",
        "acceptance_json": target / f"{ACCEPTANCE_STEM}.json",
        "acceptance_md": target / f"{ACCEPTANCE_STEM}.md",
    }
    paths["inventory_json"].write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["inventory_md"].write_text(render_inventory_md(inventory), encoding="utf-8")
    paths["freeze_json"].write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["freeze_md"].write_text(render_freeze_md(freeze), encoding="utf-8")
    paths["acceptance_json"].write_text(
        json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["acceptance_md"].write_text(render_acceptance_md(freeze), encoding="utf-8")
    return paths
