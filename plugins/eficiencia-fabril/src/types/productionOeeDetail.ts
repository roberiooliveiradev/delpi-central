export type ProductionOeeAppointmentStatus = "valid" | "outlier";

export type AppointmentTimeFindingSeverity = "info" | "warning" | "error";

export type AppointmentTimeFinding = {
  code: string;
  severity: AppointmentTimeFindingSeverity;
  message: string;
  detail?: string | null;
};

export type ProductionOeeAppointmentDetail = {
  appointment_id: number;
  branch: string;
  production_order: string;
  product_code: string;
  product_description: string;
  product_type: string;
  unit: string;
  work_center: string;
  operation: string;
  operation_description: string;
  resource_code: string;
  resource_name: string;
  operator_code: string;
  production_date: string;
  appointment_date: string;
  start_date: string;
  start_time: string;
  end_date: string;
  end_time: string;
  oee_pct: number | null;
  produced_qty: number | null;
  lost_qty: number | null;
  production_point_type: string;
  appointment_type: string;
  status: ProductionOeeAppointmentStatus;
  order_planned_qty: number | null;
  order_produced_qty: number | null;
  order_number: string;
  order_item: string;
  route_code: string;
};

export type ProductionOeeTimeAnalysis = {
  setup_hours: number | null;
  standard_time_factor: number | null;
  order_planned_qty: number | null;
  produced_qty: number | null;
  planned_hours: number | null;
  real_hours: number | null;
  real_hours_source?: "interval" | "h6_tempo";
  time_variance_hours: number | null;
  time_gained_lost_hours: number | null;
  efficiency_from_times_pct: number | null;
  oee_pct: number | null;
  formula_planned: string;
  formula_real: string;
  formula_efficiency: string;
  findings?: AppointmentTimeFinding[];
  has_findings?: boolean;
};

export type ProductionOeeRoutingOperation = {
  operation_code?: string;
  operation_description?: string;
  resource_code?: string;
  work_center?: string;
  setup_hours?: number | null;
  standard_time_hours_piece?: number | null;
  bom_level?: number;
  is_appointment_operation?: boolean;
};

export type ProductStructureNode = {
  code?: string;
  product_code?: string;
  description?: string;
  type?: string;
  quantity?: number | null;
  components?: ProductStructureNode[];
  items?: ProductStructureNode[];
};

export type ProductStructureData = {
  root?: ProductStructureNode;
  items?: ProductStructureNode[];
};

export type ProductionOeeAppointmentDetailData = {
  appointment: ProductionOeeAppointmentDetail;
  time_analysis: ProductionOeeTimeAnalysis;
  routing_operations: ProductionOeeRoutingOperation[];
  structure: ProductStructureData;
};
