# app/domain/entities/product.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:

    # =====================
    # IDENTIFICATION
    # =====================
    group_code: Optional[str] = None
    code: str = ""
    description: str = ""
    type: Optional[str] = None
    subgroup: Optional[str] = None
    previous_code: Optional[str] = None
    active: Optional[str] = None
    blocked: Optional[str] = None

    # =====================
    # COMMERCIAL
    # =====================
    customer_reference: Optional[str] = None
    customer_reference_old: Optional[str] = None
    sale_price: Optional[float] = None
    contractual_product: Optional[str] = None
    sales_class: Optional[str] = None

    # =====================
    # ENGINEERING / PRODUCTION
    # =====================
    drawing_code: Optional[str] = None
    unit: Optional[str] = None
    secondary_unit: Optional[str] = None
    conversion_factor: Optional[float] = None
    conversion_type: Optional[str] = None
    material_type: Optional[str] = None
    production_line: Optional[str] = None
    operation_decimal_type: Optional[str] = None
    current_revision: Optional[str] = None
    last_revision_date: Optional[str] = None
    net_weight: Optional[float] = None

    # =====================
    # STOCK / LOGISTICS
    # =====================
    default_warehouse: Optional[str] = None
    package_quantity: Optional[float] = None
    barcode: Optional[str] = None
    customer_packaging: Optional[str] = None
    make_or_buy: Optional[str] = None

    # =====================
    # PURCHASE
    # =====================
    last_purchase_date: Optional[str] = None
    last_purchase_price: Optional[float] = None
    lead_time_type: Optional[str] = None
    requester_restriction: Optional[str] = None

    # =====================
    # COST
    # =====================
    standard_cost: Optional[float] = None
    standard_cost_date: Optional[str] = None
    cost_currency: Optional[str] = None
    cost_reference_date: Optional[str] = None
    import_expense: Optional[float] = None

    # =====================
    # FISCAL / TAX
    # =====================
    ncm_ipi_position: Optional[str] = None
    origin: Optional[str] = None
    imported_product: Optional[str] = None
    tax_group: Optional[str] = None
    entry_tes: Optional[str] = None
    exit_tes: Optional[str] = None
    icms_rate: Optional[float] = None
    ipi_rate: Optional[float] = None
    pis_incidence: Optional[str] = None
    pis_percent: Optional[float] = None
    cofins_incidence: Optional[str] = None
    cofins_percent: Optional[float] = None
    csll_incidence: Optional[str] = None
    inss_incidence: Optional[str] = None
    retention_by_operation: Optional[str] = None
    customs_authority: Optional[str] = None
    media_product: Optional[str] = None
    media_quantity: Optional[float] = None
    intelligent_tes_group: Optional[str] = None

    # =====================
    # QUALITY / MRP
    # =====================
    rohs_indicator: Optional[str] = None
    traceability: Optional[str] = None
    warranty_product: Optional[str] = None
    mrp_considered: Optional[str] = None
    suggestion_flag: Optional[str] = None
    power_control: Optional[str] = None

    # =====================
    # ACCOUNTING
    # =====================
    accounting_account: Optional[str] = None
    cost_center: Optional[str] = None
    appropriation_type: Optional[str] = None

    # =====================
    # DELPI SYSTEM CONTROLS
    # =====================
    initial_consumption_date: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    mandatory_cc_sc: Optional[str] = None
    mandatory_cc_pc: Optional[str] = None
    mandatory_cc_pv: Optional[str] = None
    mandatory_cc_mi: Optional[str] = None
    mandatory_cc_nfe: Optional[str] = None
    approval_validation: Optional[str] = None
    delpi_category: Optional[str] = None
    delpi_segment: Optional[str] = None
