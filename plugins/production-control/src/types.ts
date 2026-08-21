export type PpcBranch = "01" | "02";
export type IssueSeverity = "critical" | "attention" | "ok";
export type IssueKind = "delayed_order";
export type SubpluginStatus = "active" | "coming_soon";

export type Subplugin = {
  id: string;
  label: string;
  description: string;
  icon: string;
  route: string;
  status: SubpluginStatus;
  permission: string;
};

export type ProblemIssue = {
  id: string;
  kind: IssueKind | string;
  severity: IssueSeverity;
  title: string;
  product_code: string | null;
  product_description: string | null;
  production_order: string | null;
  op_key: string | null;
  work_center: string | null;
  delay_days: number;
  branch: string | null;
  metrics: {
    planned_qty: number | null;
    produced_qty: number | null;
    pending_qty: number | null;
    warehouse: string | null;
    delivery_date: string | null;
    has_balance?: boolean | string | null;
    is_open?: boolean | null;
  };
};

/** Card da Análise de problemas: título e ícone do catálogo, números do detector. */
export type ProblemDetector = {
  id: string;
  title: string;
  description: string;
  action_hint: string | null;
  icon: string | null;
  order: number;
  severity: IssueSeverity;
  count: number;
  metrics: Record<string, number | string | null>;
};

export type ProblemDetectorsPayload = {
  branch: string;
  detectors: ProblemDetector[];
  summary: {
    detector_count: number;
    issue_count: number;
    critical: number;
    attention: number;
  };
};

export type OrderSetComponent = {
  product_code: string;
  description?: string | null;
  product_type?: string | null;
  bom_level?: number | null;
  production_order?: string | null;
};

/** Conjunto (C2_NUM + C2_ITEM) cujas OPs não batem com a estrutura do produto raiz. */
export type IncompleteOrderSetItem = {
  id: string;
  kind: string;
  severity: IssueSeverity;
  branch: string | null;
  set_key: string | null;
  set_number: string | null;
  set_item: string | null;
  root_code: string | null;
  root_description: string | null;
  root_order: string | null;
  due_date: string | null;
  issued_at: string | null;
  order_count: number;
  open_order_count: number;
  expected_component_count: number;
  created_component_count: number;
  missing_count: number;
  extra_count: number;
  missing_components: OrderSetComponent[];
  extra_components: OrderSetComponent[];
};

export type ProblemDetectorItemsPayload = {
  branch: string;
  detector: ProblemDetector;
  summary: Record<string, number | string | null>;
  items: IncompleteOrderSetItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    is_complete: boolean;
  };
};

export type DemandStatus = "late" | "at_risk" | "covered_by_order" | "covered_by_stock";

/** OP aberta que cobre parte do saldo de uma linha de pedido. */
export type DemandCoveringOrder = {
  production_order: string;
  quantity: number;
  expected_date: string | null;
};

export type DemandLine = {
  id: string;
  branch: string;
  sales_order: string;
  line_item: string;
  customer_name: string;
  customer_code: string;
  customer_store: string;
  customer_order: string;
  order_type: string;
  product_code: string;
  ordered_quantity: number;
  delivered_quantity: number;
  open_quantity: number;
  due_date: string | null;
  dispatch_date: string | null;
  product_stock: number;
  allocated_stock: number;
  covered_by_orders: number;
  uncovered_quantity: number;
  covering_orders: DemandCoveringOrder[];
  coverage_date: string | null;
  status: DemandStatus;
  days_late: number;
};

export type DemandHorizonBucket = {
  key: string;
  label: string;
  start_date: string | null;
  open_quantity: number;
  line_count: number;
  late: boolean;
};

export type DemandPayload = {
  branch: string;
  items: DemandLine[];
  summary: {
    line_count: number;
    open_quantity: number;
    late_line_count: number;
    at_risk_line_count: number;
    uncovered_quantity: number;
    customer_count: number;
    product_count: number;
    next_due_date: string | null;
  };
  horizon: DemandHorizonBucket[];
  filters: {
    search: string;
    status: string;
    due_from: string | null;
    due_to: string | null;
    sort: string;
    direction: "asc" | "desc";
    statuses: DemandStatus[];
  };
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    is_complete: boolean;
  };
};

export type VolumeView = "day" | "month_yoy";

