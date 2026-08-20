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
};

export type MachineLoadPayload = {
  branch: string;
  period: {
    start_date: string;
    end_date: string;
  };
  summary: {
    work_center_count: number;
    operation_count: number;
    order_count: number;
    in_production_count: number;
  };
  snapshot: {
    refreshed_at: string | null;
    refreshed_by?: string | null;
    seeded: boolean;
    schema_version?: number;
    sequence_updated_at?: string | null;
    sequence_updated_by?: string | null;
  };
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
