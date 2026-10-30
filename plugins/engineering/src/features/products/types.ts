/** Contratos do bounded context Produtos — payloads oficiais da
 * Engineering API (/v1/products*), delegados ao owner API DELPI/TOTVS.
 * A visão `engineering` já remove campos comerciais/custo/fiscais na
 * fonte — o MFE nunca reprocessa nem infere atributos. */

export type ProductRecord = {
  code: string;
  description: string | null;
  type: string | null;
  group_code: string | null;
  subgroup: string | null;
  previous_code: string | null;
  active: string | null;
  blocked: string | null;
  customer_reference: string | null;
  customer_reference_old?: string | null;
  contractual_product?: string | null;
  sales_class?: string | null;
  drawing_code: string | null;
  unit: string | null;
  secondary_unit?: string | null;
  conversion_factor?: number | null;
  conversion_type?: string | null;
  material_type?: string | null;
  production_line?: string | null;
  operation_decimal_type?: string | null;
  current_revision?: string | null;
  last_revision_date?: string | null;
  net_weight?: number | null;
  default_warehouse?: string | null;
  package_quantity?: number | null;
  barcode?: string | null;
  customer_packaging?: string | null;
  make_or_buy?: string | null;
  last_purchase_date?: string | null;
  lead_time_type?: string | null;
  requester_restriction?: string | null;
  rohs_indicator?: string | null;
  traceability?: string | null;
  warranty_product?: string | null;
  mrp_considered?: string | null;
  suggestion_flag?: string | null;
  power_control?: string | null;
  initial_consumption_date?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  delpi_category?: string | null;
  delpi_segment?: string | null;
  qtd_pi?: number | null;
};

export type ProductListResult = {
  items: ProductRecord[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type ProductDetailResult = {
  product: ProductRecord;
};

export type ProductBomNode = {
  code: string;
  description: string | null;
  type: string | null;
  unit: string | null;
  quantity: number;
  secondary_unit?: string | null;
  conversion_factor?: number | null;
  conversion_type?: string | null;
  third_unit?: string | null;
  third_conversion_factor?: number | null;
  components?: ProductBomNode[];
};

export type ProductStructureResult = {
  root: {
    code: string;
    description: string | null;
    type: string | null;
    unit: string | null;
    quantity: number;
  } | null;
  items: ProductBomNode[];
  page: number | null;
  page_size: number | null;
  total: number;
  total_pages: number | null;
  bom_validity?: unknown;
};

export type ProductParentNode = {
  code: string;
  description: string | null;
  type: string | null;
  unit: string | null;
  quantity: number;
  parents?: ProductParentNode[];
};

export type ProductParentsResult = {
  root: {
    code: string;
    description: string | null;
    type: string | null;
    unit: string | null;
    quantity: number;
  } | null;
  items: ProductParentNode[];
  page: number | null;
  page_size: number | null;
  total: number;
  total_pages: number | null;
};

export type ProductSupplier = {
  product_code: string;
  product_description: string | null;
  unit: string | null;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string | null;
  supplier_part_number: string | null;
  catalog_code: string | null;
  barcode: string | null;
  registered_lead_time_days: number | null;
  real_avg_lead_time_days: number | null;
  real_min_lead_time_days: number | null;
  real_max_lead_time_days: number | null;
  real_lead_time_sample_size: number | null;
};

export type ProductSuppliersResult = {
  items: ProductSupplier[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type ProductDrawingMetadata = {
  product_code: string;
  found: boolean;
  filename?: string;
  revision?: string | null;
  variant_suffix?: string | null;
  size_bytes?: number;
  modified_at?: string;
  media_type?: string;
  message?: string;
};

/** Entrada do histórico de preço de compra (payload playbook do owner —
 * campos variam por filial; renderizado como tabela quando tabular). */
export type ProductPurchaseHistoryResult = {
  product?: { code?: string; description?: string | null } | null;
  history?: Record<string, unknown>[];
  budget_history?: Record<string, unknown>[];
  [key: string]: unknown;
};