export type OverviewSeriesPoint = {
  label: string;
  value: number | null;
  prior_value?: number | null;
  start_date?: string | null;
  end_date?: string | null;
};

export type OverviewPayload = {
  branch: string;
  period: {
    start_date: string;
    end_date: string;
    granularity: string;
  };
  otd: {
    on_time_delivery_pct: number | null;
    late_ops: number;
    on_time_ops: number;
    total_ops_finished: number;
    late_percentage: number | null;
    series: OverviewSeriesPoint[];
  };
  /** Volume diário/mensal de PAs (última operação do roteiro) — mesma fonte do apontamento. */
  production_volume: {
    view: VolumeView;
    period: { start_date: string; end_date: string };
    prior_period?: { start_date: string; end_date: string } | null;
    total: number;
    prior_total?: number | null;
    unit: string;
    /** Média só em dias úteis (seg–sex); nula no modo mensal. */
    weekday_average: number | null;
    weekday_day_count: number;
    current_year?: number;
    prior_year?: number;
    series: OverviewSeriesPoint[];
  };
  delayed_ops: {
    count: number;
    late_percentage: number | null;
    items: ProblemIssue[];
  };
  /** Pedidos com entrega até hoje — check estoque (amarelo) / faturado (verde). */
  billing_due_today: BillingDueTodayPayload;
};

export type BillingDueTodayCheck = "pending" | "stock" | "invoiced";

export type BillingDueTodayLine = {
  id: string;
  branch: string;
  sales_order: string;
  line_item: string;
  customer_code: string;
  customer_store: string;
  customer_name: string;
  customer_order?: string;
  order_type?: string;
  product_code: string;
  ordered_quantity?: number;
  delivered_quantity?: number;
  open_quantity: number;
  product_stock?: number;
  allocated_stock?: number;
  uncovered_quantity?: number;
  due_date: string | null;
  dispatch_date?: string | null;
  invoice_date: string | null;
  check: BillingDueTodayCheck;
  days_late: number;
};

export type BillingDueTodayCustomer = {
  customer_code: string;
  customer_store: string;
  customer_name: string;
  line_count: number;
  pending_count: number;
  stock_count: number;
  invoiced_count: number;
  lines: BillingDueTodayLine[];
};

export type BillingDueTodayPayload = {
  as_of: string;
  line_count: number;
  pending_count: number;
  stock_count: number;
  invoiced_count: number;
  customers: BillingDueTodayCustomer[];
};

export type ProductionStatus = "in_progress" | "started" | "not_started";

export type MachineLoadWorkCenter = {
  work_center: string;
  work_center_name: string;
  operation_count: number;
  order_count: number;
  in_production_count: number;
  first_scheduled_date?: string | null;
  last_scheduled_date?: string | null;
};

export type MachineLoadOperation = {
  branch: string;
  work_center: string;
  work_center_name: string;
  scheduled_date: string | null;
  scheduled_start_time: string | null;
  production_order: string;
  operation_code: string;
  operation_description: string;
  tool: string;
  is_manual_operation: boolean;
  product_code: string;
  product_description: string;
  unit: string | null;
  planned_qty: number;
  pending_qty: number;
  pa_due_date: string | null;
  pa_product_code: string | null;
  production_status: ProductionStatus;
  is_in_production: boolean;
  production_started_date: string | null;
  production_started_time: string | null;
  active_operator_code: string | null;
  active_operator_name: string | null;
  active_operator_count: number;
  appointment_count: number;
  last_appointment_date: string | null;
  /** Centro de trabalho de origem, quando o PCP transferiu a operação. */
  transferred_from?: string | null;
};

export type MachineLoadLocateStop = {
  work_center: string;
  work_center_name: string;
  production_order: string;
  operation_code: string;
  operation_description: string;
  product_code: string;
  product_description: string;
  pa_product_code: string | null;
  pa_due_date: string | null;
  scheduled_date: string | null;
  scheduled_start_time: string | null;
  pending_qty: number | null;
  unit: string | null;
  tool: string;
  production_status: ProductionStatus;
  is_in_production: boolean;
  production_started_time: string | null;
  active_operator_name: string | null;
  queue_position: number;
  queue_size: number;
  /** Conjunto fora da programação: a parada aparece no rastreio, mas não na fila. */
  is_withdrawn?: boolean;
};

