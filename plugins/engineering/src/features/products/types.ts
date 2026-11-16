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

/** Opções oficiais de filtro do catálogo — valores distintos observados
 * no cadastro (SB1), entregues por `GET /v1/products/filter-options`. */
export type ProductFilterOptions = {
  groups: string[];
  types: string[];
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

/** Linha do roteiro oficial (GET /v1/products/{code}/routing — SG2,
 * pass-through do owner `/products/{code}/guide`). Cada linha é a tupla
 * (produto, operação, componente): a MESMA operação aparece repetida
 * por componente da BOM — consolidação visual espelha a identidade
 * oficial (produto × nível × operação × CT × recurso). */
export type ProductRoutingRow = {
  branch?: string | null;
  route_code?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  bom_level?: number | null;
  operation_code?: string | null;
  operation_description?: string | null;
  work_center?: string | null;
  resource_code?: string | null;
  operation_type?: string | null;
  mandatory_operation?: string | null;
  mandatory_sequence?: string | null;
  mandatory_report?: string | null;
  /** Preparação por LOTE em horas — nunca somada ao tempo peça sem lote. */
  setup_hours?: number | null;
  /** Tempo padrão por peça em minutos (semântica do owner, exibida crua). */
  standard_time_minutes_piece?: number | null;
  component_code?: string | null;
  component_description?: string | null;
  component_sequence?: string | null;
  [key: string]: unknown;
};

export type ProductRoutingResult = {
  items: ProductRoutingRow[];
  total?: number | null;
  page?: number | null;
  page_size?: number | null;
  total_pages?: number | null;
  [key: string]: unknown;
};

/* --- POST /v1/products/{code}/line-balance — domínio EVA -------------- */

/** Operação consolidada pelo backend (identidade oficial) — o MFE só
 * renderiza; dedup, takt e cenários são computados no domínio EVA. */
export type LineBalanceOperation = {
  operation_code: string;
  operation_description?: string | null;
  work_center?: string | null;
  resource_code?: string | null;
  operation_type?: string | null;
  mandatory_operation?: string | null;
  mandatory_sequence?: string | null;
  mandatory_report?: string | null;
  time_minutes_piece?: number | null;
  setup_hours?: number | null;
  effective_minutes_piece?: number | null;
  components?: {
    code: string;
    description?: string | null;
    sequence?: string | null;
  }[];
};

export type LineBalanceStage = {
  product_code: string;
  bom_level: number;
  branch?: string | null;
  route_code?: string | null;
  operations: LineBalanceOperation[];
  operations_count: number;
  operations_missing_time: string[];
  setup_hours_total?: number | null;
  setup_minutes_piece_amortized?: number | null;
  work_content_minutes?: number | null;
  takt_minutes?: number | null;
  theoretical_min_stations?: number | null;
  bottleneck_candidate?: {
    operation_code: string;
    operation_description?: string | null;
    work_center?: string | null;
    minutes_piece: number;
  } | null;
  over_takt_operations: {
    operation_code: string;
    work_center?: string | null;
    minutes_piece: number;
  }[];
  station_check?: {
    num_stations: number;
    theoretical_min_stations?: number | null;
    required_cycle_minutes?: number | null;
    feasible?: boolean;
    theoretical_efficiency?: number | null;
  } | null;
  balance_scenario?: {
    type: string;
    data_class: string;
    stations_used: number;
    stations: {
      operations: string[];
      load_minutes: number;
      idle_minutes: number;
    }[];
    balance_efficiency?: number | null;
    idle_minutes_total?: number | null;
    caveats?: string[];
  } | null;
  missing_parameters: string[];
  invalid_parameters: string[];
  limitations: string[];
};

/** Payload canônico do domínio `build_balance_result` — classes de
 * proveniência observadas pelo backend: OBSERVED (roteiro oficial),
 * PROVIDED (parâmetros do usuário), CALCULATED (métricas) e
 * SIMULATION (cenários hipotéticos). */
export type ProductLineBalanceResult = {
  analysis_type: string;
  product_code: string;
  branch?: string | null;
  method?: string;
  data_class: string;
  official_rows?: number;
  unique_operations?: number;
  parameters?: Record<
    string,
    { value: unknown; data_class: string }
  >;
  stages: LineBalanceStage[];
  missing_parameters?: string[];
  invalid_parameters?: string[];
  limitations?: string[];
  filters_applied?: {
    branch?: string | null;
    max_depth?: number | null;
    bom_levels?: number[] | null;
  };
  source?: string;
  provenance?: string;
};

/** Vocabulário fechado do contrato POST — espelha BALANCE_INPUT_FIELDS
 * do domínio; campos fora dele são rejeitados pelo backend. */
export type LineBalanceRequest = {
  branch?: string;
  max_depth?: number;
  bom_levels?: number[];
  demand?: number;
  available_minutes?: number;
  batch_size?: number;
  num_stations?: number;
};
