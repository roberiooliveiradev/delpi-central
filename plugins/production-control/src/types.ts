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

export type ProblemAnalysisPayload = {
  branch: string;
  summary: {
    critical: number;
    attention: number;
    ok: number;
    issue_count: number;
  };
  issues: ProblemIssue[];
  selected: ProblemIssue | null;
};

export type OverviewSeriesPoint = {
  label: string;
  value: number | null;
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
  delayed_ops: {
    count: number;
    late_percentage: number | null;
    items: ProblemIssue[];
  };
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

/** Resultado de mover uma operação para outro centro de trabalho. */
export type MachineLoadTransfer = {
  production_order: string;
  operation_code: string;
  source_work_center: string;
  target_work_center: string;
  target_work_center_name: string | null;
  returned_to_origin: boolean;
  message: string;
};

export type MachineLoadTransferPayload = MachineLoadPayload & {
  transfer: MachineLoadTransfer;
};