export type MachineLoadLocateJourney = {
  kind: "pa" | "op";
  key: string;
  label: string;
  pa_product_code: string | null;
  pa_due_date: string | null;
  stop_count: number;
  is_withdrawn?: boolean;
  stops: MachineLoadLocateStop[];
};

export type MachineLoadLocatePayload = {
  query: string;
  match_count: number;
  journey_count: number;
  message: string | null;
  period: {
    start_date: string | null;
    end_date: string | null;
    field?: "delivery_date";
  };
  snapshot: {
    refreshed_at: string | null;
    seeded: boolean;
    schema_version?: number;
  };
  journeys: MachineLoadLocateJourney[];
};

/** Conjunto (C2_NUM) que o PCP tirou da programação — some da fila e do cockpit. */
export type MachineLoadWithdrawnEntry = {
  order_number: string;
  withdrawn_at: string | null;
  withdrawn_by: string | null;
  operation_count: number;
  work_centers: string[];
  pa_product_code: string | null;
  pa_due_date: string | null;
};

export type MachineLoadWithdrawnSummary = {
  conjunto_count: number;
  operation_count: number;
  items: MachineLoadWithdrawnEntry[];
};

export type MachineLoadPayload = {
  branch: string;
  /** Janela por **entrega do PA**: a fila congelada é uma só; «De/até» é lente de leitura. */
  period: {
    start_date: string | null;
    end_date: string | null;
    field?: "delivery_date";
    /** Janela realmente puxada do TOTVS na última atualização. */
    pulled_start?: string | null;
    pulled_end?: string | null;
    /** Entrega mais antiga presente na fila — sugestão do campo «De». */
    oldest_due_date?: string | null;
    /** A tela está restringindo a fila com o «De/até» informado. */
    filtered?: boolean;
  };
  summary: {
    work_center_count: number;
    operation_count: number;
    order_count: number;
    in_production_count: number;
    /** Operações sem entrega do PA nem previsão da OP — não deveriam existir. */
    missing_due_date_count?: number;
  };
  snapshot: {
    refreshed_at: string | null;
    refreshed_by?: string | null;
    seeded: boolean;
    schema_version?: number;
    sequence_updated_at?: string | null;
    sequence_updated_by?: string | null;
  };
  withdrawn?: MachineLoadWithdrawnSummary;
  work_centers: MachineLoadWorkCenter[];
  selected: {
    work_center: string | null;
    requested_work_center: string | null;
    items: MachineLoadOperation[];
    pagination: {
      page?: number;
      page_size?: number;
      total?: number;
      is_complete?: boolean;
    };
  };
};

/** Resultado da priorização de um conjunto (C2_NUM) nas filas dos centros. */
export type MachineLoadPrioritization = {
  order_number: string;
  work_centers: string[];
  operation_count: number;
  kept_ahead_count: number;
  message: string;
};

export type MachineLoadPrioritizePayload = MachineLoadPayload & {
  prioritization: MachineLoadPrioritization;
};

/** Resultado de reordenar a fila de todos os centros pela entrega do PA. */
export type MachineLoadDeliveryOptimization = {
  work_centers: string[];
  moved_operation_count: number;
  kept_ahead_count: number;
  missing_due_date_count: number;
  message: string;
};

export type MachineLoadOptimizePayload = MachineLoadPayload & {
  optimization: MachineLoadDeliveryOptimization;
};

/** Resultado de retirar o conjunto da programação ou devolvê-lo à fila. */
export type MachineLoadWithdrawal = {
  order_number: string;
  action: "withdrawn" | "restored";
  operation_count: number;
  work_centers: string[];
  message: string;
};

export type MachineLoadWithdrawPayload = MachineLoadPayload & {
  withdrawal: MachineLoadWithdrawal;
};

/** Resultado de mover uma operação (ou conjunto no CT) para outro centro. */
export type MachineLoadTransfer = {
  production_order: string;
  operation_code: string | null;
  order_number?: string;
  operation_count?: number;
  scope?: "operation" | "conjunto_at_center";
  source_work_center: string;
  target_work_center: string;
  target_work_center_name: string | null;
  returned_to_origin: boolean;
  message: string;
};

export type MachineLoadTransferPayload = MachineLoadPayload & {
  transfer: MachineLoadTransfer;
};
