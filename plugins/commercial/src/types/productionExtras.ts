/** Resposta enxuta de GET /production/orders/by-op/{op}. */
export type ProductionOrderOtdStatus = "open" | "on_time" | "late" | string;

export type ProductionOrderRow = {
  branch?: string | null;
  production_order?: string | null;
  order_number?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  product_type?: string | null;
  warehouse?: string | null;
  planned_qty?: number | null;
  produced_qty?: number | null;
  order_status?: string | null;
  observation?: string | null;
  issue_date?: string | null;
  planned_start_date?: string | null;
  due_date?: string | null;
  finish_date?: string | null;
  otd_status?: ProductionOrderOtdStatus | null;
  days_diff?: number | null;
  /** Pedido de venda (C2_PEDIDO) quando preenchido. */
  sales_order?: string | null;
  /** Item do pedido (C2_ITEMPV). */
  sales_order_item?: string | null;
};

export type ProductionOrderLinkSummary = {
  order_number?: string | null;
  link_field?: string | null;
  total_pi_orders?: number | null;
  on_time_ops?: number | null;
  late_ops?: number | null;
  open_ops?: number | null;
};

export type ProductionOrderByOpData = {
  order: ProductionOrderRow;
  linked_orders?: ProductionOrderRow[];
  link_summary?: ProductionOrderLinkSummary | Record<string, unknown>;
};

export type ProductFactoryStatusIndicators = {
  total_intermediates?: number | null;
  total_raw_materials?: number | null;
  total_exclusive_raw_materials?: number | null;
  total_raw_materials_without_stock_for_one_pa?: number | null;
  max_pa_producible_from_stock?: number | null;
  limiting_raw_material_code?: string | null;
  total_pa_orders?: number | null;
  total_pi_orders?: number | null;
  total_pa_reported_quantity?: number | null;
  total_pi_reported_quantity?: number | null;
  total_pa_shipped_quantity?: number | null;
  total_inspection_loss_quantity?: number | null;
};

/** Subconjunto útil de GET /products/{code}/factory-status. */
export type ProductFactoryStatusData = {
  factory_status?: unknown;
  product?: {
    product_code?: string | null;
    description?: string | null;
  } | null;
  production?: {
    summary?: {
      pa_production_started?: unknown;
      pi_production_started?: unknown;
      total_pa_orders?: unknown;
      total_pi_orders?: unknown;
    } | null;
  } | null;
  shipping?: {
    summary?: {
      total_shipped_quantity?: unknown;
      total_inspection_loss_quantity?: unknown;
    } | null;
  } | null;
  indicators?: ProductFactoryStatusIndicators | null;
};

/** Agregado real de GET /production/appointments/by-op. */
export type ProductionAppointmentByOpRow = {
  production_order?: string | null;
  product?: string | null;
  product_type?: string | null;
  product_description?: string | null;
  unit?: string | null;
  appointment_count?: number | null;
  work_center_count?: number | null;
  qty_produced?: number | null;
  qty_lost?: number | null;
  first_date?: string | null;
  last_date?: string | null;
  /** Campos legados pontuais (se a API evoluir). */
  appointment_date?: string | null;
  work_center?: string | null;
  reported_quantity?: number | null;
  [key: string]: unknown;
};

/** @deprecated Preferir ProductionAppointmentByOpRow */
export type ProductionAppointmentItem = ProductionAppointmentByOpRow;

export type ProductionAppointmentsByOpData = {
  items: ProductionAppointmentByOpRow[];
  total?: number;
  summary?: Record<string, unknown>;
};

export type ProductStructureNode = {
  code?: string;
  product_code?: string;
  description?: string;
  type?: string;
  quantity?: number | null;
  unit?: string;
  components?: ProductStructureNode[];
  items?: ProductStructureNode[];
  [key: string]: unknown;
};

export type ProductStructureData = {
  root?: ProductStructureNode;
  items?: ProductStructureNode[];
  total?: number;
};
