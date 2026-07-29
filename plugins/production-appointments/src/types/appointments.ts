export type AppointmentsQueryFilters = {
  branch: string;
  dateStart: string;
  dateEnd: string;
  workCenter?: string;
  op?: string;
  product?: string;
  motherOp?: boolean;
};

export type FilterFormState = {
  dateStart: string;
  dateEnd: string;
  workCenter: string;
  op: string;
  product: string;
  motherOp: boolean;
};

export type WorkCenterItem = {
  branch: string;
  work_center: string;
  name: string;
  is_final_inspection: number | boolean;
};

export type AppointmentTotals = {
  appointment_count: number;
  qty_produced: number;
  qty_lost: number;
  op_count: number;
  work_center_count: number;
};

export type WorkCenterSummaryRow = {
  work_center: string;
  work_center_name: string;
  is_final_inspection: number | boolean;
  appointment_count: number;
  qty_produced: number;
  qty_lost: number;
  op_count: number;
};

export type AppointmentsSummaryData = {
  period: { start: string; end_exclusive: string };
  branch: string;
  totals: AppointmentTotals;
  items: WorkCenterSummaryRow[];
};

export type SeriesPoint = {
  /** ISO `YYYY-MM-DD` (dia) ou `YYYY-MM` (mês) — eixo temporal público. */
  appointment_date: string;
  /** ISO espelhando `appointment_date` (padrão OEE/OTD / TV). */
  periodo?: string;
  /** Bucket Protheus `YYYYMMDD` / `YYYYMM` (quando a API enviar). */
  bucket?: string;
  work_center?: string;
  work_center_name?: string;
  appointment_count: number;
  qty_produced: number;
  qty_lost: number;
};

export type AppointmentsSeriesData = {
  group_by: string;
  granularity?: string;
  points: SeriesPoint[];
};

export type AppointmentRow = {
  branch: string;
  production_order: string;
  product: string;
  product_type?: string;
  product_description?: string;
  work_center: string;
  work_center_name: string;
  is_final_inspection?: number | boolean;
  operation?: string;
  resource?: string;
  resource_name?: string;
  operator_code?: string;
  operator_name?: string;
  start_date?: string;
  start_time?: string;
  end_date?: string;
  end_time?: string;
  qty_produced: number;
  qty_lost: number;
  appointment_date: string;
  appointment_id: number;
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  is_complete: boolean;
};

export type AppointmentsListData = {
  items: AppointmentRow[];
  pagination: Pagination;
};

export type ByOpRow = {
  production_order: string;
  product: string;
  product_type?: string;
  product_description?: string;
  appointment_count: number;
  work_center_count: number;
  qty_produced: number;
  qty_lost: number;
  first_date: string;
  last_date: string;
};

export type AppointmentsByOpData = {
  items: ByOpRow[];
  pagination: Pagination;
};
