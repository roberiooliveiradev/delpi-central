export type AppointmentsQueryFilters = {
  branch: string;
  dateStart: string;
  dateEnd: string;
  workCenter?: string;
  op?: string;
  product?: string;
};

export type FilterFormState = {
  dateStart: string;
  dateEnd: string;
  workCenter: string;
  op: string;
  product: string;
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
  appointment_date: string;
  work_center?: string;
  work_center_name?: string;
  appointment_count: number;
  qty_produced: number;
  qty_lost: number;
};

export type AppointmentsSeriesData = {
  group_by: string;
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
