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
};

export type ProductionAppointmentItem = {
  production_order?: string | null;
  appointment_date?: string | null;
  work_center?: string | null;
  product_code?: string | null;
  reported_quantity?: number | null;
  [key: string]: unknown;
};

export type ProductionAppointmentsByOpData = {
  items: ProductionAppointmentItem[];
  total?: number;
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
