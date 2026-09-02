export const UNPRODUCTIVE_HOURS_PAGE_SIZE = 50;
export const UNPRODUCTIVE_HOURS_RANKING_LIMIT = 10;

export type UnproductiveHoursSort =
  | "date_desc"
  | "date_asc"
  | "hours_desc"
  | "hours_asc"
  | "cost_desc"
  | "cost_asc";

export type UnproductiveHoursRankBy =
  | "stop_reason"
  | "resource"
  | "cost_center"
  | "operator"
  | "product"
  | "operation";

export type UnproductiveHoursQueryFilters = {
  branch: string;
  start_date: string;
  end_date: string;
  stop_reason?: string;
  resource?: string;
  cost_center?: string;
  operator_code?: string;
};

export type UnproductiveHoursItemsFilters = UnproductiveHoursQueryFilters & {
  page: number;
  page_size?: number;
  sort?: UnproductiveHoursSort;
};

export type UnproductiveHoursRankingFilters = UnproductiveHoursQueryFilters & {
  rank_by: UnproductiveHoursRankBy;
  metric?: "hours" | "cost";
  limit?: number;
};

export type UnproductiveHoursNamedMetric = {
  resource?: string;
  recurso?: string;
  total_hours?: number;
  totalHoras?: number;
  operator_code?: string;
  codigoOperador?: string;
  operator_name?: string;
  nomeOperador?: string;
};

export type UnproductiveHoursSummaryMetrics = {
  total_appointments?: number;
  totalApontamentos?: number;
  total_hours?: number;
  totalHoras?: number;
  total_cost?: number;
  totalCusto?: number;
  avg_cost_per_hour?: number;
  custoMedioHora?: number;
  records_without_cost?: number;
  registrosSemCusto?: number;
  hours_without_cost?: number;
  horasSemCusto?: number;
  pct_hours_without_cost?: number;
  percentualHorasSemCusto?: number;
  top_resource_by_hours?: UnproductiveHoursNamedMetric | null;
  principalRecursoPorHoras?: UnproductiveHoursNamedMetric | null;
  top_operator_by_hours?: UnproductiveHoursNamedMetric | null;
  principalColaboradorPorHoras?: UnproductiveHoursNamedMetric | null;
};

export type UnproductiveHoursSummaryData = {
  periodo?: Record<string, string | null | undefined>;
  summary: UnproductiveHoursSummaryMetrics;
};

export type UnproductiveHoursItem = {
  reference_date?: string | null;
  dataReferencia?: string | null;
  branch?: string;
  filial?: string;
  production_order?: string;
  op?: string;
  product_code?: string;
  produto?: string;
  operation?: string;
  operacao?: string;
  resource?: string;
  recurso?: string;
  cost_center?: string;
  centroCusto?: string;
  operator_code?: string;
  codigoOperador?: string;
  operator_name?: string;
  nomeOperador?: string;
  stop_reason?: string;
  motivo?: string;
  stop_reason_description?: string | null;
  motivoDescricao?: string | null;
  observation?: string;
  observacao?: string;
  hours?: number;
  tempoHoras?: number;
  stop_cost?: number;
  valorParada?: number;
  cost_source?: string;
  fonteCusto?: string;
  recno?: number | null;
};

export type UnproductiveHoursItemsData = {
  periodo?: Record<string, string | null | undefined>;
  items: UnproductiveHoursItem[];
  page?: number;
  pageSize?: number;
  page_size?: number;
  total?: number;
  totalPages?: number;
  total_pages?: number;
  sort?: string;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    is_complete?: boolean;
  };
};

export type UnproductiveHoursRankingItem = {
  rank: number;
  stop_reason?: string;
  motivo?: string;
  stop_reason_description?: string | null;
  motivoDescricao?: string | null;
  resource?: string;
  recurso?: string;
  cost_center?: string;
  centroCusto?: string;
  operator_code?: string;
  codigoOperador?: string;
  operator_name?: string;
  nomeOperador?: string;
  product_code?: string;
  produto?: string;
  operation?: string;
  operacao?: string;
  total_appointments?: number;
  totalApontamentos?: number;
  total_hours?: number;
  totalHoras?: number;
  total_cost?: number;
  totalCusto?: number;
  hours_without_cost?: number;
  horasSemCusto?: number;
};

export type UnproductiveHoursRankingData = {
  periodo?: Record<string, string | null | undefined>;
  rank_by?: string;
  rankBy?: string;
  metric?: string;
  limit?: number;
  items: UnproductiveHoursRankingItem[];
};

export type UnproductiveHoursFilterFormState = {
  stopReason: string;
  resource: string;
  costCenter: string;
  operatorCode: string;
};

export function createDefaultUnproductiveHoursFilterForm(): UnproductiveHoursFilterFormState {
  return {
    stopReason: "",
    resource: "",
    costCenter: "",
    operatorCode: "",
  };
}

export function resolveSummaryNumber(
  summary: UnproductiveHoursSummaryMetrics | null | undefined,
  enKey: keyof UnproductiveHoursSummaryMetrics,
  ptKey: keyof UnproductiveHoursSummaryMetrics,
): number {
  if (!summary) return 0;
  const en = summary[enKey];
  if (typeof en === "number") return en;
  const pt = summary[ptKey];
  return typeof pt === "number" ? pt : 0;
}

export function resolveItemHours(item: UnproductiveHoursItem): number {
  return item.hours ?? item.tempoHoras ?? 0;
}

export function resolveItemCost(item: UnproductiveHoursItem): number {
  return item.stop_cost ?? item.valorParada ?? 0;
}

export function resolveRankingHours(item: UnproductiveHoursRankingItem): number {
  return item.total_hours ?? item.totalHoras ?? 0;
}

export function resolveItemsPagination(data: UnproductiveHoursItemsData | null): {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
} {
  if (!data) {
    return { page: 1, pageSize: UNPRODUCTIVE_HOURS_PAGE_SIZE, total: 0, totalPages: 1 };
  }
  const page = data.pagination?.page ?? data.page ?? 1;
  const pageSize =
    data.pagination?.page_size ?? data.page_size ?? data.pageSize ?? UNPRODUCTIVE_HOURS_PAGE_SIZE;
  const total = data.pagination?.total ?? data.total ?? 0;
  const totalPages =
    data.pagination?.total_pages ?? data.total_pages ?? data.totalPages ?? Math.max(1, Math.ceil(total / pageSize));
  return { page, pageSize, total, totalPages };
}
